"""Add profile READMEs and section order, and full-text search over posts.

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("readme_md", sa.Text(), nullable=True))
    op.add_column(
        "profiles",
        sa.Column(
            "sections",
            postgresql.ARRAY(sa.String(length=16)),
            server_default="{readme,pinned,friends,posts}",
            nullable=False,
        ),
    )
    # Postgres fills this for existing posts too, so search works on old posts right away.
    op.add_column(
        "posts",
        sa.Column(
            "search",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english', body_md)", persisted=True),
            nullable=False,
        ),
    )
    op.create_index("ix_posts_search", "posts", ["search"], unique=False, postgresql_using="gin")


def downgrade() -> None:
    op.drop_index("ix_posts_search", table_name="posts", postgresql_using="gin")
    op.drop_column("posts", "search")
    op.drop_column("profiles", "sections")
    op.drop_column("profiles", "readme_md")
