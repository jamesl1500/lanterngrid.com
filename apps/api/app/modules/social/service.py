import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import (
    ColumnElement,
    Select,
    and_,
    case,
    delete,
    exists,
    func,
    literal,
    or_,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.modules.notifications import service as notifications
from app.modules.social.models import Block, FriendRequest, Friendship
from app.modules.social.schemas import (
    FriendRequestOut,
    FriendRequestPage,
    RequestDirection,
    UserPage,
)
from app.modules.users.models import User
from app.modules.users.schemas import Relationship
from app.modules.users.summary import summarize


class NotAllowedError(Exception):
    """Blocked either way, or asking to befriend yourself."""


class AlreadyFriendsError(Exception):
    pass


class NotFoundError(Exception):
    pass


class TooSoonError(Exception):
    """They declined a request from this sender recently."""


# After a decline, the same person can't ask again for this long.
DECLINE_COOLDOWN = timedelta(days=7)


def _pair(a: uuid.UUID, b: uuid.UUID) -> tuple[uuid.UUID, uuid.UUID]:
    return (a, b) if a < b else (b, a)


def _between(a: uuid.UUID, b: uuid.UUID) -> ColumnElement[bool]:
    return or_(
        and_(FriendRequest.sender_id == a, FriendRequest.recipient_id == b),
        and_(FriendRequest.sender_id == b, FriendRequest.recipient_id == a),
    )


def friend_ids_of(user_id: uuid.UUID) -> Select[tuple[uuid.UUID]]:
    """A subquery of the ids of someone's friends, for use in other features' queries."""
    return select(
        case((Friendship.user_a_id == user_id, Friendship.user_b_id), else_=Friendship.user_a_id)
    ).where(or_(Friendship.user_a_id == user_id, Friendship.user_b_id == user_id))


def blocked_either_way(
    viewer_id: uuid.UUID,
    other_id: uuid.UUID | ColumnElement[uuid.UUID] | InstrumentedAttribute[uuid.UUID],
) -> ColumnElement[bool]:
    """True when either person has blocked the other. `other_id` may be a column."""
    return exists().where(
        or_(
            and_(Block.blocker_id == viewer_id, Block.blocked_id == other_id),
            and_(Block.blocker_id == other_id, Block.blocked_id == viewer_id),
        )
    )


def can_see(
    viewer_id: uuid.UUID | None,
    author_id: InstrumentedAttribute[uuid.UUID],
    visibility: InstrumentedAttribute[str],
) -> ColumnElement[bool]:
    """Whether the viewer may see something with this author and public/friends visibility:
    public things, their own, and their friends' friends-only ones, minus anything from people
    either side has blocked. Signed out (None), only public things."""
    if viewer_id is None:
        return visibility == "public"
    return and_(
        ~blocked_either_way(viewer_id, author_id),
        or_(
            visibility == "public",
            author_id == viewer_id,
            author_id.in_(friend_ids_of(viewer_id)),
        ),
    )


async def has_blocked(db: AsyncSession, blocker_id: uuid.UUID, blocked_id: uuid.UUID) -> bool:
    return await db.get(Block, (blocker_id, blocked_id)) is not None


async def are_friends(db: AsyncSession, a: uuid.UUID, b: uuid.UUID) -> bool:
    return await db.get(Friendship, _pair(a, b)) is not None


async def _pending_between(db: AsyncSession, a: uuid.UUID, b: uuid.UUID) -> FriendRequest | None:
    return (
        await db.execute(
            select(FriendRequest).where(_between(a, b), FriendRequest.status == "pending")
        )
    ).scalar_one_or_none()


async def relationship(db: AsyncSession, viewer: User, other: User) -> Relationship:
    if viewer.id == other.id:
        return Relationship(status="self")
    if await has_blocked(db, viewer.id, other.id):
        return Relationship(status="blocked")
    if await are_friends(db, viewer.id, other.id):
        return Relationship(status="friends")
    pending = await _pending_between(db, viewer.id, other.id)
    if pending is None:
        return Relationship(status="none")
    status = "request_sent" if pending.sender_id == viewer.id else "request_received"
    return Relationship(status=status, request_id=pending.id)


async def friend_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    count = await db.scalar(
        select(func.count())
        .select_from(Friendship)
        .where(or_(Friendship.user_a_id == user_id, Friendship.user_b_id == user_id))
    )
    return count or 0


def _request_out(request: FriendRequest, other: User) -> FriendRequestOut:
    return FriendRequestOut(
        id=request.id,
        status=request.status,
        user=summarize(other),
        created_at=request.created_at,
    )


async def _befriend(db: AsyncSession, request: FriendRequest) -> None:
    request.status = "accepted"
    request.responded_at = datetime.now(UTC)
    a, b = _pair(request.sender_id, request.recipient_id)
    await db.execute(
        pg_insert(Friendship).values(user_a_id=a, user_b_id=b).on_conflict_do_nothing()
    )
    await notifications.mark_subject_read(db, request.recipient_id, request.id)
    notifications.notify(
        db,
        user_id=request.sender_id,
        kind="friend_accepted",
        actor_id=request.recipient_id,
        subject_id=request.id,
    )


async def send_request(db: AsyncSession, sender: User, recipient: User) -> FriendRequestOut:
    """Ask to be friends. If they already asked you, this accepts their request instead."""
    if sender.id == recipient.id:
        raise NotAllowedError
    if await db.scalar(select(blocked_either_way(sender.id, recipient.id))):
        raise NotAllowedError
    if await are_friends(db, sender.id, recipient.id):
        raise AlreadyFriendsError

    pending = await _pending_between(db, sender.id, recipient.id)
    if pending is not None:
        if pending.recipient_id == sender.id:
            await _befriend(db, pending)
            await db.commit()
        return _request_out(pending, recipient)  # sending twice is harmless

    declined_recently = await db.scalar(
        select(
            exists().where(
                FriendRequest.sender_id == sender.id,
                FriendRequest.recipient_id == recipient.id,
                FriendRequest.status == "declined",
                FriendRequest.responded_at > datetime.now(UTC) - DECLINE_COOLDOWN,
            )
        )
    )
    if declined_recently:
        raise TooSoonError

    request = FriendRequest(sender_id=sender.id, recipient_id=recipient.id)
    db.add(request)
    try:
        await db.flush()
    except IntegrityError:  # they sent one at the same moment
        await db.rollback()
        return await send_request(db, sender, recipient)
    notifications.notify(
        db,
        user_id=recipient.id,
        kind="friend_request",
        actor_id=sender.id,
        subject_id=request.id,
    )
    await db.commit()
    await db.refresh(request)
    return _request_out(request, recipient)


async def _open_request(db: AsyncSession, request_id: uuid.UUID) -> FriendRequest:
    request = await db.get(FriendRequest, request_id, with_for_update=True)
    if request is None or request.status != "pending":
        raise NotFoundError
    return request


async def respond(
    db: AsyncSession, user: User, request_id: uuid.UUID, *, accept: bool
) -> FriendRequestOut:
    request = await _open_request(db, request_id)
    if request.recipient_id != user.id:
        raise NotFoundError
    if accept:
        await _befriend(db, request)
    else:
        # Declining is quiet: the sender gets no notification. They can ask again after
        # DECLINE_COOLDOWN; blocking is for people who shouldn't.
        request.status = "declined"
        request.responded_at = datetime.now(UTC)
        await notifications.mark_subject_read(db, user.id, request.id)
    await db.commit()
    sender = await db.get_one(User, request.sender_id)
    return _request_out(request, sender)


async def cancel(db: AsyncSession, user: User, request_id: uuid.UUID) -> FriendRequestOut:
    request = await _open_request(db, request_id)
    if request.sender_id != user.id:
        raise NotFoundError
    request.status = "cancelled"
    request.responded_at = datetime.now(UTC)
    await notifications.withdraw(db, request.id)
    await db.commit()
    recipient = await db.get_one(User, request.recipient_id)
    return _request_out(request, recipient)


async def unfriend(db: AsyncSession, user: User, other: User) -> None:
    a, b = _pair(user.id, other.id)
    result = await db.execute(
        delete(Friendship).where(Friendship.user_a_id == a, Friendship.user_b_id == b)
    )
    if result.rowcount == 0:  # type: ignore[attr-defined]
        raise NotFoundError
    await db.commit()


async def _close_requests_between(db: AsyncSession, a: uuid.UUID, b: uuid.UUID) -> None:
    ids = list(
        await db.scalars(
            update(FriendRequest)
            .where(_between(a, b), FriendRequest.status == "pending")
            .values(status="cancelled", responded_at=datetime.now(UTC))
            .returning(FriendRequest.id)
        )
    )
    for request_id in ids:
        await notifications.withdraw(db, request_id)


async def block(db: AsyncSession, user: User, other: User) -> None:
    """Block someone: ends the friendship and any open request, and hides each from the other."""
    if user.id == other.id:
        raise NotAllowedError
    await db.execute(
        pg_insert(Block).values(blocker_id=user.id, blocked_id=other.id).on_conflict_do_nothing()
    )
    a, b = _pair(user.id, other.id)
    await db.execute(delete(Friendship).where(Friendship.user_a_id == a, Friendship.user_b_id == b))
    await _close_requests_between(db, user.id, other.id)
    await db.commit()


async def unblock(db: AsyncSession, user: User, other: User) -> None:
    await db.execute(delete(Block).where(Block.blocker_id == user.id, Block.blocked_id == other.id))
    await db.commit()


def _user_page(users: Sequence[User], limit: int) -> UserPage:
    more = len(users) > limit
    users = users[:limit]
    return UserPage(items=[summarize(u) for u in users], next_cursor=users[-1].id if more else None)


async def friends(
    db: AsyncSession, user_id: uuid.UUID, *, cursor: uuid.UUID | None, limit: int
) -> UserPage:
    stmt = select(User).where(User.id.in_(friend_ids_of(user_id)))
    if cursor is not None:
        stmt = stmt.where(User.id < cursor)
    users = list(await db.scalars(stmt.order_by(User.id.desc()).limit(limit + 1)))
    return _user_page(users, limit)


async def blocked(db: AsyncSession, user_id: uuid.UUID) -> list[User]:
    return list(
        await db.scalars(
            select(User)
            .join(Block, Block.blocked_id == User.id)
            .where(Block.blocker_id == user_id)
            .order_by(Block.created_at.desc())
        )
    )


async def requests(
    db: AsyncSession,
    user_id: uuid.UUID,
    direction: RequestDirection,
    *,
    cursor: uuid.UUID | None,
    limit: int,
) -> FriendRequestPage:
    mine, theirs = (
        (FriendRequest.recipient_id, FriendRequest.sender_id)
        if direction == "incoming"
        else (FriendRequest.sender_id, FriendRequest.recipient_id)
    )
    stmt = (
        select(FriendRequest, User)
        .join(User, User.id == theirs)
        .where(mine == user_id, FriendRequest.status == "pending")
    )
    if cursor is not None:
        stmt = stmt.where(FriendRequest.id < cursor)
    rows = list(
        (await db.execute(stmt.order_by(FriendRequest.id.desc()).limit(limit + 1))).tuples()
    )
    more = len(rows) > limit
    rows = rows[:limit]
    return FriendRequestPage(
        items=[_request_out(r, u) for r, u in rows],
        next_cursor=rows[-1][0].id if more else None,
    )


async def search_people(
    db: AsyncSession, viewer: User | None, query: str, limit: int
) -> list[User]:
    """Match usernames by prefix and names loosely. Friends rank first, blocked people never
    show."""
    q = query.strip().lstrip("@").lower()
    if not q:
        return []
    username = func.lower(User.username)
    name = func.lower(User.display_name)
    prefix = username.startswith(q, autoescape=True)
    stmt = select(User).where(
        User.username.is_not(None),
        or_(prefix, name.contains(q, autoescape=True), name.op("%")(q)),
    )
    friend_rank: ColumnElement[int] = literal(1)
    if viewer is not None:
        stmt = stmt.where(User.id != viewer.id, ~blocked_either_way(viewer.id, User.id))
        friend_rank = case((User.id.in_(friend_ids_of(viewer.id)), 0), else_=1)
    stmt = stmt.order_by(
        case((username == q, 0), else_=1),
        friend_rank,
        case((prefix, 0), else_=1),
        func.similarity(name, q).desc(),
        username,
    )
    return list(await db.scalars(stmt.limit(limit)))
