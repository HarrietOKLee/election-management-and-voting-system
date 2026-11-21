"""Single-use voter sessions and aggregate tallies for assigned staff."""

from collections.abc import Callable
from hashlib import sha256
from typing import Annotated, Any, NoReturn
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from election.server.configuration_models import Candidate, Constituency, Election
from election.server.epolling_models import ElectronicVote, ElectronicVotingSession
from election.server.models import Account
from election.server.polling import voting_service
from election.server.station_access import station_scope
from election.server.station_models import PollingStation


class SessionReference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: UUID


class VoteSelection(SessionReference):
    candidate_id: int = Field(strict=True, gt=0, repr=False)


def fail(status_code: int, code: str) -> NoReturn:
    raise HTTPException(status_code, detail={"code": code})


def require_open_service(db: Session, station_id: int) -> None:
    # The caller holds the same station lock as polling approvals and amendments.
    if voting_service(db, station_id, lock=True) not in ("open", "queued"):
        fail(409, "epolling_service_closed")


def require_epolling(election: Election) -> None:
    if election.voting_method != "electronic":
        fail(409, "epolling_not_enabled")


def epolling_context(
    station: PollingStation, constituency: Constituency, election: Election
) -> dict[str, Any]:
    return {
        "election": {
            "id": election.id,
            "name": election.name,
            "status": election.status,
            "voting_method": election.voting_method,
        },
        "constituency": {
            "id": constituency.id,
            "name": constituency.name,
            "code": constituency.code,
        },
        "station": {"id": station.id, "name": station.name, "code": station.code},
    }


def candidate_view(candidate: Candidate) -> dict[str, str | int]:
    return {"id": candidate.id, "number": candidate.ballot_number, "name": candidate.name}


def current_candidates(db: Session, constituency_id: int) -> tuple[list[Candidate], str]:
    # Current reads avoid the older snapshot established during authentication.
    candidates = list(
        db.scalars(
            select(Candidate)
            .where(Candidate.constituency_id == constituency_id)
            .order_by(Candidate.ballot_number, Candidate.id)
            .with_for_update()
        )
    )
    fingerprint = sha256(
        "|".join(f"{row.id}:{row.revision}" for row in candidates).encode()
    ).hexdigest()
    return candidates, fingerprint


def voting_station(
    db: Session, actor: Account, station_id: int, *, write: bool = False
) -> tuple[PollingStation, Constituency, Election]:
    if actor.role != "polling_officer":
        fail(403, "polling_officer_required")
    return station_scope(db, actor, station_id, write=write)


def find_session(
    db: Session, session_id: UUID, station_id: int, *, owner_id: int | None = None
) -> ElectronicVotingSession | None:
    row = db.scalar(
        select(ElectronicVotingSession)
        .where(ElectronicVotingSession.id == str(session_id))
        .with_for_update()
    )
    if row and (
        row.station_id != station_id or (owner_id is not None and row.actor_id != owner_id)
    ):
        fail(404, "epolling_session_not_found")
    return row


def commit_session(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        fail(409, "request_conflict")


def epolling_router(
    database: Callable[..., Any], ready_account: Callable[..., Account]
) -> APIRouter:
    router = APIRouter(prefix="/api/workspace/stations/{station_id}/e-polling", tags=["e-polling"])
    Database = Annotated[Session, Depends(database)]
    Actor = Annotated[Account, Depends(ready_account)]

    @router.get("/results")
    def results(station_id: int, response: Response, db: Database, actor: Actor) -> dict[str, Any]:
        if actor.role != "supervisor":
            fail(403, "supervisor_required")
        station, constituency, election = station_scope(db, actor, station_id)
        require_epolling(election)

        vote_totals = (
            select(ElectronicVote.candidate_id, func.count().label("votes"))
            .where(
                ElectronicVote.election_id == election.id,
                ElectronicVote.constituency_id == constituency.id,
                ElectronicVote.station_id == station.id,
            )
            .group_by(ElectronicVote.candidate_id)
            .subquery()
        )
        rows = db.execute(
            select(Candidate, func.coalesce(vote_totals.c.votes, 0))
            .outerjoin(vote_totals, vote_totals.c.candidate_id == Candidate.id)
            .where(Candidate.constituency_id == constituency.id)
            .order_by(Candidate.ballot_number, Candidate.id)
        ).all()
        response.headers["Cache-Control"] = "no-store"
        return {
            "context": epolling_context(station, constituency, election),
            "candidates": [
                {**candidate_view(candidate), "votes": votes} for candidate, votes in rows
            ],
            "total_votes": sum(votes for _, votes in rows),
        }

    @router.post("/sessions")
    def start(
        station_id: int, data: SessionReference, db: Database, actor: Actor
    ) -> dict[str, Any]:
        station, constituency, election = voting_station(db, actor, station_id, write=True)
        require_epolling(election)
        row = find_session(db, data.session_id, station_id, owner_id=actor.id)
        if row and row.status != "pending":
            return {"status": row.status}
        require_open_service(db, station_id)
        candidates, digest = current_candidates(db, constituency.id)
        if not candidates:
            fail(409, "epolling_no_candidates")
        if row and row.candidate_list_digest != digest:
            fail(409, "epolling_candidates_changed")
        result = {
            "status": "pending",
            "context": epolling_context(station, constituency, election),
            "candidates": [candidate_view(candidate) for candidate in candidates],
        }
        if row is None:
            db.add(
                ElectronicVotingSession(
                    id=str(data.session_id),
                    station_id=station_id,
                    actor_id=actor.id,
                    status="pending",
                    candidate_list_digest=digest,
                )
            )
            commit_session(db)
        return result

    @router.post("/sessions/status")
    def status(
        station_id: int, data: SessionReference, response: Response, db: Database, actor: Actor
    ) -> dict[str, str]:
        voting_station(db, actor, station_id)
        # An assigned replacement officer can recover status using the private reference.
        row = find_session(db, data.session_id, station_id)
        if row is None:
            fail(404, "epolling_session_not_found")
        response.headers["Cache-Control"] = "no-store"
        return {"status": row.status}

    @router.put("/sessions/vote")
    def cast(station_id: int, data: VoteSelection, db: Database, actor: Actor) -> dict[str, str]:
        _, constituency, election = voting_station(db, actor, station_id, write=True)
        require_epolling(election)
        row = find_session(db, data.session_id, station_id, owner_id=actor.id)
        if row is None:
            fail(404, "epolling_session_not_found")
        if row.status == "recorded":
            return {"status": "recorded"}
        if row.status == "cancelled":
            fail(409, "epolling_session_cancelled")
        require_open_service(db, station_id)
        candidates, digest = current_candidates(db, constituency.id)
        if row.candidate_list_digest != digest:
            fail(409, "epolling_candidates_changed")
        if data.candidate_id not in {candidate.id for candidate in candidates}:
            fail(422, "epolling_candidate_unavailable")
        db.add(
            ElectronicVote(
                id=str(uuid4()),
                election_id=election.id,
                constituency_id=constituency.id,
                station_id=station_id,
                candidate_id=data.candidate_id,
            )
        )
        row.status, row.candidate_list_digest = "recorded", None
        commit_session(db)
        return {"status": "recorded"}

    @router.post("/sessions/cancel")
    def cancel(
        station_id: int, data: SessionReference, db: Database, actor: Actor
    ) -> dict[str, str]:
        _, _, election = voting_station(db, actor, station_id)
        require_epolling(election)
        # Match the lock order of start and cast, even if polling is now closed.
        db.scalar(select(PollingStation).where(PollingStation.id == station_id).with_for_update())
        row = find_session(db, data.session_id, station_id)
        if row is None:
            # Fence a start that timed out and could still arrive at the server.
            db.add(
                ElectronicVotingSession(
                    id=str(data.session_id),
                    station_id=station_id,
                    actor_id=actor.id,
                    status="cancelled",
                )
            )
        elif row.status != "pending":
            return {"status": row.status}
        else:
            row.status, row.candidate_list_digest = "cancelled", None
        commit_session(db)
        return {"status": "cancelled"}

    return router
