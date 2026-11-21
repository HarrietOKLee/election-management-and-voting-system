"""Station-scoped live electronic vote totals for the Supervisor workspace."""

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot

from election.desktop.configuration import AuthorizedRequest
from election.desktop.lifecycle import HKT

TEMPORARY_FAILURES = frozenset(
    {"certificate_error", "database_unavailable", "disconnected", "request_failed"}
)


@dataclass(frozen=True)
class ResultScope:
    account_id: int
    election_id: int
    constituency_id: int
    station_id: int


class EpollingResultsController(QObject):
    stateChanged = Signal()

    def __init__(self, request: AuthorizedRequest, parent: QObject) -> None:
        super().__init__(parent)
        self._request = request
        self._generation = 0
        self._state: dict[str, Any] = {}
        self.reset()

    @Property(dict, notify=stateChanged)
    def state(self) -> dict[str, Any]:
        return deepcopy(self._state)

    def _clear_tally(self) -> None:
        self._generation += 1
        self._state = {
            "station_id": self._scope.station_id if self._scope else 0,
            "tally": {},
            "updated_at": "",
            "refreshing": False,
            "error": "",
        }
        self.stateChanged.emit()

    def reset(self) -> None:
        self._viewing = False
        self._scope: ResultScope | None = None
        self._clear_tally()

    def set_context(self, context: dict[str, Any]) -> None:
        account = context.get("account") or {}
        election = context.get("election") or {}
        scope = None
        if account.get("role") == "supervisor" and election.get("voting_method") == "electronic":
            identifiers = (
                account.get("id", 0),
                election.get("id", 0),
                (context.get("constituency") or {}).get("id", 0),
                (context.get("station") or {}).get("id", 0),
            )
            if all(type(value) is int and value > 0 for value in identifiers):
                scope = ResultScope(*identifiers)
        if scope != self._scope:
            self._scope = scope
            self._clear_tally()
            self.refresh()

    @Slot(bool)
    def setViewing(self, viewing: bool) -> None:
        if self._viewing == viewing:
            return
        self._viewing = viewing
        if viewing:
            self.refresh()
        else:
            self._clear_tally()

    @staticmethod
    def _tally(data: dict[str, Any], scope: ResultScope) -> dict[str, Any] | None:
        context = data.get("context")
        if not isinstance(context, dict):
            return None
        labels = {}
        for kind, identifier in (
            ("election", scope.election_id),
            ("constituency", scope.constituency_id),
            ("station", scope.station_id),
        ):
            entry = context.get(kind)
            if (
                not isinstance(entry, dict)
                or entry.get("id") != identifier
                or not isinstance(entry.get("name"), str)
            ):
                return None
            labels[kind] = entry["name"]

        candidates = data.get("candidates")
        total = data.get("total_votes")
        if type(total) is not int or not isinstance(candidates, list):
            return None
        rows = []
        votes = 0
        for candidate in candidates:
            if (
                not isinstance(candidate, dict)
                or type(candidate.get("number")) is not int
                or not isinstance(candidate.get("name"), str)
                or type(candidate.get("votes")) is not int
                or candidate["votes"] < 0
            ):
                return None
            votes += candidate["votes"]
            rows.append(
                {
                    "number": str(candidate["number"]),
                    "name": candidate["name"],
                    "votes": str(candidate["votes"]),
                }
            )
        if total != votes:
            return None
        return {
            "context": labels,
            "candidates": rows,
            "total": str(total),
            "zero_votes": total == 0,
        }

    @Slot()
    def refresh(self) -> None:
        scope = self._scope
        if not self._viewing or scope is None or self._state["refreshing"]:
            return
        generation = self._generation
        self._state["refreshing"] = True
        self.stateChanged.emit()

        def rejected(code: str) -> None:
            if generation != self._generation:
                return
            if code not in TEMPORARY_FAILURES:
                self._state.update(tally={}, updated_at="")
            self._state.update(refreshing=False, error=code)
            self.stateChanged.emit()

        def loaded(data: dict[str, Any]) -> None:
            if generation != self._generation:
                return
            tally = self._tally(data, scope)
            if tally is None:
                rejected("request_failed")
                return
            self._state.update(
                refreshing=False,
                error="",
                tally=tally,
                updated_at=datetime.now(HKT).strftime("%H:%M:%S HKT"),
            )
            self.stateChanged.emit()

        self._request(
            f"/api/workspace/stations/{scope.station_id}/e-polling/results",
            "GET",
            None,
            loaded,
            rejected,
        )
