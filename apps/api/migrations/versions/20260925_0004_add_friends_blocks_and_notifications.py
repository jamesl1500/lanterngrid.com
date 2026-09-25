"""Add friend requests, friendships, blocks and notifications, and index people search.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _created_at() -> sa.Column[sa.DateTime]:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )


def _user_fk(column: str, table: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        [column], ["users.id"], name=op.f(f"fk_{table}_{column}_users"), ondelete="CASCADE"
    )


def upgrade() -> None:
    op.create_table(
        "friend_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("sender_id", sa.Uuid(), nullable=False),
        sa.Column("recipient_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        _created_at(),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("sender_id <> recipient_id", name=op.f("ck_friend_requests_not_self")),
        _user_fk("sender_id", "friend_requests"),
        _user_fk("recipient_id", "friend_requests"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_friend_requests")),
    )
    op.create_index(
        "ix_friend_requests_recipient_id_status", "friend_requests", ["recipient_id", "status"]
    )
    op.create_index(
        "ix_friend_requests_sender_id_status", "friend_requests", ["sender_id", "status"]
    )
    # At most one open request between two people, whichever way it goes.
    op.create_index(
        "uq_friend_requests_pending_pair",
        "friend_requests",
        [
            sa.literal_column("least(sender_id, recipient_id)"),
            sa.literal_column("greatest(sender_id, recipient_id)"),
        ],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )

    op.create_table(
        "friendships",
        sa.Column("user_a_id", sa.Uuid(), nullable=False),
        sa.Column("user_b_id", sa.Uuid(), nullable=False),
        _created_at(),
        sa.CheckConstraint("user_a_id < user_b_id", name=op.f("ck_friendships_ordered_pair")),
        _user_fk("user_a_id", "friendships"),
        _user_fk("user_b_id", "friendships"),
        sa.PrimaryKeyConstraint("user_a_id", "user_b_id", name=op.f("pk_friendships")),
    )
    op.create_index(op.f("ix_friendships_user_b_id"), "friendships", ["user_b_id"])

    op.create_table(
        "blocks",
        sa.Column("blocker_id", sa.Uuid(), nullable=False),
        sa.Column("blocked_id", sa.Uuid(), nullable=False),
        _created_at(),
        sa.CheckConstraint("blocker_id <> blocked_id", name=op.f("ck_blocks_not_self")),
        _user_fk("blocker_id", "blocks"),
        _user_fk("blocked_id", "blocks"),
        sa.PrimaryKeyConstraint("blocker_id", "blocked_id", name=op.f("pk_blocks")),
    )
    op.create_index(op.f("ix_blocks_blocked_id"), "blocks", ["blocked_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=True),
        _created_at(),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        _user_fk("user_id", "notifications"),
        _user_fk("actor_id", "notifications"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notifications")),
    )
    op.create_index("ix_notifications_user_id_id", "notifications", ["user_id", "id"])
    op.create_index(
        "ix_notifications_unread",
        "notifications",
        ["user_id"],
        postgresql_where=sa.text("read_at IS NULL"),
    )

    # People search (pg_trgm is enabled in 0001).
    op.create_index(
        "ix_users_username_trgm",
        "users",
        [sa.text("lower(username::text) gin_trgm_ops")],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_users_display_name_trgm",
        "users",
        [sa.text("lower(display_name) gin_trgm_ops")],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_users_display_name_trgm", table_name="users")
    op.drop_index("ix_users_username_trgm", table_name="users")
    op.drop_table("notifications")
    op.drop_table("blocks")
    op.drop_table("friendships")
    op.drop_table("friend_requests")
