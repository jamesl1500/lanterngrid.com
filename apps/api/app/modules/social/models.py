import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.ids import uuid7


class FriendRequest(Base):
    __tablename__ = "friend_requests"
    __table_args__ = (
        CheckConstraint("sender_id <> recipient_id", name="not_self"),
        # At most one open request between two people, whichever way it goes.
        Index(
            "uq_friend_requests_pending_pair",
            func.least(text("sender_id"), text("recipient_id")),
            func.greatest(text("sender_id"), text("recipient_id")),
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
        Index("ix_friend_requests_recipient_id_status", "recipient_id", "status"),
        Index("ix_friend_requests_sender_id_status", "sender_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    sender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # pending, then accepted, declined or cancelled.
    status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Friendship(Base):
    """One row per pair of friends, stored with the smaller id first."""

    __tablename__ = "friendships"
    __table_args__ = (CheckConstraint("user_a_id < user_b_id", name="ordered_pair"),)

    user_a_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    user_b_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Block(Base):
    __tablename__ = "blocks"
    __table_args__ = (CheckConstraint("blocker_id <> blocked_id", name="not_self"),)

    blocker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    blocked_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
