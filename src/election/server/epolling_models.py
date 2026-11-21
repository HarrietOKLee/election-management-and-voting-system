"""Paperless voting sessions and unlinked electronic vote records."""

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from election.server.db import Base


class ElectronicVotingSession(Base):
    __tablename__ = "electronic_voting_sessions"
    __table_args__ = (
        CheckConstraint(
            "(status = 'pending' AND candidate_list_digest IS NOT NULL) OR "
            "(status IN ('recorded', 'cancelled') AND candidate_list_digest IS NULL)",
            name="ck_electronic_voting_session_status",
        ),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("polling_stations.id"))
    actor_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    status: Mapped[str] = mapped_column(String(16))
    candidate_list_digest: Mapped[str | None] = mapped_column(String(64))


class ElectronicVote(Base):
    __tablename__ = "electronic_votes"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    # A separate random identifier avoids a direct link to the session or its staff owner.
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    election_id: Mapped[int] = mapped_column(ForeignKey("elections.id"))
    constituency_id: Mapped[int] = mapped_column(ForeignKey("constituencies.id"))
    station_id: Mapped[int] = mapped_column(ForeignKey("polling_stations.id"))
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
