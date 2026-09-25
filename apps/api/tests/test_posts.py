from collections.abc import Callable

import pytest
from httpx import AsyncClient

from tests.helpers import member

NewClient = Callable[[], AsyncClient]


@pytest.fixture
async def ada(new_client: NewClient) -> AsyncClient:
    c = new_client()
    await member(c, "ada", "Ada Park")
    return c


@pytest.fixture
async def ben(new_client: NewClient) -> AsyncClient:
    c = new_client()
    await member(c, "ben", "Ben Okafor")
    return c


@pytest.fixture
async def cy(new_client: NewClient) -> AsyncClient:
    c = new_client()
    await member(c, "cyd", "Cy Doe")
    return c


async def befriend(a: AsyncClient, b: AsyncClient, b_username: str) -> None:
    sent = (await a.post("/v1/friend-requests", json={"username": b_username})).json()
    assert (await b.post(f"/v1/friend-requests/{sent['id']}/accept")).status_code == 200


async def post(client: AsyncClient, body: str, visibility: str = "public") -> dict[str, object]:
    response = await client.post("/v1/posts", json={"body_md": body, "visibility": visibility})
    assert response.status_code == 201, response.text
    return dict(response.json())


def bodies(page: dict[str, list[dict[str, str]]]) -> list[str]:
    return [p["body_md"] for p in page["items"]]


async def test_create_post_with_tags_mentions_and_code(ada: AsyncClient, ben: AsyncClient) -> None:
    body = (
        "Shipped the planner rewrite in #Rust with @ben. #postgres\n\n"
        "```rust\n// #not-a-tag @not_a_mention\nfn main() {}\n```"
    )
    created = await post(ada, f"  {body}  ")
    assert created["body_md"] == body  # trimmed
    assert created["kind"] == "update"
    assert created["author"]["username"] == "ada"  # type: ignore[index]
    assert [t["slug"] for t in created["tags"]] == ["postgres", "rust"]  # type: ignore[attr-defined]
    assert created["mentions"] == ["ben"]
    assert created["edited_at"] is None

    notes = (await ben.get("/v1/me/notifications")).json()["items"]
    assert [(n["kind"], n["actor"]["username"], n["subject_id"]) for n in notes] == [
        ("mention", "ada", created["id"])
    ]
    fetched = await ben.get(f"/v1/posts/{created['id']}")
    assert fetched.json() == created


async def test_post_validation(ada: AsyncClient, client: AsyncClient) -> None:
    assert (await ada.post("/v1/posts", json={"body_md": "   "})).status_code == 422
    too_long = {"body_md": "x" * 5001}
    assert (await ada.post("/v1/posts", json=too_long)).status_code == 422
    weird = {"body_md": "hi", "visibility": "secret"}
    assert (await ada.post("/v1/posts", json=weird)).status_code == 422
    assert (await client.post("/v1/posts", json={"body_md": "hi"})).status_code == 401


async def test_feed_is_you_and_your_friends_newest_first(
    ada: AsyncClient, ben: AsyncClient, cy: AsyncClient
) -> None:
    await befriend(ada, ben, "ben")
    await post(ada, "ada one")
    await post(ben, "ben one", "friends")
    await post(cy, "cy one")  # not a friend
    await post(ada, "ada two")

    assert bodies((await ada.get("/v1/feed")).json()) == ["ada two", "ben one", "ada one"]
    assert bodies((await cy.get("/v1/feed")).json()) == ["cy one"]

    first = (await ada.get("/v1/feed?limit=2")).json()
    assert bodies(first) == ["ada two", "ben one"]
    rest = (await ada.get(f"/v1/feed?limit=2&cursor={first['next_cursor']}")).json()
    assert bodies(rest) == ["ada one"]
    assert rest["next_cursor"] is None


async def test_friends_only_posts_stay_with_friends(
    ada: AsyncClient, ben: AsyncClient, cy: AsyncClient, client: AsyncClient
) -> None:
    await befriend(ada, ben, "ben")
    secret = await post(ada, "friends only #rust", "friends")
    await post(ada, "hello world #rust")

    assert (await ben.get(f"/v1/posts/{secret['id']}")).status_code == 200
    assert (await cy.get(f"/v1/posts/{secret['id']}")).status_code == 404
    assert (await client.get(f"/v1/posts/{secret['id']}")).status_code == 404

    assert bodies((await cy.get("/v1/users/ada/posts")).json()) == ["hello world #rust"]
    assert bodies((await ben.get("/v1/users/ada/posts")).json()) == [
        "hello world #rust",
        "friends only #rust",
    ]
    # Explore is public posts only, even for friends.
    assert bodies((await ben.get("/v1/explore")).json()) == ["hello world #rust"]
    assert bodies((await client.get("/v1/explore")).json()) == ["hello world #rust"]
    # Tag pages follow the same rules.
    assert bodies((await client.get("/v1/tags/rust/posts")).json()) == ["hello world #rust"]
    assert len((await ben.get("/v1/tags/rust/posts")).json()["items"]) == 2
    assert (await client.get("/v1/tags/nope/posts")).status_code == 404


async def test_mentions_only_notify_people_who_can_see_the_post(
    ada: AsyncClient, ben: AsyncClient, cy: AsyncClient
) -> None:
    await befriend(ada, ben, "ben")
    created = await post(ada, "hey @ben and @cyd and @nobody", "friends")
    assert created["mentions"] == ["ben"]
    assert len((await ben.get("/v1/me/notifications")).json()["items"]) == 2  # accept + mention
    assert (await cy.get("/v1/me/notifications")).json()["items"] == []


async def test_blocked_people_see_nothing(ada: AsyncClient, ben: AsyncClient) -> None:
    public = await post(ada, "public post")
    await ben.put("/v1/me/blocks/ada")
    assert (await ada.get(f"/v1/posts/{public['id']}")).status_code == 200  # own post
    assert (await ben.get(f"/v1/posts/{public['id']}")).status_code == 404
    assert (await ben.get("/v1/explore")).json()["items"] == []
    assert (await ada.get("/v1/users/ben/posts")).status_code == 404


async def test_edit_and_delete(ada: AsyncClient, ben: AsyncClient, cy: AsyncClient) -> None:
    created = await post(ada, "first draft #go")
    post_id = created["id"]
    assert (await ben.patch(f"/v1/posts/{post_id}", json={"body_md": "hijack"})).status_code == 404

    edited = await ada.patch(
        f"/v1/posts/{post_id}", json={"body_md": "second draft #rust cc @ben @cyd"}
    )
    assert edited.status_code == 200
    body = edited.json()
    assert body["edited_at"] is not None
    assert [t["slug"] for t in body["tags"]] == ["rust"]
    assert sorted(body["mentions"]) == ["ben", "cyd"]
    # Editing again doesn't notify the same people twice.
    await ada.patch(f"/v1/posts/{post_id}", json={"body_md": "third draft cc @ben @cyd"})
    assert len((await ben.get("/v1/me/notifications")).json()["items"]) == 1

    visibility_only = await ada.patch(f"/v1/posts/{post_id}", json={"visibility": "friends"})
    assert visibility_only.json()["body_md"] == "third draft cc @ben @cyd"
    assert visibility_only.json()["mentions"] == []  # neither is Ada's friend

    assert (await ben.delete(f"/v1/posts/{post_id}")).status_code == 404
    assert (await ada.delete(f"/v1/posts/{post_id}")).status_code == 204
    assert (await ada.get(f"/v1/posts/{post_id}")).status_code == 404
    assert (await ada.get("/v1/feed")).json()["items"] == []
    assert (await ben.get("/v1/me/notifications")).json()["items"] == []  # withdrawn


async def test_get_tag(client: AsyncClient) -> None:
    response = await client.get("/v1/tags/TypeScript")
    assert response.json() == {"slug": "typescript", "name": "TypeScript", "kind": "language"}
    assert (await client.get("/v1/tags/suggest?q=typ")).status_code == 200
    assert (await client.get("/v1/tags/definitely-not-a-tag")).status_code == 404
