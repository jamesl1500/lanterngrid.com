"""Add profile links, tags and profile stacks, and seed common tags.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.core.ids import uuid7

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (slug, name, kind). Slugs are written out rather than computed so this migration doesn't
# change if slugify() does.
SEED_TAGS = [
    ("python", "Python", "language"),
    ("typescript", "TypeScript", "language"),
    ("javascript", "JavaScript", "language"),
    ("go", "Go", "language"),
    ("rust", "Rust", "language"),
    ("java", "Java", "language"),
    ("kotlin", "Kotlin", "language"),
    ("swift", "Swift", "language"),
    ("c", "C", "language"),
    ("cpp", "C++", "language"),
    ("csharp", "C#", "language"),
    ("ruby", "Ruby", "language"),
    ("php", "PHP", "language"),
    ("elixir", "Elixir", "language"),
    ("scala", "Scala", "language"),
    ("haskell", "Haskell", "language"),
    ("clojure", "Clojure", "language"),
    ("dart", "Dart", "language"),
    ("zig", "Zig", "language"),
    ("lua", "Lua", "language"),
    ("sql", "SQL", "language"),
    ("bash", "Bash", "language"),
    ("r", "R", "language"),
    ("ocaml", "OCaml", "language"),
    ("fsharp", "F#", "language"),
    ("julia", "Julia", "language"),
    ("erlang", "Erlang", "language"),
    ("objective-c", "Objective-C", "language"),
    ("gleam", "Gleam", "language"),
    ("react", "React", "tool"),
    ("next.js", "Next.js", "tool"),
    ("vue", "Vue", "tool"),
    ("svelte", "Svelte", "tool"),
    ("angular", "Angular", "tool"),
    ("node.js", "Node.js", "tool"),
    ("deno", "Deno", "tool"),
    ("bun", "Bun", "tool"),
    ("django", "Django", "tool"),
    ("fastapi", "FastAPI", "tool"),
    ("flask", "Flask", "tool"),
    ("rails", "Rails", "tool"),
    ("laravel", "Laravel", "tool"),
    ("spring", "Spring", "tool"),
    ("dotnet", ".NET", "tool"),
    ("express", "Express", "tool"),
    ("tailwind-css", "Tailwind CSS", "tool"),
    ("postgres", "Postgres", "tool"),
    ("mysql", "MySQL", "tool"),
    ("sqlite", "SQLite", "tool"),
    ("redis", "Redis", "tool"),
    ("mongodb", "MongoDB", "tool"),
    ("kafka", "Kafka", "tool"),
    ("graphql", "GraphQL", "tool"),
    ("docker", "Docker", "tool"),
    ("kubernetes", "Kubernetes", "tool"),
    ("terraform", "Terraform", "tool"),
    ("aws", "AWS", "tool"),
    ("google-cloud", "Google Cloud", "tool"),
    ("azure", "Azure", "tool"),
    ("linux", "Linux", "tool"),
    ("git", "Git", "tool"),
    ("neovim", "Neovim", "tool"),
    ("emacs", "Emacs", "tool"),
    ("vs-code", "VS Code", "tool"),
    ("flutter", "Flutter", "tool"),
    ("react-native", "React Native", "tool"),
    ("unity", "Unity", "tool"),
    ("unreal-engine", "Unreal Engine", "tool"),
    ("pytorch", "PyTorch", "tool"),
    ("tensorflow", "TensorFlow", "tool"),
    ("frontend", "Frontend", "topic"),
    ("backend", "Backend", "topic"),
    ("full-stack", "Full stack", "topic"),
    ("devops", "DevOps", "topic"),
    ("sre", "SRE", "topic"),
    ("security", "Security", "topic"),
    ("machine-learning", "Machine learning", "topic"),
    ("ai", "AI", "topic"),
    ("data-engineering", "Data engineering", "topic"),
    ("mobile", "Mobile", "topic"),
    ("game-dev", "Game dev", "topic"),
    ("embedded", "Embedded", "topic"),
    ("open-source", "Open source", "topic"),
    ("distributed-systems", "Distributed systems", "topic"),
    ("databases", "Databases", "topic"),
    ("compilers", "Compilers", "topic"),
    ("web-performance", "Web performance", "topic"),
    ("accessibility", "Accessibility", "topic"),
    ("design-systems", "Design systems", "topic"),
    ("testing", "Testing", "topic"),
    ("systems-programming", "Systems programming", "topic"),
    ("functional-programming", "Functional programming", "topic"),
    ("developer-tools", "Developer tools", "topic"),
    ("api-design", "API design", "topic"),
]


def upgrade() -> None:
    tags = op.create_table(
        "tags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=32), nullable=False),
        sa.Column("kind", sa.String(length=16), server_default="topic", nullable=False),
        sa.Column("curated", sa.Boolean(), server_default=sa.text("false"), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tags")),
        sa.UniqueConstraint("slug", name=op.f("uq_tags_slug")),
    )
    # Fuzzy matches for tag suggestions (pg_trgm is enabled in 0001).
    op.create_index(
        "ix_tags_slug_trgm",
        "tags",
        ["slug"],
        postgresql_using="gin",
        postgresql_ops={"slug": "gin_trgm_ops"},
    )
    op.create_table(
        "profile_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("url", sa.String(length=300), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_profile_links_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_profile_links")),
    )
    op.create_index("ix_profile_links_user_id_position", "profile_links", ["user_id", "position"])
    op.create_table(
        "user_tags",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tag_id"], ["tags.id"], name=op.f("fk_user_tags_tag_id_tags"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_user_tags_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "tag_id", name=op.f("pk_user_tags")),
    )
    op.create_index(op.f("ix_user_tags_tag_id"), "user_tags", ["tag_id"])

    op.bulk_insert(
        tags,
        [
            {"id": uuid7(), "slug": slug, "name": name, "kind": kind, "curated": True}
            for slug, name, kind in SEED_TAGS
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_tags_tag_id"), table_name="user_tags")
    op.drop_table("user_tags")
    op.drop_index("ix_profile_links_user_id_position", table_name="profile_links")
    op.drop_table("profile_links")
    op.drop_index("ix_tags_slug_trgm", table_name="tags")
    op.drop_table("tags")
