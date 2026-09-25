from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import update

from app.core.db import SessionLocal
from app.main import app
from app.modules.auth import github as github_auth
from app.modules.repos import github, service
from app.modules.repos.models import Repo
from tests.fakes import FakeGitHub


@pytest.fixture
def gh() -> Iterator[FakeGitHub]:
    fake = FakeGitHub()
    app.dependency_overrides[github_auth.get_http] = fake.client
    yield fake
    app.dependency_overrides.pop(github_auth.get_http, None)


async def add(client: AsyncClient, ref: str) -> dict[str, Any]:
    response = await client.post("/v1/repos", json={"repo": ref})
    assert response.status_code == 201, response.text
    return dict(response.json())


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("vercel/next.js", ("vercel", "next.js")),
        ("https://github.com/vercel/next.js", ("vercel", "next.js")),
        ("github.com/vercel/next.js.git", ("vercel", "next.js")),
        ("https://www.github.com/astral-sh/uv/tree/main/crates", ("astral-sh", "uv")),
        ("  torvalds/linux/  ", ("torvalds", "linux")),
        ("https://gitlab.com/a/b", None),
        ("just-a-name", None),
        ("-bad/name", None),
        ("owner/..", None),
    ],
)
def test_parse_ref(text: str, expected: tuple[str, str] | None) -> None:
    assert github.parse_ref(text) == expected


async def test_add_repo(ada: AsyncClient, client: AsyncClient, gh: FakeGitHub) -> None:
    gh.add("adapark/lantern", stargazers_count=42, topics=["rust", "cli"], homepage="https://x.dev")
    repo = await add(ada, "https://github.com/AdaPark/lantern")
    assert repo["full_name"] == "adapark/lantern"
    assert repo["url"] == "https://github.com/adapark/lantern"
    assert (repo["stars"], repo["forks"], repo["language"]) == (42, 2, "Python")
    assert repo["topics"] == ["rust", "cli"]
    assert repo["owner"]["username"] == "ada"
    assert repo["missing"] is False

    # Adding it again, however it's written, is a conflict.
    again = await ada.post("/v1/repos", json={"repo": "adapark/lantern"})
    assert again.status_code == 409

    # Anyone can see someone's repos.
    listed = (await client.get("/v1/users/ada/repos")).json()
    assert [r["id"] for r in listed["items"]] == [repo["id"]]
    assert (await client.get(f"/v1/repos/{repo['id']}")).json()["full_name"] == "adapark/lantern"


async def test_add_repo_errors(ada: AsyncClient, client: AsyncClient, gh: FakeGitHub) -> None:
    gh.add("ada/secret", private=True)
    for ref, code in [
        ("not a repo", 400),
        ("ada/nothing-here", 400),
        ("ada/secret", 400),
    ]:
        response = await ada.post("/v1/repos", json={"repo": ref})
        assert response.status_code == code, (ref, response.text)
    # Signed-out people can't add repos.
    assert (await client.post("/v1/repos", json={"repo": "ada/x"})).status_code == 401
    gh.add("ada/fine")
    gh.rate_limited = True
    assert (await ada.post("/v1/repos", json={"repo": "ada/fine"})).status_code == 503


async def test_remove_repo(ada: AsyncClient, ben: AsyncClient, gh: FakeGitHub) -> None:
    gh.add("ada/tool")
    repo = await add(ada, "ada/tool")
    shared = await ada.post("/v1/posts", json={"body_md": "Made this", "repo_id": repo["id"]})
    assert shared.status_code == 201, shared.text
    assert shared.json()["kind"] == "repo"
    assert shared.json()["repo"]["full_name"] == "ada/tool"
    await ada.put(f"/v1/me/pins/repo/{repo['id']}")

    # Only the owner can remove it.
    assert (await ben.delete(f"/v1/repos/{repo['id']}")).status_code == 404
    assert (await ada.delete(f"/v1/repos/{repo['id']}")).status_code == 204
    assert (await ada.get(f"/v1/repos/{repo['id']}")).status_code == 404
    # The post keeps its text; the repo and the pin are gone.
    post = (await ada.get(f"/v1/posts/{shared.json()['id']}")).json()
    assert (post["kind"], post["body_md"], post["repo"]) == ("repo", "Made this", None)
    assert (await ada.get("/v1/users/ada/pins")).json()["items"] == []


async def test_share_rules(ada: AsyncClient, ben: AsyncClient, gh: FakeGitHub) -> None:
    gh.add("ada/tool")
    repo = await add(ada, "ada/tool")
    # Only repos on your own profile.
    theirs = await ben.post("/v1/posts", json={"repo_id": repo["id"]})
    assert theirs.status_code == 400
    # One attachment per post.
    both = await ada.post(
        "/v1/posts",
        json={"repo_id": repo["id"], "achievement": {"type": "shipped", "title": "It"}},
    )
    assert both.status_code == 422


async def test_pins_mix_snippets_and_repos(
    ada: AsyncClient, ben: AsyncClient, client: AsyncClient, gh: FakeGitHub
) -> None:
    gh.add("ada/tool")
    repo = await add(ada, "ada/tool")
    snippet = (
        await ada.post("/v1/snippets", json={"title": "One liner", "content": "print(1)"})
    ).json()
    await ada.put(f"/v1/me/pins/repo/{repo['id']}")
    pins = (await ada.put(f"/v1/me/pins/snippet/{snippet['id']}")).json()["items"]
    assert [p["type"] for p in pins] == ["repo", "snippet"]
    assert pins[0]["repo"]["full_name"] == "ada/tool"
    assert pins[0]["snippet"] is None
    assert pins[1]["snippet"]["title"] == "One liner"
    # You can only pin your own things.
    assert (await ben.put(f"/v1/me/pins/repo/{repo['id']}")).status_code == 404
    seen = (await client.get("/v1/users/ada/pins")).json()["items"]
    assert [p["type"] for p in seen] == ["repo", "snippet"]


async def _age(repo_id: str | None = None, hours: int = 7) -> None:
    async with SessionLocal() as db:
        stmt = update(Repo).values(fetched_at=datetime.now(UTC) - timedelta(hours=hours))
        if repo_id:
            stmt = stmt.where(Repo.id == repo_id)
        await db.execute(stmt)
        await db.commit()


async def _refresh(gh: FakeGitHub) -> int:
    async with SessionLocal() as db, gh.client() as http:
        return await service.refresh_stale(db, http)


async def test_refresh_stale(ada: AsyncClient, gh: FakeGitHub) -> None:
    changed = gh.add("ada/changed")
    same = gh.add("ada/same")
    gone = gh.add("ada/gone")
    gh.add("ada/fresh")
    ids = {r: (await add(ada, f"ada/{r}"))["id"] for r in ("changed", "same", "gone", "fresh")}
    for name in ("changed", "same", "gone"):
        await _age(ids[name])

    changed["stargazers_count"] = 99
    changed["full_name"] = "ada/renamed"
    del gh.repos[gone["id"]]
    gh.requests.clear()
    assert await _refresh(gh) == 3
    # Refreshes go by id, with the ETag from last time; fresh repos are left alone.
    paths = sorted(r.url.path for r in gh.requests)
    assert paths == sorted(f"/repositories/{r['id']}" for r in (changed, same, gone))
    assert all(r.headers.get("if-none-match") for r in gh.requests)

    repos = {r["id"]: r for r in (await ada.get("/v1/users/ada/repos")).json()["items"]}
    assert repos[ids["changed"]]["stars"] == 99
    assert repos[ids["changed"]]["full_name"] == "ada/renamed"
    assert repos[ids["same"]]["stars"] == same["stargazers_count"]
    assert repos[ids["gone"]]["missing"] is True
    # Nothing is stale any more.
    assert await _refresh(gh) == 0


async def test_refresh_stops_when_rate_limited(ada: AsyncClient, gh: FakeGitHub) -> None:
    gh.add("ada/one")
    repo = await add(ada, "ada/one")
    await _age()
    gh.rate_limited = True
    assert await _refresh(gh) == 0
    # Still stale, so the next run tries again.
    gh.rate_limited = False
    assert await _refresh(gh) == 1
    assert (await ada.get(f"/v1/repos/{repo['id']}")).json()["missing"] is False
