"""Add reports, the moderation queue, moderators, suspensions and removed messages.

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_moderator", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column("users", sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True))
    # Few accounts are ever suspended, so "not suspended" checks read a tiny index.
    op.create_index(
        "ix_users_suspended",
        "users",
        ["id"],
        unique=False,
        postgresql_where=sa.text("suspended_at IS NOT NULL"),
    )
    op.add_column("messages", sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "moderation_cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("subject_kind", sa.String(length=16), nullable=False),
        # Not a foreign key: it points at a different table for each kind.
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("subject_author_id", sa.Uuid(), nullable=True),
        sa.Column("post_id", sa.Uuid(), nullable=True),
        sa.Column("snapshot", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="open", nullable=False),
        sa.Column("report_count", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by_id", sa.Uuid(), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(
            ["subject_author_id"],
            ["users.id"],
            name=op.f("fk_moderation_cases_subject_author_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by_id"],
            ["users.id"],
            name=op.f("fk_moderation_cases_resolved_by_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_moderation_cases")),
    )
    # One open case per reported thing; later reports join it.
    op.create_index(
        "uq_moderation_cases_open_subject",
        "moderation_cases",
        ["subject_kind", "subject_id"],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
    )
    op.create_index(
        "ix_moderation_cases_status_id", "moderation_cases", ["status", "id"], unique=False
    )
    op.create_index(
        "ix_moderation_cases_open_author",
        "moderation_cases",
        ["subject_author_id"],
        unique=False,
        postgresql_where=sa.text("status = 'open'"),
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("reporter_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.String(length=16), nullable=False),
        sa.Column("details", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["moderation_cases.id"],
            name=op.f("fk_reports_case_id_moderation_cases"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reporter_id"],
            ["users.id"],
            name=op.f("fk_reports_reporter_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reports")),
        sa.UniqueConstraint("case_id", "reporter_id", name="uq_reports_case_id_reporter_id"),
    )
    op.create_index("ix_reports_reporter_id", "reports", ["reporter_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_reports_reporter_id", table_name="reports")
    op.drop_table("reports")
    op.drop_index(
        "ix_moderation_cases_open_author",
        table_name="moderation_cases",
        postgresql_where=sa.text("status = 'open'"),
    )
    op.drop_index("ix_moderation_cases_status_id", table_name="moderation_cases")
    op.drop_index(
        "uq_moderation_cases_open_subject",
        table_name="moderation_cases",
        postgresql_where=sa.text("status = 'open'"),
    )
    op.drop_table("moderation_cases")
    op.drop_column("messages", "removed_at")
    op.drop_index(
        "ix_users_suspended",
        table_name="users",
        postgresql_where=sa.text("suspended_at IS NOT NULL"),
    )
    op.drop_column("users", "suspended_at")
    op.drop_column("users", "is_moderator")
