import uuid
from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import and_, delete, func, or_, select, tuple_, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ids import uuid7
from app.modules.messaging.models import Conversation, ConversationMember, Message
from app.modules.messaging.schemas import (
    MAX_GROUP_SIZE,
    ConversationCreate,
    ConversationOut,
    ConversationPage,
    MemberOut,
    MessageCreate,
    MessageOut,
    MessagePage,
)
from app.modules.realtime import bus
from app.modules.social import service as social
from app.modules.users.models import User
from app.modules.users.summary import summarize


class ConversationNotFoundError(Exception):
    pass


class NotFriendsError(Exception):
    """Messages only go between friends (and not across a block)."""

    def __init__(self, username: str) -> None:
        super().__init__(username)
        self.username = username


class UnknownPeopleError(Exception):
    def __init__(self, usernames: list[str]) -> None:
        super().__init__(usernames)
        self.usernames = usernames


class GroupFullError(Exception):
    pass


class NotAGroupError(Exception):
    pass


class NotOwnerError(Exception):
    pass


def _dm_key(a: uuid.UUID, b: uuid.UUID) -> str:
    low, high = sorted((a, b))
    return f"{low}:{high}"


def message_out(m: Message) -> MessageOut:
    return MessageOut(
        id=m.id,
        conversation_id=m.conversation_id,
        sender=summarize(m.sender) if m.sender else None,
        body=m.body,
        client_id=m.client_id,
        created_at=m.created_at,
    )


async def _people(db: AsyncSession, me: User, usernames: Sequence[str]) -> list[User]:
    """The friends named in `usernames`, without duplicates or yourself."""
    wanted = {u.strip().lstrip("@").lower() for u in usernames} - {(me.username or "").lower()}
    found = list(await db.scalars(select(User).where(func.lower(User.username).in_(wanted))))
    missing = sorted(wanted - {str(u.username).lower() for u in found})
    if missing:
        raise UnknownPeopleError(missing)
    for person in found:
        if not await _can_message(db, me.id, person.id):
            raise NotFriendsError(str(person.username))
    return sorted(found, key=lambda u: str(u.username))


async def _can_message(db: AsyncSession, a: uuid.UUID, b: uuid.UUID) -> bool:
    if not await social.are_friends(db, a, b):
        return False
    blocked = await db.scalar(select(social.blocked_either_way(a, b)))
    return not blocked


async def member_ids(db: AsyncSession, conversation_id: uuid.UUID) -> list[uuid.UUID]:
    return list(
        await db.scalars(
            select(ConversationMember.user_id).where(
                ConversationMember.conversation_id == conversation_id
            )
        )
    )


async def create(db: AsyncSession, me: User, data: ConversationCreate) -> ConversationOut:
    people = await _people(db, me, data.usernames)
    if not people:
        raise UnknownPeopleError([])
    if len(people) == 1 and not data.title:
        # Two people share one DM, however many times either starts it.
        key = _dm_key(me.id, people[0].id)
        conversation = await db.scalar(select(Conversation).where(Conversation.dm_key == key))
        if conversation is None:
            conversation = Conversation(kind="dm", dm_key=key, created_by=me.id)
            db.add(conversation)
            await db.flush()
            db.add_all(
                ConversationMember(conversation_id=conversation.id, user_id=u.id, role="member")
                for u in (me, people[0])
            )
            await db.commit()
            await bus.publish(
                [people[0].id],
                {"type": "conversation.updated", "conversation_id": str(conversation.id)},
            )
        return (await outs(db, me, [conversation]))[0]
    if len(people) + 1 > MAX_GROUP_SIZE:
        raise GroupFullError
    conversation = Conversation(kind="group", title=data.title or None, created_by=me.id)
    db.add(conversation)
    await db.flush()
    db.add(ConversationMember(conversation_id=conversation.id, user_id=me.id, role="owner"))
    db.add_all(ConversationMember(conversation_id=conversation.id, user_id=u.id) for u in people)
    await db.commit()
    await bus.publish(
        [u.id for u in people],
        {"type": "conversation.updated", "conversation_id": str(conversation.id)},
    )
    return (await outs(db, me, [conversation]))[0]


async def _membership(
    db: AsyncSession, me: User, conversation_id: uuid.UUID
) -> tuple[Conversation, ConversationMember]:
    row = (
        await db.execute(
            select(Conversation, ConversationMember)
            .join(ConversationMember, ConversationMember.conversation_id == Conversation.id)
            .where(Conversation.id == conversation_id, ConversationMember.user_id == me.id)
        )
    ).first()
    if row is None:
        raise ConversationNotFoundError
    return row[0], row[1]


async def get(db: AsyncSession, me: User, conversation_id: uuid.UUID) -> ConversationOut:
    conversation, _ = await _membership(db, me, conversation_id)
    return (await outs(db, me, [conversation]))[0]


def _unread_filter(me: User) -> list[object]:
    return [
        or_(
            ConversationMember.last_read_message_id.is_(None),
            Message.id > ConversationMember.last_read_message_id,
        ),
        or_(Message.sender_id.is_(None), Message.sender_id != me.id),
    ]


async def outs(
    db: AsyncSession, me: User, conversations: Sequence[Conversation]
) -> list[ConversationOut]:
    ids = [c.id for c in conversations]
    if not ids:
        return []
    members: dict[uuid.UUID, list[ConversationMember]] = defaultdict(list)
    for m in await db.scalars(
        select(ConversationMember)
        .where(ConversationMember.conversation_id.in_(ids))
        .order_by(ConversationMember.joined_at)
    ):
        members[m.conversation_id].append(m)
    last: dict[uuid.UUID, Message] = {
        m.conversation_id: m
        for m in await db.scalars(
            select(Message)
            .where(Message.conversation_id.in_(ids))
            .distinct(Message.conversation_id)
            .order_by(Message.conversation_id, Message.id.desc())
        )
    }
    unread: dict[uuid.UUID, int] = dict(
        (
            await db.execute(
                select(Message.conversation_id, func.count())
                .join(
                    ConversationMember,
                    and_(
                        ConversationMember.conversation_id == Message.conversation_id,
                        ConversationMember.user_id == me.id,
                    ),
                )
                .where(Message.conversation_id.in_(ids), *_unread_filter(me))  # type: ignore[arg-type]
                .group_by(Message.conversation_id)
            )
        )
        .tuples()
        .all()
    )
    return [
        ConversationOut(
            id=c.id,
            kind=c.kind,
            title=c.title,
            members=[
                MemberOut(
                    user=summarize(m.user),
                    role=m.role,
                    last_read_message_id=m.last_read_message_id,
                )
                for m in members[c.id]
            ],
            last_message=message_out(last[c.id]) if c.id in last else None,
            unread_count=unread.get(c.id, 0),
            last_message_at=c.last_message_at,
            created_at=c.created_at,
        )
        for c in conversations
    ]


def _encode_cursor(c: Conversation) -> str:
    return f"{c.last_message_at.isoformat()}|{c.id}"


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    at, _, id_ = cursor.partition("|")
    return datetime.fromisoformat(at), uuid.UUID(id_)


async def inbox(db: AsyncSession, me: User, *, cursor: str | None, limit: int) -> ConversationPage:
    stmt = (
        select(Conversation)
        .join(ConversationMember, ConversationMember.conversation_id == Conversation.id)
        .where(ConversationMember.user_id == me.id)
    )
    if cursor:
        at, id_ = _decode_cursor(cursor)
        stmt = stmt.where(tuple_(Conversation.last_message_at, Conversation.id) < (at, id_))
    rows = list(
        await db.scalars(
            stmt.order_by(Conversation.last_message_at.desc(), Conversation.id.desc()).limit(
                limit + 1
            )
        )
    )
    more = len(rows) > limit
    rows = rows[:limit]
    return ConversationPage(
        items=await outs(db, me, rows), next_cursor=_encode_cursor(rows[-1]) if more else None
    )


async def unread_conversations(db: AsyncSession, me: User) -> int:
    count = await db.scalar(
        select(func.count(func.distinct(Message.conversation_id)))
        .join(
            ConversationMember,
            and_(
                ConversationMember.conversation_id == Message.conversation_id,
                ConversationMember.user_id == me.id,
            ),
        )
        .where(*_unread_filter(me))  # type: ignore[arg-type]
    )
    return count or 0


async def messages(
    db: AsyncSession,
    me: User,
    conversation_id: uuid.UUID,
    *,
    before: uuid.UUID | None,
    after: uuid.UUID | None,
    limit: int,
) -> MessagePage:
    """The latest messages, those before a cursor (scrolling up) or after one (catching up
    after a reconnect). Always oldest first."""
    await _membership(db, me, conversation_id)
    stmt = select(Message).where(Message.conversation_id == conversation_id)
    if after is not None:
        rows = list(
            await db.scalars(stmt.where(Message.id > after).order_by(Message.id).limit(limit))
        )
        return MessagePage(items=[message_out(m) for m in rows], older_cursor=None)
    if before is not None:
        stmt = stmt.where(Message.id < before)
    rows = list(await db.scalars(stmt.order_by(Message.id.desc()).limit(limit + 1)))
    more = len(rows) > limit
    rows = rows[:limit]
    rows.reverse()
    return MessagePage(
        items=[message_out(m) for m in rows], older_cursor=rows[0].id if more and rows else None
    )


async def send(
    db: AsyncSession, me: User, conversation_id: uuid.UUID, data: MessageCreate
) -> MessageOut:
    conversation, membership = await _membership(db, me, conversation_id)
    ids = await member_ids(db, conversation_id)
    if conversation.kind == "dm":
        other = next((i for i in ids if i != me.id), None)
        if other is None or not await _can_message(db, me.id, other):
            raise NotFriendsError("")
    inserted = await db.scalar(
        pg_insert(Message)
        .values(
            id=uuid7(),
            conversation_id=conversation_id,
            sender_id=me.id,
            body=data.body,
            client_id=data.client_id,
        )
        .on_conflict_do_nothing(constraint="uq_messages_client_id")
        .returning(Message.id)
    )
    message = await db.scalar(
        select(Message).where(
            Message.conversation_id == conversation_id,
            Message.sender_id == me.id,
            Message.client_id == data.client_id,
        )
    )
    assert message is not None
    if inserted is None:
        # A retry of a message that already went out.
        return message_out(message)
    conversation.last_message_at = message.created_at
    # Your own message counts as read.
    membership.last_read_message_id = message.id
    await db.commit()
    out = message_out(message)
    await bus.publish(ids, {"type": "message.created", "message": out.model_dump(mode="json")})
    return out


async def mark_read(
    db: AsyncSession, me: User, conversation_id: uuid.UUID, message_id: uuid.UUID
) -> None:
    """Move the read marker forward (never back) to a message in this conversation."""
    await _membership(db, me, conversation_id)
    exists_ = await db.scalar(
        select(Message.id).where(
            Message.id == message_id, Message.conversation_id == conversation_id
        )
    )
    if exists_ is None:
        raise ConversationNotFoundError
    moved = await db.execute(
        update(ConversationMember)
        .where(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id == me.id,
            or_(
                ConversationMember.last_read_message_id.is_(None),
                ConversationMember.last_read_message_id < message_id,
            ),
        )
        .values(last_read_message_id=message_id)
    )
    await db.commit()
    if moved.rowcount:  # type: ignore[attr-defined]
        await bus.publish(
            await member_ids(db, conversation_id),
            {
                "type": "conversation.read",
                "conversation_id": str(conversation_id),
                "user_id": str(me.id),
                "message_id": str(message_id),
            },
        )


async def add_members(
    db: AsyncSession, me: User, conversation_id: uuid.UUID, usernames: Sequence[str]
) -> ConversationOut:
    conversation, membership = await _membership(db, me, conversation_id)
    if conversation.kind != "group":
        raise NotAGroupError
    if membership.role != "owner":
        raise NotOwnerError
    current = set(await member_ids(db, conversation_id))
    people = [p for p in await _people(db, me, usernames) if p.id not in current]
    if len(current) + len(people) > MAX_GROUP_SIZE:
        raise GroupFullError
    db.add_all(ConversationMember(conversation_id=conversation.id, user_id=p.id) for p in people)
    await db.commit()
    await bus.publish(
        current | {p.id for p in people},
        {"type": "conversation.updated", "conversation_id": str(conversation.id)},
    )
    return (await outs(db, me, [conversation]))[0]


async def leave(db: AsyncSession, me: User, conversation_id: uuid.UUID) -> None:
    """Leave a group. The next longest-standing member becomes owner; an empty group goes."""
    conversation, membership = await _membership(db, me, conversation_id)
    if conversation.kind != "group":
        raise NotAGroupError
    await db.delete(membership)
    await db.flush()
    remaining = list(
        await db.scalars(
            select(ConversationMember)
            .where(ConversationMember.conversation_id == conversation_id)
            .order_by(ConversationMember.joined_at)
        )
    )
    if not remaining:
        await db.execute(delete(Conversation).where(Conversation.id == conversation_id))
    elif membership.role == "owner":
        remaining[0].role = "owner"
    await db.commit()
    await bus.publish(
        [m.user_id for m in remaining],
        {"type": "conversation.updated", "conversation_id": str(conversation_id)},
    )
