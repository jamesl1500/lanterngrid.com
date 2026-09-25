import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.ids import uuid7
from app.modules.users.models import User


class Snippet(Base):
    __tablename__ = "snippets"
    __table_args__ = (
        # Someone's snippets, newest first.
        Index(
            "ix_snippets_owner_id_id",
            "owner_id",
            "id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(100))
    filename: Mapped[str | None] = mapped_column(String(100))
    # A Shiki language id; see LANGUAGES.
    language: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(String(500), default="", server_default="")
    # public or friends.
    visibility: Mapped[str] = mapped_column(String(16), default="public")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    owner: Mapped[User] = relationship(lazy="joined")


class Pin(Base):
    """Something someone pinned to their profile."""

    __tablename__ = "pins"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    # snippet now; repo arrives with repo sharing.
    item_type: Mapped[str] = mapped_column(String(16), primary_key=True)
    item_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    position: Mapped[int] = mapped_column()
