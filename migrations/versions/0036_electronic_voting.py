"""Add the election voting method and independent session and vote records."""

import sqlalchemy as sa
from alembic import op

revision = "0036_electronic_voting"
down_revision = "0035_election_completion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "elections",
        sa.Column("voting_method", sa.String(16), nullable=False, server_default="paper"),
    )
    op.create_check_constraint(
        "ck_elections_voting_method",
        "elections",
        "voting_method IN ('paper', 'electronic')",
    )
    op.create_table(
        "electronic_voting_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("station_id", sa.Integer(), sa.ForeignKey("polling_stations.id"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("candidate_list_digest", sa.String(64), nullable=True),
        sa.CheckConstraint(
            "(status = 'pending' AND candidate_list_digest IS NOT NULL) OR "
            "(status IN ('recorded', 'cancelled') AND candidate_list_digest IS NULL)",
            name="ck_electronic_voting_session_status",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_table(
        "electronic_votes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("election_id", sa.Integer(), sa.ForeignKey("elections.id"), nullable=False),
        sa.Column(
            "constituency_id", sa.Integer(), sa.ForeignKey("constituencies.id"), nullable=False
        ),
        sa.Column("station_id", sa.Integer(), sa.ForeignKey("polling_stations.id"), nullable=False),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("candidates.id"), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )


def downgrade() -> None:
    op.drop_table("electronic_votes")
    op.drop_table("electronic_voting_sessions")
    op.drop_constraint("ck_elections_voting_method", "elections", type_="check")
    op.drop_column("elections", "voting_method")
