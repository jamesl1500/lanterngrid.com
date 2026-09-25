"""Add GitHub repos, and let posts share one.

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("github_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("homepage", sa.String(length=500), nullable=True),
        sa.Column("language", sa.String(length=64), nullable=True),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("forks", sa.Integer(), nullable=False),
        sa.Column("open_issues", sa.Integer(), nullable=False),
        sa.Column("topics", postgresql.ARRAY(sa.String(length=50)), nullable=False),
        sa.Column("fork", sa.Boolean(), nullable=False),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("pushed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("etag", sa.String(length=200), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("missing_since", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name=op.f("fk_repos_owner_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_repos")),
        sa.UniqueConstraint("owner_id", "github_id", name="uq_repos_owner_id_github_id"),
    )
    # Someone's repos, newest first.
    op.create_index("ix_repos_owner_id_id", "repos", ["owner_id", "id"], unique=False)
    # The worker refreshes the stalest first.
    op.create_index("ix_repos_fetched_at", "repos", ["fetched_at"], unique=False)
    op.add_column("posts", sa.Column("repo_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f("fk_posts_repo_id_repos"), "posts", "repos", ["repo_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_posts_repo_id_repos"), "posts", type_="foreignkey")
    op.drop_column("posts", "repo_id")
    op.drop_table("repos")
