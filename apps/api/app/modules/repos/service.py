import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

import httpx
import structlog
from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.auth.github import GitHubError
from app.modules.pins.models import Pin
from app.modules.repos import github
from app.modules.repos.models import Repo
from app.modules.repos.schemas import MAX_REPOS, RepoOut, RepoPage
from app.modules.users.models import User
from app.modules.users.summary import summarize

log = structlog.get_logger()


class RepoNotFoundError(Exception):
    pass


class BadRepoRefError(Exception):
    pass


class NotOnGitHubError(Exception):
    pass


class DuplicateRepoError(Exception):
    pass


class TooManyReposError(Exception):
    pass


def to_out(repo: Repo) -> RepoOut:
    return RepoOut(
        id=repo.id,
        owner=summarize(repo.owner),
        full_name=repo.full_name,
        url=f"https://github.com/{repo.full_name}",
        description=repo.description,
        homepage=repo.homepage,
        language=repo.language,
        stars=repo.stars,
        forks=repo.forks,
        open_issues=repo.open_issues,
        topics=list(repo.topics),
        fork=repo.fork,
        archived=repo.archived,
        pushed_at=repo.pushed_at,
        fetched_at=repo.fetched_at,
        missing=repo.missing_since is not None,
        created_at=repo.created_at,
    )


def _apply(repo: Repo, data: github.GitHubRepo, now: datetime) -> None:
    repo.full_name = data.full_name
    repo.description = data.description[:1000] if data.description else None
    repo.homepage = data.homepage[:500] if data.homepage else None
    repo.language = data.language[:64] if data.language else None
    repo.stars = data.stars
    repo.forks = data.forks
    repo.open_issues = data.open_issues
    repo.topics = [t[:50] for t in data.topics]
    repo.fork = data.fork
    repo.archived = data.archived
    repo.pushed_at = data.pushed_at
    repo.etag = data.etag
    repo.fetched_at = now
    repo.missing_since = None


async def add(db: AsyncSession, http: httpx.AsyncClient, owner: User, text: str) -> RepoOut:
    """Add a public GitHub repo to someone's profile, reading its stats now."""
    ref = github.parse_ref(text)
    if ref is None:
        raise BadRepoRefError
    count = await db.scalar(select(func.count()).where(Repo.owner_id == owner.id))
    if (count or 0) >= MAX_REPOS:
        raise TooManyReposError
    data = await github.fetch_by_name(http, *ref)
    if data is None:
        raise NotOnGitHubError
    existing = await db.scalar(
        select(Repo.id).where(Repo.owner_id == owner.id, Repo.github_id == data.id)
    )
    if existing is not None:
        raise DuplicateRepoError
    repo = Repo(owner_id=owner.id, github_id=data.id)
    _apply(repo, data, datetime.now(UTC))
    db.add(repo)
    await db.commit()
    await db.refresh(repo)
    return to_out(repo)


async def get(db: AsyncSession, repo_id: uuid.UUID) -> Repo:
    repo = await db.get(Repo, repo_id)
    if repo is None:
        raise RepoNotFoundError
    return repo


async def own(db: AsyncSession, owner: User, repo_id: uuid.UUID) -> Repo:
    repo = await db.get(Repo, repo_id)
    if repo is None or repo.owner_id != owner.id:
        raise RepoNotFoundError
    return repo


async def remove(db: AsyncSession, owner: User, repo_id: uuid.UUID) -> None:
    """Posts that shared it keep their text and show that the repo is gone."""
    repo = await own(db, owner, repo_id)
    await db.execute(delete(Pin).where(Pin.item_type == "repo", Pin.item_id == repo.id))
    await db.delete(repo)
    await db.commit()


async def by_owner(
    db: AsyncSession, owner: User, *, cursor: uuid.UUID | None, limit: int
) -> RepoPage:
    stmt: Select[tuple[Repo]] = select(Repo).where(Repo.owner_id == owner.id)
    if cursor is not None:
        stmt = stmt.where(Repo.id < cursor)
    rows = list(await db.scalars(stmt.order_by(Repo.id.desc()).limit(limit + 1)))
    more = len(rows) > limit
    rows = rows[:limit]
    return RepoPage(items=[to_out(r) for r in rows], next_cursor=rows[-1].id if more else None)


async def by_ids(db: AsyncSession, ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, Repo]:
    if not ids:
        return {}
    return {r.id: r for r in await db.scalars(select(Repo).where(Repo.id.in_(ids)))}


async def refresh_stale(db: AsyncSession, http: httpx.AsyncClient, *, limit: int = 100) -> int:
    """Re-read the stalest repos from GitHub. Returns how many were checked.

    Stops early when GitHub rate-limits us; the rest wait for the next run.
    """
    now = datetime.now(UTC)
    cutoff = now - timedelta(hours=get_settings().repo_refresh_hours)
    repos = list(
        await db.scalars(
            select(Repo).where(Repo.fetched_at < cutoff).order_by(Repo.fetched_at).limit(limit)
        )
    )
    checked = 0
    for repo in repos:
        try:
            found = await github.fetch_by_id(http, repo.github_id, repo.etag)
        except github.RateLimitedError:
            log.warning("repos.refresh.rate_limited", checked=checked)
            break
        except GitHubError as e:
            # One bad answer shouldn't hold up the rest; try this one again next run.
            log.warning("repos.refresh.failed", repo=repo.full_name, error=str(e))
            continue
        if isinstance(found, github.NotModified):
            repo.fetched_at = now
            repo.missing_since = None
        elif found is None:
            repo.fetched_at = now
            repo.missing_since = repo.missing_since or now
        else:
            _apply(repo, found, now)
        checked += 1
    await db.commit()
    log.info("repos.refresh.done", checked=checked, stale=len(repos))
    return checked
