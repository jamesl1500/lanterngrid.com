"""Let a message share a snippet.

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("snippet_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f("fk_messages_snippet_id_snippets"),
        "messages",
        "snippets",
        ["snippet_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # Clearing shared snippets when their owner's account goes.
    op.create_index(
        "ix_messages_snippet_id",
        "messages",
        ["snippet_id"],
        unique=False,
        postgresql_where=sa.text("snippet_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_messages_snippet_id",
        table_name="messages",
        postgresql_where=sa.text("snippet_id IS NOT NULL"),
    )
    op.drop_constraint(op.f("fk_messages_snippet_id_snippets"), "messages", type_="foreignkey")
    op.drop_column("messages", "snippet_id")
