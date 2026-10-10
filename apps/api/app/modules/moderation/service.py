import uuid
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import Storage
from app.modules.auth import service as auth
from app.modules.media import service as media
from app.modules.messaging import service as messaging
from app.modules.messaging.models import ConversationMember, Message
from app.modules.moderation.models import ModerationCase, Report
from app.modules.moderation.schemas import (
    MAX_SNAPSHOT,
    CaseOut,
    CasePage,
    CaseResolve,
    QueueFilter,
    ReportCreate,
    ReportOut,
    SubjectKind,
)
from app.modules.posts import service as posts
from app.modules.posts.models import Comment, Post
from app.modules.snippets import service as snippets
from app.modules.snippets.models import Snippet
from app.modules.users.models import User
from app.modules.users.summary import summarize

# Reports shown with each case in the queue.
REPORTS_PER_CASE = 20


class SubjectNotFoundError(Exception):
    """It doesn't exist, or the reporter can't see it."""


class OwnSubjectError(Exception):
    """Reporting yourself or something you wrote."""


class CaseNotFoundError(Exception):
    pass


class CaseClosedError(Exception):
    pass


class ActionError(Exception):
    """The action doesn't fit this case; the message says why."""


@dataclass
class _Subject:
    author_id: uuid.UUID | None
    snapshot: str
    post_id: uuid.UUID | None = None


def _clip(snapshot: str) -> str:
    snapshot = snapshot.strip()
    return snapshot if len(snapshot) <= MAX_SNAPSHOT else snapshot[: MAX_SNAPSHOT - 1] + "…"


async def _subject(
    db: AsyncSession, reporter: User, kind: SubjectKind, subject_id: uuid.UUID
) -> _Subject:
    """What's being reported, if the reporter can see it."""
    match kind:
        case "post":
            post = await db.scalar(
                select(Post).where(Post.id == subject_id, posts.visible_to(reporter.id))
            )
            if post is not None:
                return _Subject(post.author_id, post.body_md or "(no text, only images)")
        case "comment":
            comment = await db.scalar(
                select(Comment)
                .join(Post, Post.id == Comment.post_id)
                .where(Comment.id == subject_id, posts.visible_to(reporter.id))
            )
            if comment is not None:
                return _Subject(comment.author_id, comment.body_md, post_id=comment.post_id)
        case "snippet":
            snippet = await db.scalar(
                select(Snippet).where(Snippet.id == subject_id, snippets.visible_to(reporter.id))
            )
            if snippet is not None:
                heading = " · ".join(filter(None, [snippet.title, snippet.filename]))
                return _Subject(snippet.owner_id, f"{heading}\n\n{snippet.content}")
        case "message":
            # Only people in the conversation can report its messages.
            message = await db.scalar(
                select(Message)
                .join(
                    ConversationMember,
                    ConversationMember.conversation_id == Message.conversation_id,
                )
                .where(
                    Message.id == subject_id,
                    ConversationMember.user_id == reporter.id,
                    Message.removed_at.is_(None),
                )
            )
            if message is not None:
                said = message.body
                if message.snippet is not None:
                    shared = message.snippet
                    said = f"{said}\n\n[shared snippet] {shared.title}\n{shared.content}"
                return _Subject(message.sender_id, said)
        case "user":
            person = await db.scalar(
                select(User).where(
                    User.id == subject_id,
                    User.username.is_not(None),
                    User.suspended_at.is_(None),
                )
            )
            if person is not None:
                profile = person.profile
                parts = [
                    f"{person.display_name} (@{person.username})",
                    profile.headline,
                    profile.bio,
                    profile.readme_md,
                ]
                return _Subject(person.id, "\n\n".join(p for p in parts if p))
    raise SubjectNotFoundError


async def report(db: AsyncSession, reporter: User, data: ReportCreate) -> None:
    """File a report. Reports about the same thing share one open case; reporting it again
    changes nothing."""
    subject = await _subject(db, reporter, data.subject_kind, data.subject_id)
    if subject.author_id == reporter.id:
        raise OwnSubjectError
    # Two reports at once can both try to open the case; the second finds the first's.
    await db.execute(
        pg_insert(ModerationCase)
        .values(
            subject_kind=data.subject_kind,
            subject_id=data.subject_id,
            subject_author_id=subject.author_id,
            post_id=subject.post_id,
            snapshot=_clip(subject.snapshot),
        )
        .on_conflict_do_nothing(
            index_elements=["subject_kind", "subject_id"],
            index_where=text("status = 'open'"),
        )
    )
    case_id = await db.scalar(
        select(ModerationCase.id).where(
            ModerationCase.subject_kind == data.subject_kind,
            ModerationCase.subject_id == data.subject_id,
            ModerationCase.status == "open",
        )
    )
    assert case_id is not None
    added = await db.scalar(
        pg_insert(Report)
        .values(case_id=case_id, reporter_id=reporter.id, reason=data.reason, details=data.details)
        .on_conflict_do_nothing(constraint="uq_reports_case_id_reporter_id")
        .returning(Report.id)
    )
    if added is not None:
        await db.execute(
            update(ModerationCase)
            .where(ModerationCase.id == case_id)
            .values(report_count=ModerationCase.report_count + 1)
        )
    await db.commit()


async def _gone(db: AsyncSession, cases: Sequence[ModerationCase]) -> set[uuid.UUID]:
    """The ids of reported things that no longer exist."""
    wanted: dict[str, set[uuid.UUID]] = defaultdict(set)
    for c in cases:
        wanted[c.subject_kind].add(c.subject_id)
    live: set[uuid.UUID] = set()
    for kind, ids in wanted.items():
        match kind:
            case "post":
                stmt = select(Post.id).where(Post.id.in_(ids), Post.deleted_at.is_(None))
            case "comment":
                stmt = select(Comment.id).where(Comment.id.in_(ids))
            case "snippet":
                stmt = select(Snippet.id).where(Snippet.id.in_(ids), Snippet.deleted_at.is_(None))
            case "message":
                stmt = select(Message.id).where(Message.id.in_(ids), Message.removed_at.is_(None))
            case _:
                stmt = select(User.id).where(User.id.in_(ids))
        live.update(await db.scalars(stmt))
    return {c.subject_id for c in cases} - live


async def _outs(db: AsyncSession, cases: Sequence[ModerationCase]) -> list[CaseOut]:
    reports: dict[uuid.UUID, list[ReportOut]] = defaultdict(list)
    if cases:
        rows = await db.scalars(
            select(Report)
            .where(Report.case_id.in_([c.id for c in cases]))
            .order_by(Report.id.desc())
        )
        for r in rows:
            if len(reports[r.case_id]) < REPORTS_PER_CASE:
                reports[r.case_id].append(
                    ReportOut(
                        id=r.id,
                        reporter=summarize(r.reporter),
                        reason=r.reason,
                        details=r.details,
                        created_at=r.created_at,
                    )
                )
    gone = await _gone(db, cases)
    return [
        CaseOut(
            id=c.id,
            subject_kind=c.subject_kind,
            subject_id=c.subject_id,
            subject_author=summarize(c.subject_author)
            if c.subject_author and c.subject_author.username
            else None,
            author_suspended=c.subject_author is not None
            and c.subject_author.suspended_at is not None,
            post_id=c.post_id,
            snapshot=c.snapshot,
            subject_gone=c.subject_id in gone,
            status=c.status,
            report_count=c.report_count,
            reports=reports[c.id],
            created_at=c.created_at,
            resolved_at=c.resolved_at,
            resolved_by=summarize(c.resolved_by)
            if c.resolved_by and c.resolved_by.username
            else None,
            note=c.note,
        )
        for c in cases
    ]


async def queue(
    db: AsyncSession, which: QueueFilter, *, cursor: uuid.UUID | None, limit: int
) -> CasePage:
    """Open cases, or closed ones, newest first."""
    stmt = select(ModerationCase).where(
        ModerationCase.status == "open" if which == "open" else ModerationCase.status != "open"
    )
    if cursor is not None:
        stmt = stmt.where(ModerationCase.id < cursor)
    rows = list(await db.scalars(stmt.order_by(ModerationCase.id.desc()).limit(limit + 1)))
    more = len(rows) > limit
    rows = rows[:limit]
    return CasePage(items=await _outs(db, rows), next_cursor=rows[-1].id if more else None)


async def open_count(db: AsyncSession) -> int:
    count = await db.scalar(
        select(func.count()).select_from(ModerationCase).where(ModerationCase.status == "open")
    )
    return count or 0


async def _remove_subject(db: AsyncSession, found: ModerationCase) -> list[str]:
    """Delete the reported thing if it's still there. Returns storage keys to discard."""
    subject_id = found.subject_id
    match found.subject_kind:
        case "post":
            post = await db.get(Post, subject_id)
            if post is not None and post.deleted_at is None:
                return await posts.delete_post(db, post)
        case "comment":
            comment = await db.get(Comment, subject_id)
            if comment is not None:
                await posts.delete_comment(db, comment)
        case "snippet":
            snippet = await db.get(Snippet, subject_id)
            if snippet is not None and snippet.deleted_at is None:
                await snippets.delete_snippet(db, snippet)
        case "message":
            message = await db.get(Message, subject_id)
            if message is not None and message.removed_at is None:
                await messaging.remove_message(db, message)
        case _:
            raise ActionError("There's nothing to remove for a person. Suspend them instead.")
    return []


async def _suspend(db: AsyncSession, moderator: User, person: User, note: str | None) -> None:
    """Suspend an account: sign it out everywhere and close its other open cases."""
    if person.id == moderator.id:
        raise ActionError("You can't suspend yourself.")
    if person.is_moderator:
        raise ActionError("Moderators can't be suspended. Take their moderator role away first.")
    now = datetime.now(UTC)
    person.suspended_at = person.suspended_at or now
    await auth.end_all_sessions(db, person)
    await db.execute(
        update(ModerationCase)
        .where(ModerationCase.subject_author_id == person.id, ModerationCase.status == "open")
        .values(status="suspended", resolved_at=now, resolved_by_id=moderator.id, note=note)
    )


async def resolve(
    db: AsyncSession, storage: Storage, moderator: User, case_id: uuid.UUID, data: CaseResolve
) -> CaseOut:
    found = await db.get(ModerationCase, case_id)
    if found is None:
        raise CaseNotFoundError
    if found.status != "open":
        raise CaseClosedError
    discard: list[str] = []
    match data.action:
        case "dismiss":
            found.status = "dismissed"
        case "remove":
            discard = await _remove_subject(db, found)
            found.status = "removed"
        case "suspend":
            if found.subject_author is None:
                raise ActionError("That account no longer exists.")
            await _suspend(db, moderator, found.subject_author, data.note)
            found.status = "suspended"
    found.resolved_at = datetime.now(UTC)
    found.resolved_by_id = moderator.id
    found.note = data.note
    await db.commit()
    for key in discard:
        await media.discard(storage, key)
    await db.refresh(found)
    return (await _outs(db, [found]))[0]


async def lift_suspension(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Let a suspended person back in. Their old sessions stay ended; they sign in again."""
    person = await db.get(User, user_id)
    if person is None:
        raise SubjectNotFoundError
    person.suspended_at = None
    await db.commit()
