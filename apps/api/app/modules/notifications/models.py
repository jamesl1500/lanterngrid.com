import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.ids import uuid7
from app.modules.users.models import User


class Notification(Base):
    """Something that happened to someone: a friend request, an accepted request..."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id_id", "user_id", "id"),
        # Keeps the unread badge cheap however long the history gets.
        Index(
            "ix_notifications_unread",
            "user_id",
            postgresql_where=text("read_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(32))
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # What it is about, e.g. the friend request's id. Not a foreign key: it points at
    # different tables depending on kind.
    subject_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    actor: Mapped[User] = relationship(foreign_keys=[actor_id], lazy="joined")
