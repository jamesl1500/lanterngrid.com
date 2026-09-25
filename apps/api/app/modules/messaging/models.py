import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.ids import uuid7
from app.modules.users.models import User


class Conversation(Base):
    """A DM between two friends, or a small group chat."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    # dm or group.
    kind: Mapped[str] = mapped_column(String(8))
    # Groups only; a DM is named after the other person.
    title: Mapped[str | None] = mapped_column(String(80))
    # "<smaller id>:<larger id>" for DMs, so two people share exactly one.
    dm_key: Mapped[str | None] = mapped_column(String(80), unique=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Orders the inbox; the creation time until someone writes.
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ConversationMember(Base):
    __tablename__ = "conversation_members"
    # Someone's inbox, most recent first.
    __table_args__ = (Index("ix_conversation_members_user_id", "user_id"),)

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    # owner or member. The owner of a group can add people.
    role: Mapped[str] = mapped_column(String(8), default="member")
    # Everything up to and including this message has been read.
    last_read_message_id: Mapped[uuid.UUID | None] = mapped_column()
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(lazy="joined")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        # A retried send with the same client_id finds the first one instead of posting twice.
        UniqueConstraint("conversation_id", "sender_id", "client_id", name="uq_messages_client_id"),
        # A conversation's messages in order.
        Index("ix_messages_conversation_id_id", "conversation_id", "id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE")
    )
    sender_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    body: Mapped[str] = mapped_column(Text)
    client_id: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sender: Mapped[User | None] = relationship(lazy="joined")
