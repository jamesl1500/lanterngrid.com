import uuid
from collections.abc import Callable
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import update

from app.core.db import SessionLocal
from app.modules.users.models import User
from tests.helpers import PASSWORD, befriend, member, post


async def make_moderator(username: str) -> None:
    async with SessionLocal() as db:
        await db.execute(update(User).where(User.username == username).values(is_moderator=True))
        await db.commit()


@pytest.fixture
async def mo(new_client: Callable[[], AsyncClient]) -> AsyncClient:
    """A moderator, on their own client."""
    c = new_client()
    await member(c, "moira", "Moira Reyes")
    await make_moderator("moira")
    return c


async def report(
    client: AsyncClient, kind: str, subject_id: object, reason: str = "spam", **extra: Any
) -> int:
    response = await client.post(
        "/v1/reports",
        json={"subject_kind": kind, "subject_id": str(subject_id), "reason": reason, **extra},
    )
    return response.status_code


async def cases(client: AsyncClient, status: str = "open") -> list[dict[str, Any]]:
    response = await client.get("/v1/moderation/cases", params={"status": status})
    assert response.status_code == 200, response.text
    return list(response.json()["items"])


async def resolve(client: AsyncClient, case_id: str, action: str, note: str | None = None) -> Any:
    return await client.post(
        f"/v1/moderation/cases/{case_id}/resolve", json={"action": action, "note": note}
    )


async def user_id(client: AsyncClient, username: str) -> str:
    return str((await client.get(f"/v1/users/{username}")).json()["id"])


async def test_reports_share_one_case(
    ada: AsyncClient, ben: AsyncClient, cy: AsyncClient, mo: AsyncClient
) -> None:
    spam = await post(ada, "Buy followers at example.com")
    assert await report(ben, "post", spam["id"], details="  it's an ad  ") == 204
    assert await report(cy, "post", spam["id"], "harassment") == 204
    # Reporting again changes nothing.
    assert await report(ben, "post", spam["id"], "hate") == 204

    [case] = await cases(mo)
    assert case["subject_kind"] == "post"
    assert case["subject_author"]["username"] == "ada"
    assert case["snapshot"] == "Buy followers at example.com"
    assert case["report_count"] == 2
    assert [(r["reporter"]["username"], r["reason"]) for r in case["reports"]] == [
        ("cyd", "harassment"),
        ("ben", "spam"),
    ]
    assert case["reports"][1]["details"] == "it's an ad"
    assert (await mo.get("/v1/moderation/summary")).json() == {"open_cases": 1}

    # Editing the post afterwards doesn't change what moderators see.
    await ada.patch(f"/v1/posts/{spam['id']}", json={"body_md": "Nothing to see"})
    assert (await cases(mo))[0]["snapshot"] == "Buy followers at example.com"


async def test_what_can_be_reported(ada: AsyncClient, ben: AsyncClient, cy: AsyncClient) -> None:
    mine = await post(ada, "My own post")
    assert await report(ada, "post", mine["id"]) == 400
    assert await report(ada, "user", await user_id(ada, "ada")) == 400
    # Only things you can see.
    hidden = await post(ben, "Friends only", visibility="friends")
    assert await report(cy, "post", hidden["id"]) == 404
    assert await report(cy, "comment", uuid.uuid4()) == 404
    # "Other" needs a word about what's wrong.
    assert await report(cy, "post", mine["id"], "other") == 422
    assert await report(cy, "post", mine["id"], "other", details="Off-topic crypto pitch") == 204
    # People can be reported too.
    assert await report(cy, "user", await user_id(cy, "ben"), "impersonation") == 204


async def test_only_moderators_see_the_queue(ada: AsyncClient, mo: AsyncClient) -> None:
    assert (await ada.get("/v1/moderation/cases")).status_code == 403
    assert (await ada.get("/v1/moderation/summary")).status_code == 403
    assert (await resolve(ada, str(uuid.uuid4()), "dismiss")).status_code == 403
    assert (await ada.get("/v1/auth/me")).json()["is_moderator"] is False
    assert (await mo.get("/v1/auth/me")).json()["is_moderator"] is True


async def test_dismiss_and_remove(
    ada: AsyncClient, ben: AsyncClient, cy: AsyncClient, mo: AsyncClient
) -> None:
    fine = await post(ada, "A perfectly fine post")
    await report(ben, "post", fine["id"])
    [case] = await cases(mo)
    dismissed = await resolve(mo, case["id"], "dismiss", "Not spam")
    assert dismissed.status_code == 200, dismissed.text
    assert dismissed.json()["status"] == "dismissed"
    assert dismissed.json()["resolved_by"]["username"] == "moira"
    assert await cases(mo) == []
    [closed] = await cases(mo, "closed")
    assert (closed["status"], closed["note"]) == ("dismissed", "Not spam")
    # A closed case can't be decided twice.
    assert (await resolve(mo, case["id"], "remove")).status_code == 409
    # Reporting it again opens a new case.
    await report(cy, "post", fine["id"])
    [again] = await cases(mo)
    assert again["id"] != case["id"]

    removed = await resolve(mo, again["id"], "remove")
    assert removed.json()["status"] == "removed"
    assert removed.json()["subject_gone"] is True
    assert (await ben.get(f"/v1/posts/{fine['id']}")).status_code == 404


async def test_removing_comments_snippets_and_messages(
    ada: AsyncClient, ben: AsyncClient, mo: AsyncClient
) -> None:
    await befriend(ada, ben, "ben")
    target = await post(ben, "Ship it")
    comment = (
        await ada.post(f"/v1/posts/{target['id']}/comments", json={"body_md": "Rude comment"})
    ).json()
    snippet = (
        await ada.post(
            "/v1/snippets",
            json={"title": "Miner", "language": "python", "content": "mine()"},
        )
    ).json()
    dm = (await ada.post("/v1/conversations", json={"usernames": ["ben"]})).json()
    message = (
        await ada.post(
            f"/v1/conversations/{dm['id']}/messages",
            json={"body": "Nasty message", "client_id": "m1"},
        )
    ).json()
    await report(ben, "comment", comment["id"], "harassment")
    await report(ben, "snippet", snippet["id"])
    await report(ben, "message", message["id"], "harassment")

    queue = {c["subject_kind"]: c for c in await cases(mo)}
    assert queue["comment"]["post_id"] == target["id"]
    assert queue["snippet"]["snapshot"] == "Miner\n\nmine()"
    assert queue["message"]["snapshot"] == "Nasty message"
    for case in queue.values():
        assert (await resolve(mo, case["id"], "remove")).status_code == 200

    comments = (await ben.get(f"/v1/posts/{target['id']}/comments")).json()["items"]
    assert comments == []
    assert (await ben.get(f"/v1/snippets/{snippet['id']}")).status_code == 404
    # A removed message keeps its place in the chat, without its text.
    [shown] = (await ben.get(f"/v1/conversations/{dm['id']}/messages")).json()["items"]
    assert (shown["id"], shown["body"], shown["removed"]) == (message["id"], "", True)
    # It can't be reported again.
    assert await report(ben, "message", message["id"]) == 404


async def test_people_outside_a_conversation_cant_report_its_messages(
    ada: AsyncClient, ben: AsyncClient, cy: AsyncClient
) -> None:
    await befriend(ada, ben, "ben")
    dm = (await ada.post("/v1/conversations", json={"usernames": ["ben"]})).json()
    message = (
        await ada.post(
            f"/v1/conversations/{dm['id']}/messages", json={"body": "hi", "client_id": "m1"}
        )
    ).json()
    assert await report(cy, "message", message["id"]) == 404


async def test_suspending_an_account(
    ada: AsyncClient,
    ben: AsyncClient,
    cy: AsyncClient,
    mo: AsyncClient,
    client: AsyncClient,
) -> None:
    await befriend(ada, cy, "cyd")
    spam = await post(cy, "Spam spam spam")
    other = await post(cy, "More spam")
    on_ada = await post(ada, "Ada's post")
    await cy.post(f"/v1/posts/{on_ada['id']}/comments", json={"body_md": "Spammy comment"})
    await report(ada, "post", spam["id"])
    await report(ben, "post", other["id"])
    await report(ben, "user", await user_id(ben, "cyd"))
    unrelated = await post(ben, "Ben's post")
    await report(ada, "post", unrelated["id"])
    assert len(await cases(mo)) == 4

    first = next(c for c in await cases(mo) if c["subject_id"] == spam["id"])
    suspended = await resolve(mo, first["id"], "suspend", "Spam account")
    assert suspended.status_code == 200, suspended.text
    assert suspended.json()["author_suspended"] is True
    # Their other cases close with them; Ben's stays open.
    [still_open] = await cases(mo)
    assert still_open["subject_id"] == unrelated["id"]
    closed = await cases(mo, "closed")
    assert {c["status"] for c in closed} == {"suspended"}
    assert {c["note"] for c in closed} == {"Spam account"}

    # Signed out everywhere, and can't sign back in.
    assert (await cy.get("/v1/auth/me")).status_code == 401
    signin = await client.post(
        "/v1/auth/signin", json={"email": "cyd@example.com", "password": PASSWORD}
    )
    assert signin.status_code == 403
    # Their profile, posts and comments are hidden from everyone.
    assert (await ada.get("/v1/users/cyd")).status_code == 404
    assert (await client.get(f"/v1/posts/{spam['id']}")).status_code == 404
    feed = (await ada.get("/v1/feed")).json()["items"]
    assert [p["body_md"] for p in feed] == ["Ada's post"]
    explore = (await client.get("/v1/explore")).json()["items"]
    assert "cyd" not in {p["author"]["username"] for p in explore}
    assert (await ada.get(f"/v1/posts/{on_ada['id']}/comments")).json()["items"] == []
    assert (await ada.get("/v1/people/search", params={"q": "cy"})).json() == []
    assert (await ada.get("/v1/users/ada/friends")).json()["items"] == []

    # Lifting it brings everything back once they sign in again.
    cy_id = closed[0]["subject_author"]["id"]
    assert (await mo.delete(f"/v1/moderation/suspensions/{cy_id}")).status_code == 204
    signin = await client.post(
        "/v1/auth/signin", json={"email": "cyd@example.com", "password": PASSWORD}
    )
    assert signin.status_code == 200
    assert (await ada.get("/v1/users/cyd")).status_code == 200
    assert len((await ada.get("/v1/feed")).json()["items"]) == 3


async def test_moderators_cant_be_suspended(
    ada: AsyncClient, mo: AsyncClient, new_client: Callable[[], AsyncClient]
) -> None:
    other = new_client()
    await member(other, "milo")
    await make_moderator("milo")
    await report(ada, "user", await user_id(ada, "milo"))
    [case] = await cases(mo)
    refused = await resolve(mo, case["id"], "suspend")
    assert refused.status_code == 400
    assert "Moderators can't be suspended" in refused.json()["detail"]
    # People can't be "removed", only suspended.
    assert (await resolve(mo, case["id"], "remove")).status_code == 400
    assert (await cases(mo))[0]["status"] == "open"


async def test_unverified_accounts_get_tighter_limits(
    new_client: Callable[[], AsyncClient],
) -> None:
    fresh = new_client()
    await member(fresh, "fresh", verified=False)
    for n in range(5):
        await post(fresh, f"Post {n}")
    limited = await fresh.post("/v1/posts", json={"body_md": "One more", "visibility": "public"})
    assert limited.status_code == 429
    assert "Verify your email" in limited.json()["detail"]
    assert 0 < int(limited.headers["retry-after"]) <= 3600


async def test_searching_is_rate_limited(client: AsyncClient) -> None:
    for _ in range(60):
        assert (await client.get("/v1/search/posts", params={"q": "queue"})).status_code == 200
    limited = await client.get("/v1/search/posts", params={"q": "queue"})
    assert limited.status_code == 429
    assert "retry-after" in limited.headers
