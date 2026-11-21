"""Voter interaction and privacy-preserving recovery for a single desktop screen."""

from collections.abc import Callable
from copy import deepcopy
from typing import Any
from uuid import uuid4

from PySide6.QtCore import Property, QObject, Signal, Slot

from election.desktop.configuration import AuthorizedRequest, ResultHandler
from election.desktop.epolling_recovery import VotingSession, VotingSessionJournal

START_REJECTIONS = {
    "active_election_required",
    "epolling_no_candidates",
    "epolling_not_enabled",
    "epolling_service_closed",
    "polling_officer_required",
    "station_access_denied",
    "validation_error",
}
SESSION_ENDED = {
    "epolling_candidates_changed",
    "epolling_service_closed",
    "epolling_session_cancelled",
    "epolling_session_not_found",
}
SELECTION_REJECTIONS = {"epolling_candidate_unavailable", "validation_error"}


class EpollingController(QObject):
    stateChanged = Signal()

    def __init__(
        self,
        request: AuthorizedRequest,
        journal: VotingSessionJournal,
        sign_out: Callable[[], None],
        parent: QObject,
    ) -> None:
        super().__init__(parent)
        self._request = request
        self._journal = journal
        self._journal_locked = False
        self._sign_out = sign_out
        self._generation = 0
        self._state: dict[str, Any] = {}
        self.reset()

    @Property(dict, notify=stateChanged)
    def state(self) -> dict[str, Any]:
        return deepcopy(self._state)

    @property
    def active(self) -> bool:
        return bool(self._state["stage"] != "inactive")

    def _update(self, **changes: Any) -> None:
        self._state.update(changes)
        self.stateChanged.emit()

    def reset(self) -> None:
        self._generation += 1
        self._release_journal()
        self._server_url = ""
        self._account_id = 0
        self._station_id = 0
        self._session: VotingSession | None = None
        # The confirmed candidate exists only in memory while a submission is unresolved.
        self._candidate: int | None = None
        self._cancellation_error = ""
        self._update(
            stage="inactive",
            context={},
            candidates=[],
            busy=False,
            retry=False,
            error="",
        )

    def set_account(self, server_url: str, account: dict[str, Any]) -> None:
        account_id = account.get("id", 0)
        if (
            account.get("role") != "polling_officer"
            or account.get("must_change_password", True)
            or type(account_id) is not int
            or account_id <= 0
        ):
            account_id = 0
        if (server_url, account_id) == (self._server_url, self._account_id):
            return
        self.reset()
        self._server_url, self._account_id = server_url, account_id
        if not account_id:
            return
        try:
            if self._journal.exists():
                self._prepare_session(0)
        except OSError:
            self._update(error="epolling_journal_unavailable")

    def _release_journal(self) -> None:
        self._journal.release()
        self._journal_locked = False

    def _prepare_session(self, station_id: int) -> None:
        try:
            if not self._journal_locked:
                if not self._journal.acquire():
                    self._update(error="epolling_screen_busy")
                    return
                self._journal_locked = True
            session = self._journal.read()
            if session and session.server_url != self._server_url:
                self._release_journal()
                self._update(error="epolling_recovery_server")
                return
            if session is None:
                if not station_id:
                    self._release_journal()
                    return
                session = VotingSession(self._server_url, station_id, str(uuid4()))
                self._journal.write(session)
                self._station_id = station_id
                self._session = session
                self._start_session(keep_private=self.active)
            else:
                self._station_id = session.station_id
                self._session = session
                self._update(stage="checking", context={}, error="", retry=False)
                self.checkStatus()
        except OSError:
            self._release_journal()
            self._update(error="epolling_journal_unavailable")

    def _sessions_path(self, session: VotingSession) -> str:
        return f"/api/workspace/stations/{session.station_id}/e-polling/sessions"

    def _send(
        self,
        path: str,
        method: str,
        payload: dict[str, Any] | None,
        loaded: ResultHandler,
        rejected: Callable[[str], None],
    ) -> None:
        generation = self._generation
        self._update(busy=True, error="", retry=False)

        def done(data: dict[str, Any]) -> None:
            if generation == self._generation:
                loaded(data)

        def failed(code: str) -> None:
            if generation == self._generation:
                rejected(code)

        self._request(path, method, payload, done, failed)

    @Slot(int)
    def start(self, station_id: int) -> None:
        if not self.active and self._account_id and station_id > 0:
            self._prepare_session(station_id)

    @Slot()
    def startNext(self) -> None:
        if (
            self._state["stage"] in {"waiting", "unavailable"}
            and not self._state["busy"]
            and self._session is None
            and self._account_id
            and self._station_id
        ):
            self._prepare_session(self._station_id)

    def _start_session(self, *, keep_private: bool) -> None:
        session = self._session
        if session is None:
            return
        self._update(stage="starting", candidates=[])

        def loaded(data: dict[str, Any]) -> None:
            if data == {"status": "recorded"}:
                self._finish("recorded")
                return
            if data == {"status": "cancelled"}:
                self._finish("unavailable", "epolling_session_cancelled")
                return
            context, candidates = data.get("context"), data.get("candidates")
            if (
                data.get("status") == "pending"
                and isinstance(context, dict)
                and all(
                    isinstance(context.get(kind), dict)
                    and isinstance(context[kind].get("name"), str)
                    for kind in ("station", "election", "constituency")
                )
                and context["station"].get("id") == session.station_id
                and isinstance(candidates, list)
                and bool(candidates)
                and all(
                    isinstance(row, dict)
                    and type(row.get("id")) is int
                    and type(row.get("number")) is int
                    and isinstance(row.get("name"), str)
                    for row in candidates
                )
            ):
                self._update(stage="select", context=context, candidates=candidates, busy=False)
            else:
                self._check_after_failure()

        def rejected(code: str) -> None:
            if code in START_REJECTIONS:
                self._finish("unavailable" if keep_private else "inactive", code)
            else:
                self._check_after_failure()

        self._send(
            self._sessions_path(session),
            "POST",
            {"session_id": session.session_id},
            loaded,
            rejected,
        )

    @Slot(int)
    def cast(self, candidate_id: int) -> None:
        if (
            self._state["stage"] == "select"
            and not self._state["busy"]
            and any(row["id"] == candidate_id for row in self._state["candidates"])
        ):
            self._candidate = candidate_id
            self._cast_vote(retry=False)

    @Slot()
    def retryCast(self) -> None:
        if self._state["stage"] == "checking" and self._state["retry"] and not self._state["busy"]:
            self._cast_vote(retry=True)

    def _cast_vote(self, *, retry: bool) -> None:
        session, candidate_id = self._session, self._candidate
        if session is None or candidate_id is None:
            return
        self._update(stage="casting")

        def loaded(data: dict[str, Any]) -> None:
            if data == {"status": "recorded"}:
                self._finish("recorded")
            else:
                self._check_after_failure()

        def rejected(code: str) -> None:
            if not retry and code in SELECTION_REJECTIONS:
                self._candidate = None
                self._update(stage="select", busy=False, error=code)
            elif code in SESSION_ENDED | SELECTION_REJECTIONS:
                self._cancel_session(code)
            else:
                self._check_after_failure()

        self._send(
            f"{self._sessions_path(session)}/vote",
            "PUT",
            {"session_id": session.session_id, "candidate_id": candidate_id},
            loaded,
            rejected,
        )

    def _check_after_failure(self) -> None:
        self._update(stage="checking", busy=False)
        self.checkStatus()

    @Slot()
    def checkStatus(self) -> None:
        session = self._session
        if session is None or self._state["stage"] != "checking" or self._state["busy"]:
            return

        def loaded(data: dict[str, Any]) -> None:
            if data == {"status": "recorded"}:
                self._finish("recorded")
            elif data == {"status": "cancelled"}:
                self._finish_cancelled()
            elif data == {"status": "pending"}:
                if self._candidate is None:
                    self._cancel_session(self._cancellation_error)
                else:
                    self._update(busy=False, retry=True)
            else:
                self._update(busy=False, error="request_failed")

        def rejected(code: str) -> None:
            if code == "epolling_session_not_found":
                self._cancel_session(self._cancellation_error or code)
            else:
                self._update(busy=False, error=code)

        self._send(
            f"{self._sessions_path(session)}/status",
            "POST",
            {"session_id": session.session_id},
            loaded,
            rejected,
        )

    @Slot()
    def abandon(self) -> None:
        stage = self._state["stage"]
        can_abandon = stage == "select" or (stage == "checking" and self._state["retry"])
        if can_abandon and not self._state["busy"]:
            self._cancel_session("")

    def _cancel_session(self, error: str) -> None:
        session = self._session
        if session is None:
            return
        self._candidate = None
        self._cancellation_error = error
        self._update(stage="checking", candidates=[])

        def loaded(data: dict[str, Any]) -> None:
            if data == {"status": "recorded"}:
                self._finish("recorded")
            elif data == {"status": "cancelled"}:
                self._finish_cancelled()
            else:
                self._update(busy=False, error="request_failed")

        self._send(
            f"{self._sessions_path(session)}/cancel",
            "POST",
            {"session_id": session.session_id},
            loaded,
            lambda code: self._update(busy=False, error=code),
        )

    def _finish_cancelled(self) -> None:
        error = self._cancellation_error
        self._finish("unavailable" if error else "waiting", error)

    def _finish(self, stage: str, error: str = "") -> None:
        self._candidate = None
        try:
            self._journal.clear()
        except OSError:
            self._update(
                stage="checking",
                candidates=[],
                busy=False,
                retry=False,
                error="epolling_journal_unavailable",
            )
            return
        # The same window owns the voting screen between voters until staff signs out.
        if stage == "inactive":
            self._release_journal()
            self._station_id = 0
        self._session = None
        self._cancellation_error = ""
        self._update(stage=stage, candidates=[], busy=False, retry=False, error=error)

    @Slot()
    def done(self) -> None:
        if self._state["stage"] == "recorded":
            self._update(stage="waiting")

    @Slot()
    def exit(self) -> None:
        if (
            self._state["stage"] in {"waiting", "unavailable", "checking"}
            and not self._state["busy"]
        ):
            self._sign_out()
