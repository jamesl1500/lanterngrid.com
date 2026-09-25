import uuid
from collections.abc import Sequence

from sqlalchemy import case, delete, func, insert, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tags.models import Tag, UserTag
from app.modules.tags.schemas import TagOut, slugify


def to_out(tag: Tag) -> TagOut:
    return TagOut(slug=tag.slug, name=tag.name, kind=tag.kind)


async def ensure_tags(db: AsyncSession, names: Sequence[str]) -> list[Tag]:
    """The tags for these names, in the same order, creating any that don't exist yet."""
    slugs = [slugify(n) for n in names]
    if not slugs:
        return []
    # ON CONFLICT DO NOTHING so two people adding the same new tag at once both succeed.
    await db.execute(
        pg_insert(Tag)
        .values([{"slug": s, "name": n} for s, n in zip(slugs, names, strict=True)])
        .on_conflict_do_nothing(index_elements=["slug"])
    )
    by_slug = {t.slug: t for t in (await db.scalars(select(Tag).where(Tag.slug.in_(slugs)))).all()}
    return [by_slug[s] for s in slugs]


async def user_tags(db: AsyncSession, user_id: uuid.UUID) -> list[TagOut]:
    rows = await db.scalars(
        select(Tag)
        .join(UserTag, UserTag.tag_id == Tag.id)
        .where(UserTag.user_id == user_id)
        .order_by(UserTag.position)
    )
    return [to_out(t) for t in rows]


async def set_user_tags(db: AsyncSession, user_id: uuid.UUID, names: Sequence[str]) -> None:
    """Replace someone's stack. The caller commits."""
    tags = await ensure_tags(db, names)
    await db.execute(delete(UserTag).where(UserTag.user_id == user_id))
    if tags:
        await db.execute(
            insert(UserTag),
            [{"user_id": user_id, "tag_id": t.id, "position": i} for i, t in enumerate(tags)],
        )


async def suggest(db: AsyncSession, query: str, limit: int) -> list[TagOut]:
    slug = slugify(query)
    popularity = (
        select(func.count()).where(UserTag.tag_id == Tag.id).correlate(Tag).scalar_subquery()
    )
    stmt = select(Tag)
    if slug:
        prefix = Tag.slug.startswith(slug, autoescape=True)
        stmt = stmt.where(or_(prefix, Tag.slug.op("%")(slug))).order_by(
            case((prefix, 0), else_=1),
            Tag.curated.desc(),
            func.similarity(Tag.slug, slug).desc(),
            popularity.desc(),
            Tag.slug,
        )
    else:
        # Nothing typed yet: the stacks people list most, curated ones first.
        stmt = stmt.order_by(popularity.desc(), Tag.curated.desc(), Tag.slug)
    return [to_out(t) for t in await db.scalars(stmt.limit(limit))]
