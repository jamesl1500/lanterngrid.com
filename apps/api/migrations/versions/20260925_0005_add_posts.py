"""Add posts, with the tags and people they mention.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "posts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=16), server_default="update", nullable=False),
        sa.Column("body_md", sa.Text(), nullable=False),
        sa.Column("visibility", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["author_id"], ["users.id"], name=op.f("fk_posts_author_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_posts")),
    )
    # Profile timelines, and explore's public posts, newest first.
    op.create_index(
        "ix_posts_author_id_id",
        "posts",
        ["author_id", "id"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_posts_public_id",
        "posts",
        ["id"],
        unique=False,
        postgresql_where=sa.text("visibility = 'public' AND deleted_at IS NULL"),
    )
    op.create_table(
        "mentions",
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["post_id"], ["posts.id"], name=op.f("fk_mentions_post_id_posts"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_mentions_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("post_id", "user_id", name=op.f("pk_mentions")),
    )
    op.create_index(op.f("ix_mentions_user_id"), "mentions", ["user_id"], unique=False)
    op.create_table(
        "post_tags",
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["post_id"], ["posts.id"], name=op.f("fk_post_tags_post_id_posts"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"], ["tags.id"], name=op.f("fk_post_tags_tag_id_tags"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("post_id", "tag_id", name=op.f("pk_post_tags")),
    )
    # Tag pages, newest first.
    op.create_index("ix_post_tags_tag_id_post_id", "post_tags", ["tag_id", "post_id"], unique=False)


def downgrade() -> None:
    op.drop_table("post_tags")
    op.drop_table("mentions")
    op.drop_table("posts")
