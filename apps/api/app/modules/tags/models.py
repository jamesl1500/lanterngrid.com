import uuid

from sqlalchemy import Boolean, ForeignKey, Index, SmallInteger, String, false
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.ids import uuid7
from app.core.models import TimestampMixin


class Tag(TimestampMixin, Base):
    """A topic, language or tool. Shared by profiles now and by posts later."""

    __tablename__ = "tags"
    __table_args__ = (
        Index(
            "ix_tags_slug_trgm",
            "slug",
            postgresql_using="gin",
            postgresql_ops={"slug": "gin_trgm_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    # Lowercase, from slugify(); what URLs and lookups use.
    slug: Mapped[str] = mapped_column(String(32), unique=True)
    # How the tag is written, e.g. "TypeScript" for slug "typescript".
    name: Mapped[str] = mapped_column(String(32))
    kind: Mapped[str] = mapped_column(String(16), default="topic", server_default="topic")
    # Seeded by us rather than typed in by someone; ranked first in suggestions.
    curated: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())


class UserTag(Base):
    """The stack someone lists on their profile, in the order they chose."""

    __tablename__ = "user_tags"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    position: Mapped[int] = mapped_column(SmallInteger)
