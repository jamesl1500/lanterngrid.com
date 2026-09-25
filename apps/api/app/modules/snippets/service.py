import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import ColumnElement, Select, and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pins.models import Pin
from app.modules.snippets.models import Snippet
from app.modules.snippets.schemas import (
    SnippetCreate,
    SnippetOut,
    SnippetPage,
    SnippetUpdate,
)
from app.modules.social import service as social
from app.modules.users.models import User
from app.modules.users.summary import summarize


class SnippetNotFoundError(Exception):
    pass


def visible_to(viewer_id: uuid.UUID | None) -> ColumnElement[bool]:
    """Live snippets this person may see (see social.can_see)."""
    return and_(
        Snippet.deleted_at.is_(None),
        social.can_see(viewer_id, Snippet.owner_id, Snippet.visibility),
    )


def to_out(snippet: Snippet) -> SnippetOut:
    return SnippetOut(
        id=snippet.id,
        owner=summarize(snippet.owner),
        title=snippet.title,
        filename=snippet.filename,
        language=snippet.language,
        content=snippet.content,
        description=snippet.description,
        visibility=snippet.visibility,
        line_count=snippet.content.count("\n") + 1,
        created_at=snippet.created_at,
        updated_at=snippet.updated_at,
    )


async def create(db: AsyncSession, owner: User, data: SnippetCreate) -> SnippetOut:
    snippet = Snippet(owner_id=owner.id, **data.model_dump())
    db.add(snippet)
    await db.commit()
    await db.refresh(snippet)
    return to_out(snippet)


async def visible(db: AsyncSession, viewer_id: uuid.UUID | None, snippet_id: uuid.UUID) -> Snippet:
    snippet = await db.scalar(
        select(Snippet).where(Snippet.id == snippet_id, visible_to(viewer_id))
    )
    if snippet is None:
        raise SnippetNotFoundError
    return snippet


async def own(db: AsyncSession, owner: User, snippet_id: uuid.UUID) -> Snippet:
    snippet = await db.get(Snippet, snippet_id)
    if snippet is None or snippet.deleted_at is not None or snippet.owner_id != owner.id:
        raise SnippetNotFoundError
    return snippet


async def update(
    db: AsyncSession, owner: User, snippet_id: uuid.UUID, data: SnippetUpdate
) -> SnippetOut:
    snippet = await own(db, owner, snippet_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        # Only the filename can be cleared; null elsewhere means "unchanged".
        if value is not None or field == "filename":
            setattr(snippet, field, value)
    await db.commit()
    await db.refresh(snippet)
    return to_out(snippet)


async def remove(db: AsyncSession, owner: User, snippet_id: uuid.UUID) -> None:
    snippet = await own(db, owner, snippet_id)
    snippet.deleted_at = datetime.now(UTC)
    await db.execute(delete(Pin).where(Pin.item_type == "snippet", Pin.item_id == snippet.id))
    await db.commit()


async def _page(
    db: AsyncSession, stmt: Select[tuple[Snippet]], *, cursor: uuid.UUID | None, limit: int
) -> SnippetPage:
    if cursor is not None:
        stmt = stmt.where(Snippet.id < cursor)
    rows = list(await db.scalars(stmt.order_by(Snippet.id.desc()).limit(limit + 1)))
    more = len(rows) > limit
    rows = rows[:limit]
    return SnippetPage(items=[to_out(s) for s in rows], next_cursor=rows[-1].id if more else None)


async def by_owner(
    db: AsyncSession, viewer: User | None, owner: User, *, cursor: uuid.UUID | None, limit: int
) -> SnippetPage:
    stmt = select(Snippet).where(
        Snippet.owner_id == owner.id, visible_to(viewer.id if viewer else None)
    )
    return await _page(db, stmt, cursor=cursor, limit=limit)


async def by_ids(
    db: AsyncSession, viewer_id: uuid.UUID | None, ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, Snippet]:
    """The snippets among `ids` that the viewer can see."""
    if not ids:
        return {}
    rows = await db.scalars(select(Snippet).where(Snippet.id.in_(ids), visible_to(viewer_id)))
    return {s.id: s for s in rows}
