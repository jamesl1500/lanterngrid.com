import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, SmallInteger, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.ids import uuid7
from app.modules.users.models import User


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (
        # Profile timelines: someone's posts, newest first.
        Index(
            "ix_posts_author_id_id", "author_id", "id", postgresql_where=text("deleted_at IS NULL")
        ),
        # Explore: public posts, newest first.
        Index(
            "ix_posts_public_id",
            "id",
            postgresql_where=text("visibility = 'public' AND deleted_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # update, snippet, repo or achievement.
    kind: Mapped[str] = mapped_column(String(16), default="update", server_default="update")
    # The snippet a snippet post shares.
    snippet_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("snippets.id", ondelete="SET NULL")
    )
    # The repo a repo post shares.
    repo_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("repos.id", ondelete="SET NULL"))
    body_md: Mapped[str] = mapped_column(Text)
    # public or friends.
    visibility: Mapped[str] = mapped_column(String(16), default="public")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    author: Mapped[User] = relationship(lazy="joined")


class PostTag(Base):
    __tablename__ = "post_tags"
    # Tag pages list a tag's posts newest first.
    __table_args__ = (Index("ix_post_tags_tag_id_post_id", "tag_id", "post_id"),)

    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )


class Mention(Base):
    __tablename__ = "mentions"

    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )


class PostImage(Base):
    __tablename__ = "post_images"

    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    position: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    # Object key in the bucket; build URLs with public_url().
    key: Mapped[str] = mapped_column(String(300))
    alt: Mapped[str] = mapped_column(String(300), default="", server_default="")


class Reaction(Base):
    __tablename__ = "reactions"

    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    kind: Mapped[str] = mapped_column(String(16), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Comment(Base):
    __tablename__ = "comments"
    # A post's comments, oldest first.
    __table_args__ = (Index("ix_comments_post_id_id", "post_id", "id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    body_md: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    author: Mapped[User] = relationship(lazy="joined")


class Achievement(Base):
    """What an achievement post celebrates."""

    __tablename__ = "achievements"

    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    type: Mapped[str] = mapped_column(String(24))
    title: Mapped[str] = mapped_column(String(100))
