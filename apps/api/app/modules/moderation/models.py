import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.ids import uuid7
from app.modules.users.models import User


class ModerationCase(Base):
    """One reported thing waiting for (or past) a moderator's decision. Reports about the same
    thing pile onto its open case, so the queue shows each thing once."""

    __tablename__ = "moderation_cases"
    __table_args__ = (
        # At most one open case per reported thing.
        Index(
            "uq_moderation_cases_open_subject",
            "subject_kind",
            "subject_id",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
        # The queue: open or closed cases, newest first.
        Index("ix_moderation_cases_status_id", "status", "id"),
        # Closing someone's other cases when they're suspended.
        Index(
            "ix_moderation_cases_open_author",
            "subject_author_id",
            postgresql_where=text("status = 'open'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    # post, comment, snippet, message or user.
    subject_kind: Mapped[str] = mapped_column(String(16))
    # Not a foreign key: it points at a different table for each kind, and the case should
    # outlive the thing if its author deletes it.
    subject_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    # Who wrote it (for a user report, the person themselves).
    subject_author_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    # The post a reported comment is on, to link to it.
    post_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    # The reported text as it was at the first report, so edits can't hide it.
    snapshot: Mapped[str] = mapped_column(Text)
    # open, dismissed, removed or suspended.
    status: Mapped[str] = mapped_column(String(16), default="open", server_default="open")
    report_count: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    # The moderator's note to other moderators.
    note: Mapped[str | None] = mapped_column(String(500))

    subject_author: Mapped[User | None] = relationship(
        foreign_keys=[subject_author_id], lazy="joined"
    )
    resolved_by: Mapped[User | None] = relationship(foreign_keys=[resolved_by_id], lazy="joined")


class Report(Base):
    """Someone flagging a post, comment, snippet, message or person for moderators."""

    __tablename__ = "reports"
    __table_args__ = (
        # Reporting the same thing twice doesn't count twice.
        UniqueConstraint("case_id", "reporter_id", name="uq_reports_case_id_reporter_id"),
        # Removing someone's reports when their account goes.
        Index("ix_reports_reporter_id", "reporter_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("moderation_cases.id", ondelete="CASCADE")
    )
    reporter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # See ReportReason.
    reason: Mapped[str] = mapped_column(String(16))
    details: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    reporter: Mapped[User] = relationship(lazy="joined")
