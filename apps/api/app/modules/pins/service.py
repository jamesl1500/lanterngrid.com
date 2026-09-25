from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pins.models import Pin
from app.modules.pins.schemas import MAX_PINS, PinIn, PinOut, Pins
from app.modules.repos import service as repos
from app.modules.snippets import service as snippets
from app.modules.users.models import User


class PinNotFoundError(Exception):
    """Not one of your snippets or repos."""


class TooManyPinsError(Exception):
    pass


async def pins(db: AsyncSession, viewer: User | None, owner: User) -> Pins:
    rows = list(await db.scalars(select(Pin).where(Pin.user_id == owner.id).order_by(Pin.position)))
    shown = await snippets.by_ids(
        db, viewer.id if viewer else None, [p.item_id for p in rows if p.item_type == "snippet"]
    )
    found = await repos.by_ids(db, [p.item_id for p in rows if p.item_type == "repo"])
    items: list[PinOut] = []
    for p in rows:
        if p.item_type == "snippet" and p.item_id in shown:
            items.append(PinOut(type="snippet", snippet=snippets.to_out(shown[p.item_id])))
        elif p.item_type == "repo" and p.item_id in found:
            items.append(PinOut(type="repo", repo=repos.to_out(found[p.item_id])))
    return Pins(items=items)


async def pin(db: AsyncSession, user: User, item: PinIn) -> Pins:
    """Pin one of your snippets or repos to the end of your pins. Pinning twice changes nothing."""
    try:
        if item.type == "snippet":
            await snippets.own(db, user, item.id)
        else:
            await repos.own(db, user, item.id)
    except (snippets.SnippetNotFoundError, repos.RepoNotFoundError):
        raise PinNotFoundError from None
    existing = await db.get(Pin, (user.id, item.type, item.id))
    if existing is None:
        count, last = (
            await db.execute(
                select(func.count(), func.max(Pin.position)).where(Pin.user_id == user.id)
            )
        ).one()
        if count >= MAX_PINS:
            raise TooManyPinsError
        db.add(Pin(user_id=user.id, item_type=item.type, item_id=item.id, position=(last or 0) + 1))
        await db.commit()
    return await pins(db, user, user)


async def unpin(db: AsyncSession, user: User, item: PinIn) -> Pins:
    await db.execute(
        delete(Pin).where(
            Pin.user_id == user.id, Pin.item_type == item.type, Pin.item_id == item.id
        )
    )
    await db.commit()
    return await pins(db, user, user)
