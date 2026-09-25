"""Add conversations, their members and messages.

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=8), nullable=False),
        sa.Column("title", sa.String(length=80), nullable=True),
        sa.Column("dm_key", sa.String(length=80), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_message_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_conversations_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversations")),
        sa.UniqueConstraint("dm_key", name=op.f("uq_conversations_dm_key")),
    )
    op.create_table(
        "conversation_members",
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=8), nullable=False),
        sa.Column("last_read_message_id", sa.Uuid(), nullable=True),
        sa.Column(
            "joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f("fk_conversation_members_conversation_id_conversations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_conversation_members_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("conversation_id", "user_id", name=op.f("pk_conversation_members")),
    )
    # Someone's inbox.
    op.create_index(
        "ix_conversation_members_user_id", "conversation_members", ["user_id"], unique=False
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("sender_id", sa.Uuid(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("client_id", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f("fk_messages_conversation_id_conversations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"],
            ["users.id"],
            name=op.f("fk_messages_sender_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
        # A retried send finds the first message instead of posting twice.
        sa.UniqueConstraint(
            "conversation_id", "sender_id", "client_id", name="uq_messages_client_id"
        ),
    )
    # A conversation's messages in order.
    op.create_index(
        "ix_messages_conversation_id_id", "messages", ["conversation_id", "id"], unique=False
    )


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("conversation_members")
    op.drop_table("conversations")
