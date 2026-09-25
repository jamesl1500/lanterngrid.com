"""Read public repositories from the GitHub REST API."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from app.core.config import get_settings
from app.modules.auth.github import API_URL, GitHubError

# owner/name, or a github.com URL, with or without .git or a deeper path (/tree/main, ...).
_REF = re.compile(
    r"^(?:(?:https?://)?(?:www\.)?github\.com/)?"
    r"(?P<owner>[A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))/"
    r"(?P<name>[A-Za-z0-9._-]{1,100}?)(?:\.git)?(?:/.*)?/?$"
)


class RateLimitedError(GitHubError):
    pass


@dataclass(frozen=True)
class GitHubRepo:
    id: int
    full_name: str
    description: str | None
    homepage: str | None
    language: str | None
    stars: int
    forks: int
    open_issues: int
    topics: list[str]
    fork: bool
    archived: bool
    pushed_at: datetime | None
    etag: str | None


class NotModified:
    """GitHub says nothing changed since the ETag we sent."""


def parse_ref(text: str) -> tuple[str, str] | None:
    """(owner, name) from "owner/name" or a github.com URL, or None if it isn't one."""
    match = _REF.match(text.strip())
    if match is None or match["name"] in (".", ".."):
        return None
    return match["owner"], match["name"]


def _headers(etag: str | None) -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token := get_settings().github_token:
        headers["Authorization"] = f"Bearer {token}"
    if etag:
        headers["If-None-Match"] = etag
    return headers


def _parse(body: dict[str, Any], etag: str | None) -> GitHubRepo:
    pushed = body.get("pushed_at")
    return GitHubRepo(
        id=int(body["id"]),
        full_name=str(body["full_name"]),
        description=body.get("description") or None,
        homepage=body.get("homepage") or None,
        language=body.get("language") or None,
        stars=int(body.get("stargazers_count") or 0),
        forks=int(body.get("forks_count") or 0),
        open_issues=int(body.get("open_issues_count") or 0),
        topics=[str(t) for t in body.get("topics") or []][:20],
        fork=bool(body.get("fork")),
        archived=bool(body.get("archived")),
        pushed_at=datetime.fromisoformat(pushed) if pushed else None,
        etag=etag,
    )


async def _get(
    http: httpx.AsyncClient, path: str, etag: str | None
) -> GitHubRepo | NotModified | None:
    try:
        response = await http.get(f"{API_URL}{path}", headers=_headers(etag))
    except httpx.HTTPError as e:
        raise GitHubError("GitHub didn't answer") from e
    if response.status_code == 304:
        return NotModified()
    # Private and missing repos both answer 404 (and 451 for DMCA takedowns).
    if response.status_code in (404, 451):
        return None
    if response.status_code in (403, 429) and (
        response.headers.get("x-ratelimit-remaining") == "0" or response.status_code == 429
    ):
        raise RateLimitedError("GitHub rate limit reached")
    if response.status_code != 200:
        raise GitHubError(f"GitHub answered {response.status_code}")
    body = response.json()
    if body.get("private"):
        return None
    return _parse(body, response.headers.get("etag"))


async def fetch_by_name(http: httpx.AsyncClient, owner: str, name: str) -> GitHubRepo | None:
    """A public repo by owner/name, or None if GitHub doesn't have one."""
    found = await _get(http, f"/repos/{owner}/{name}", None)
    assert not isinstance(found, NotModified)
    return found


async def fetch_by_id(
    http: httpx.AsyncClient, github_id: int, etag: str | None = None
) -> GitHubRepo | NotModified | None:
    """By id, so renamed and transferred repos keep working."""
    return await _get(http, f"/repositories/{github_id}", etag)
