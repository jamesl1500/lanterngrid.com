import uuid
from datetime import datetime

from sqlalchemy import (
    ColumnElement,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    func,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, CITEXT
from sqlalchemy.orm import InstrumentedAttribute, Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.ids import uuid7
from app.core.models import TimestampMixin
from app.modules.users.schemas import PROFILE_SECTIONS


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        # People search: username prefixes and loose name matches (pg_trgm).
        Index(
            "ix_users_username_trgm",
            text("lower(username::text) gin_trgm_ops"),
            postgresql_using="gin",
        ),
        Index(
            "ix_users_display_name_trgm",
            text("lower(display_name) gin_trgm_ops"),
            postgresql_using="gin",
        ),
        # Keeps "not suspended" checks cheap: few accounts are ever suspended.
        Index("ix_users_suspended", "id", postgresql_where=text("suspended_at IS NOT NULL")),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    email: Mapped[str] = mapped_column(CITEXT, unique=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Null until the person finishes onboarding.
    username: Mapped[str | None] = mapped_column(CITEXT, unique=True)
    display_name: Mapped[str] = mapped_column(String(50))
    # Null for accounts that only sign in with GitHub.
    password_hash: Mapped[str | None] = mapped_column(Text)
    # Moderators work the report queue. Granted with `python -m scripts.moderators`.
    is_moderator: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    # Set by a moderator. Suspended accounts can't sign in, and what they wrote is hidden.
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped["Profile"] = relationship(
        back_populates="user", lazy="joined", cascade="all, delete-orphan"
    )


def not_suspended(user_id: InstrumentedAttribute[uuid.UUID]) -> ColumnElement[bool]:
    """True where the account in this column isn't suspended, for hiding what they wrote."""
    return user_id.not_in(select(User.id).where(User.suspended_at.is_not(None)))


class Profile(Base):
    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    headline: Mapped[str | None] = mapped_column(String(120))
    bio: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(80))
    website: Mapped[str | None] = mapped_column(String(200))
    accent_color: Mapped[str] = mapped_column(String(16), default="violet", server_default="violet")
    avatar_key: Mapped[str | None] = mapped_column(String(300))
    banner_key: Mapped[str | None] = mapped_column(String(300))
    # Markdown shown at the top of the profile page, like a GitHub profile README.
    readme_md: Mapped[str | None] = mapped_column(Text)
    # The profile page's sections in order; ones left out are hidden. See PROFILE_SECTIONS.
    sections: Mapped[list[str]] = mapped_column(
        ARRAY(String(16)),
        default=lambda: list(PROFILE_SECTIONS),
        server_default="{readme,pinned,friends,posts}",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="profile")


class ProfileLink(Base):
    """A link shown on someone's profile: GitHub, a blog, a Mastodon account..."""

    __tablename__ = "profile_links"
    __table_args__ = (Index("ix_profile_links_user_id_position", "user_id", "position"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16))
    url: Mapped[str] = mapped_column(String(300))
    position: Mapped[int] = mapped_column(SmallInteger)
