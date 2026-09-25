from collections.abc import Callable

import pytest
from httpx import AsyncClient

from tests.helpers import member, sign_up

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


async def relationship(client: AsyncClient, username: str) -> dict[str, object]:
    response = await client.get(f"/v1/users/{username}")
    assert response.status_code == 200, response.text
    return dict(response.json()["relationship"])


async def request_friend(client: AsyncClient, username: str) -> dict[str, object]:
    response = await client.post("/v1/friend-requests", json={"username": username})
    assert response.status_code == 200, response.text
    return dict(response.json())


async def test_request_accept_and_unfriend(ada: AsyncClient, ben: AsyncClient) -> None:
    sent = await request_friend(ada, "ben")
    assert sent["status"] == "pending"
    assert sent["user"]["username"] == "ben"  # type: ignore[index]
    assert await relationship(ada, "ben") == {"status": "request_sent", "request_id": sent["id"]}
    assert await relationship(ben, "ada") == {
        "status": "request_received",
        "request_id": sent["id"],
    }

    # Ben is told, and sees it in his incoming list; Ada sees it in her outgoing list.
    notes = (await ben.get("/v1/me/notifications")).json()["items"]
    assert [(n["kind"], n["actor"]["username"]) for n in notes] == [("friend_request", "ada")]
    assert (await ben.get("/v1/me/notifications/unread-count")).json() == {"count": 1}
    incoming = (await ben.get("/v1/me/friend-requests")).json()["items"]
    assert [r["user"]["username"] for r in incoming] == ["ada"]
    outgoing = (await ada.get("/v1/me/friend-requests?direction=outgoing")).json()["items"]
    assert [r["user"]["username"] for r in outgoing] == ["ben"]

    accepted = await ben.post(f"/v1/friend-requests/{sent['id']}/accept")
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"
    assert (await ben.get("/v1/me/notifications/unread-count")).json() == {"count": 0}
    notes = (await ada.get("/v1/me/notifications")).json()["items"]
    assert [(n["kind"], n["actor"]["username"]) for n in notes] == [("friend_accepted", "ben")]

    for viewer, other in ((ada, "ben"), (ben, "ada")):
        profile = (await viewer.get(f"/v1/users/{other}")).json()
        assert profile["relationship"] == {"status": "friends", "request_id": None}
        assert profile["friend_count"] == 1
    friends = (await ada.get("/v1/users/ben/friends")).json()
    assert [f["username"] for f in friends["items"]] == ["ada"]
    assert (await ben.get("/v1/me/friend-requests")).json()["items"] == []

    again = await ada.post("/v1/friend-requests", json={"username": "ben"})
    assert again.status_code == 409

    assert (await ada.delete("/v1/me/friends/ben")).status_code == 204
    assert (await relationship(ada, "ben"))["status"] == "none"
    assert (await ada.delete("/v1/me/friends/ben")).status_code == 404


async def test_asking_someone_who_already_asked_you_accepts(
    ada: AsyncClient, ben: AsyncClient
) -> None:
    sent = await request_friend(ada, "ben")
    assert (await request_friend(ada, "ben"))["id"] == sent["id"]  # double click is harmless
    crossed = await request_friend(ben, "ada")
    assert crossed["id"] == sent["id"]
    assert crossed["status"] == "accepted"
    assert (await relationship(ada, "ben"))["status"] == "friends"


async def test_cancel_withdraws_the_notification(ada: AsyncClient, ben: AsyncClient) -> None:
    sent = await request_friend(ada, "ben")
    # Only the sender can cancel, only the recipient can answer.
    assert (await ben.post(f"/v1/friend-requests/{sent['id']}/cancel")).status_code == 404
    assert (await ada.post(f"/v1/friend-requests/{sent['id']}/accept")).status_code == 404

    cancelled = await ada.post(f"/v1/friend-requests/{sent['id']}/cancel")
    assert cancelled.json()["status"] == "cancelled"
    assert (await ben.get("/v1/me/notifications")).json()["items"] == []
    assert (await relationship(ben, "ada"))["status"] == "none"
    assert (await ben.post(f"/v1/friend-requests/{sent['id']}/accept")).status_code == 404


async def test_decline_is_quiet_and_has_a_cooldown(ada: AsyncClient, ben: AsyncClient) -> None:
    sent = await request_friend(ada, "ben")
    declined = await ben.post(f"/v1/friend-requests/{sent['id']}/decline")
    assert declined.json()["status"] == "declined"
    assert (await ada.get("/v1/me/notifications")).json()["items"] == []
    assert (await ben.get("/v1/me/notifications/unread-count")).json() == {"count": 0}

    again = await ada.post("/v1/friend-requests", json={"username": "ben"})
    assert again.status_code == 429
    # Ben can still change his mind.
    assert (await request_friend(ben, "ada"))["status"] == "pending"


async def test_block_ends_everything_and_hides_both_ways(
    ada: AsyncClient, ben: AsyncClient
) -> None:
    sent = await request_friend(ada, "ben")
    await ben.post(f"/v1/friend-requests/{sent['id']}/accept")

    assert (await ben.put("/v1/me/blocks/ada")).status_code == 204
    assert (await relationship(ben, "ada"))["status"] == "blocked"
    assert (await ada.get("/v1/users/ben")).status_code == 404  # Ben vanishes for Ada
    assert (await ada.get("/v1/users/ben/friends")).json()["items"] == []
    refused = await ada.post("/v1/friend-requests", json={"username": "ben"})
    assert refused.status_code == 403
    blocked = (await ben.get("/v1/me/blocks")).json()
    assert [u["username"] for u in blocked] == ["ada"]
    assert (await ada.get("/v1/people/search?q=ben")).json() == []

    assert (await ben.delete("/v1/me/blocks/ada")).status_code == 204
    assert (await relationship(ben, "ada"))["status"] == "none"  # the friendship stays gone
    assert (await ben.put("/v1/me/blocks/ben")).status_code == 400


async def test_block_withdraws_open_requests(ada: AsyncClient, ben: AsyncClient) -> None:
    sent = await request_friend(ada, "ben")
    await ben.put("/v1/me/blocks/ada")
    assert (await ben.get("/v1/me/notifications")).json()["items"] == []
    assert (await ben.post(f"/v1/friend-requests/{sent['id']}/accept")).status_code == 404


async def test_friend_endpoints_need_a_username(client: AsyncClient, ben: AsyncClient) -> None:
    await sign_up(client, email="new@example.com")
    response = await client.post("/v1/friend-requests", json={"username": "ben"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Pick a username first."
    assert (await ben.post("/v1/friend-requests", json={"username": "ben"})).status_code == 403
    missing = await ben.post("/v1/friend-requests", json={"username": "nobody"})
    assert missing.status_code == 404


async def test_friends_list_pages_newest_account_first(new_client: NewClient) -> None:
    hub = new_client()
    await member(hub, "hub")
    for name in ("cyd", "dee", "eli"):
        c = new_client()
        await member(c, name)
        sent = await request_friend(c, "hub")
        await hub.post(f"/v1/friend-requests/{sent['id']}/accept")

    first = (await hub.get("/v1/users/hub/friends?limit=2")).json()
    assert [f["username"] for f in first["items"]] == ["eli", "dee"]
    rest = (await hub.get(f"/v1/users/hub/friends?limit=2&cursor={first['next_cursor']}")).json()
    assert [f["username"] for f in rest["items"]] == ["cyd"]
    assert rest["next_cursor"] is None


async def test_people_search(new_client: NewClient) -> None:
    me = new_client()
    await member(me, "grace", "Grace Hopper")
    for username, name in (("adalove", "Ada Lovelace"), ("ada", "Ada Park"), ("bob", "Robert Ada")):
        await member(new_client(), username, name)

    def names(response_json: list[dict[str, str]]) -> list[str]:
        return [u["username"] for u in response_json]

    results = names((await me.get("/v1/people/search?q=ada")).json())
    assert results[0] == "ada"  # exact username first
    assert set(results) == {"ada", "adalove", "bob"}
    assert names((await me.get("/v1/people/search?q=@adal")).json()) == ["adalove"]
    assert names((await me.get("/v1/people/search?q=lovelace")).json()) == ["adalove"]
    assert (await me.get("/v1/people/search?q=grace")).json() == []  # never yourself
    assert (await me.get("/v1/people/search?q=")).json() == []
