"""Add snippets, profile pins and achievement posts.

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pins",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("item_type", sa.String(length=16), nullable=False),
        sa.Column("item_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_pins_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "item_type", "item_id", name=op.f("pk_pins")),
    )
    op.create_table(
        "snippets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("filename", sa.String(length=100), nullable=True),
        sa.Column("language", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("description", sa.String(length=500), server_default="", nullable=False),
        sa.Column("visibility", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name=op.f("fk_snippets_owner_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_snippets")),
    )
    op.create_index(
        "ix_snippets_owner_id_id",
        "snippets",
        ["owner_id", "id"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_table(
        "achievements",
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=24), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(
            ["post_id"],
            ["posts.id"],
            name=op.f("fk_achievements_post_id_posts"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("post_id", name=op.f("pk_achievements")),
    )
    # Snippet posts point at the snippet they share.
    op.add_column("posts", sa.Column("snippet_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f("fk_posts_snippet_id_snippets"),
        "posts",
        "snippets",
        ["snippet_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_posts_snippet_id_snippets"), "posts", type_="foreignkey")
    op.drop_column("posts", "snippet_id")
    op.drop_table("achievements")
    op.drop_index(
        "ix_snippets_owner_id_id",
        table_name="snippets",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_table("snippets")
    op.drop_table("pins")
