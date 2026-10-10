import uuid
from contextlib import AbstractAsyncContextManager
from typing import Any

from httpx import AsyncClient
from httpx_ws import AsyncWebSocketSession, WebSocketDisconnect, aconnect_ws
from httpx_ws.transport import ASGIWebSocketTransport

from app.main import app
from tests.helpers import befriend


async def start(client: AsyncClient, *usernames: str, title: str | None = None) -> dict[str, Any]:
    response = await client.post(
        "/v1/conversations", json={"usernames": list(usernames), "title": title}
    )
    assert response.status_code == 201, response.text
    return dict(response.json())


async def send(client: AsyncClient, conversation_id: str, body: str) -> dict[str, Any]:
    response = await client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"body": body, "client_id": str(uuid.uuid4())},
    )
    assert response.status_code == 201, response.text
    return dict(response.json())


async def share(client: AsyncClient, conversation_id: str, snippet_id: str, body: str = "") -> Any:
    return await client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"body": body, "client_id": str(uuid.uuid4()), "snippet_id": snippet_id},
    )


async def unread(client: AsyncClient) -> int:
    return int((await client.get("/v1/conversations/unread-count")).json()["conversations"])


async def test_dm_needs_friends(ada: AsyncClient, ben: AsyncClient) -> None:
    stranger = await ada.post("/v1/conversations", json={"usernames": ["ben"]})
    assert stranger.status_code == 403
    nobody = await ada.post("/v1/conversations", json={"usernames": ["nobody"]})
    assert nobody.status_code == 400
    assert "@nobody" in nobody.json()["detail"]

    await befriend(ada, ben, "ben")
    dm = await start(ada, "ben")
    assert dm["kind"] == "dm"
    assert sorted(m["user"]["username"] for m in dm["members"]) == ["ada", "ben"]
    # Either person starting it again gets the same DM.
    assert (await start(ben, "@Ada"))["id"] == dm["id"]
    assert [c["id"] for c in (await ben.get("/v1/conversations")).json()["items"]] == [dm["id"]]


async def test_messages_and_unread(ada: AsyncClient, ben: AsyncClient, cy: AsyncClient) -> None:
    await befriend(ada, ben, "ben")
    dm = await start(ada, "ben")
    path = f"/v1/conversations/{dm['id']}"

    first = await send(ada, dm["id"], "  hi ben  ")
    assert first["body"] == "hi ben"
    assert first["sender"]["username"] == "ada"
    # A retry with the same client_id returns the first message.
    retry = await ada.post(
        f"{path}/messages", json={"body": "hi ben", "client_id": first["client_id"]}
    )
    assert retry.status_code == 201
    assert retry.json()["id"] == first["id"]
    second = await send(ben, dm["id"], "hey!")
    third = await send(ada, dm["id"], "lunch?")

    page = (await ben.get(f"{path}/messages")).json()
    assert [m["body"] for m in page["items"]] == ["hi ben", "hey!", "lunch?"]
    assert page["older_cursor"] is None
    # Paging up, and catching up after a reconnect.
    older = (await ben.get(f"{path}/messages", params={"limit": 2})).json()
    assert [m["body"] for m in older["items"]] == ["hey!", "lunch?"]
    assert older["older_cursor"] == second["id"]
    before = (await ben.get(f"{path}/messages", params={"before": second["id"]})).json()
    assert [m["body"] for m in before["items"]] == ["hi ben"]
    after = (await ben.get(f"{path}/messages", params={"after": first["id"]})).json()
    assert [m["body"] for m in after["items"]] == ["hey!", "lunch?"]

    # Ben read "hey!" by sending it, so only "lunch?" is new; Ada has read everything.
    inbox = (await ben.get("/v1/conversations")).json()["items"]
    assert inbox[0]["unread_count"] == 1
    assert inbox[0]["last_message"]["body"] == "lunch?"
    assert (await unread(ben), await unread(ada)) == (1, 0)
    assert (await ben.post(f"{path}/read", json={"message_id": third["id"]})).status_code == 204
    assert await unread(ben) == 0
    # The read marker never moves back.
    await ben.post(f"{path}/read", json={"message_id": first["id"]})
    members = {m["user"]["username"]: m for m in (await ada.get(path)).json()["members"]}
    assert members["ben"]["last_read_message_id"] == third["id"]

    # Outsiders can't see or post.
    assert (await cy.get(path)).status_code == 404
    assert (await cy.get(f"{path}/messages")).status_code == 404
    outsider = await cy.post(f"{path}/messages", json={"body": "hi", "client_id": "x"})
    assert outsider.status_code == 404


async def test_dm_closes_when_unfriended(ada: AsyncClient, ben: AsyncClient) -> None:
    await befriend(ada, ben, "ben")
    dm = await start(ada, "ben")
    await send(ada, dm["id"], "bye")
    assert (await ada.delete("/v1/me/friends/ben")).status_code == 204
    gone = await ben.post(
        f"/v1/conversations/{dm['id']}/messages", json={"body": "wait", "client_id": "1"}
    )
    assert gone.status_code == 403
    # The history is still there.
    messages = (await ben.get(f"/v1/conversations/{dm['id']}/messages")).json()["items"]
    assert [m["body"] for m in messages] == ["bye"]


async def test_groups(ada: AsyncClient, ben: AsyncClient, cy: AsyncClient) -> None:
    await befriend(ada, ben, "ben")
    await befriend(ada, cy, "cyd")
    group = await start(ada, "ben", title="Launch crew")
    assert (group["kind"], group["title"]) == ("group", "Launch crew")
    roles = {m["user"]["username"]: m["role"] for m in group["members"]}
    assert roles == {"ada": "owner", "ben": "member"}

    path = f"/v1/conversations/{group['id']}"
    # Only the owner adds people, and only their friends.
    assert (await ben.post(f"{path}/members", json={"usernames": ["cyd"]})).status_code == 403
    added = await ada.post(f"{path}/members", json={"usernames": ["cyd"]})
    assert added.status_code == 200
    assert len(added.json()["members"]) == 3
    await send(cy, group["id"], "hello all")
    assert await unread(ben) == 1

    # A DM can't be left; a group can, and the owner role moves on.
    assert (await ada.delete(f"{path}/members/me")).status_code == 204
    assert (await ada.get(path)).status_code == 404
    roles = {m["user"]["username"]: m["role"] for m in (await ben.get(path)).json()["members"]}
    assert roles == {"ben": "owner", "cyd": "member"}
    dm = await start(ada, "ben")
    assert (await ada.delete(f"/v1/conversations/{dm['id']}/members/me")).status_code == 400


async def test_sharing_snippets(ada: AsyncClient, ben: AsyncClient, cy: AsyncClient) -> None:
    await befriend(ada, ben, "ben")
    await befriend(ben, cy, "cyd")
    snippet = {"title": "Retry loop", "language": "python", "content": "while True:\n    pass"}
    mine = (await ada.post("/v1/snippets", json={**snippet, "visibility": "friends"})).json()
    group = await start(ben, "ada", "cyd")
    path = f"/v1/conversations/{group['id']}/messages"

    # A snippet on its own is a message; cy sees it in the group though ada isn't her friend.
    response = await share(ada, group["id"], mine["id"])
    assert response.status_code == 201, response.text
    assert response.json()["body"] == ""
    seen = (await cy.get(path)).json()["items"][-1]
    assert seen["snippet"]["title"] == "Retry loop"
    # Others' friends-only snippets stay theirs to share; public ones are fair game.
    assert (await share(ben, group["id"], mine["id"])).status_code == 400
    public = (await ada.post("/v1/snippets", json={**snippet, "title": "Open"})).json()
    assert (await share(ben, group["id"], public["id"], "look")).status_code == 201
    assert (await share(ben, group["id"], str(uuid.uuid4()))).status_code == 400
    # Nothing to send.
    empty = await ben.post(path, json={"body": "  ", "client_id": "x"})
    assert empty.status_code == 422
    # Deleting the snippet empties the card but keeps the message.
    assert (await ada.delete(f"/v1/snippets/{mine['id']}")).status_code == 204
    first = (await cy.get(path)).json()["items"][0]
    assert first["snippet_id"] == mine["id"]
    assert first["snippet"] is None


def connect(
    url: str, client: AsyncClient, **kwargs: Any
) -> AbstractAsyncContextManager[AsyncWebSocketSession]:
    return aconnect_ws(url, client, **kwargs)


def ws_client() -> AsyncClient:
    # Made inside each test: the transport's task group must close in the task that opened it.
    return AsyncClient(transport=ASGIWebSocketTransport(app=app), base_url="http://testserver")


async def ticket_for(client: AsyncClient) -> str:
    response = await client.post("/v1/realtime/ticket")
    assert response.status_code == 200, response.text
    assert response.json()["url"].endswith("/v1/realtime")
    return str(response.json()["ticket"])


async def test_socket_pushes_messages_and_reads(ada: AsyncClient, ben: AsyncClient) -> None:
    await befriend(ada, ben, "ben")
    dm = await start(ada, "ben")
    ticket = await ticket_for(ben)
    async with ws_client() as c, connect(f"/v1/realtime?ticket={ticket}", c) as ws:
        assert (await ws.receive_json(timeout=2))["type"] == "ready"
        await ws.send_json({"type": "ping"})
        assert (await ws.receive_json(timeout=2))["type"] == "pong"

        sent = await send(ada, dm["id"], "live?")
        event = await ws.receive_json(timeout=2)
        assert event["type"] == "message.created"
        assert event["message"]["id"] == sent["id"]
        assert event["message"]["sender"]["username"] == "ada"

        await ben.post(f"/v1/conversations/{dm['id']}/read", json={"message_id": sent["id"]})
        event = await ws.receive_json(timeout=2)
        assert event["type"] == "conversation.read"
        assert event["message_id"] == sent["id"]


async def close_code(url: str, **kwargs: Any) -> int | None:
    """The code the server closed with before accepting, or None if it accepted."""
    codes: list[int] = []
    try:
        async with ws_client() as c, connect(url, c, **kwargs) as ws:
            await ws.receive_json(timeout=2)
    except* WebSocketDisconnect as group:
        codes = [e.code for e in group.exceptions if isinstance(e, WebSocketDisconnect)]
    return codes[0] if codes else None


async def test_socket_needs_a_fresh_ticket(ada: AsyncClient) -> None:
    assert await close_code("/v1/realtime") == 4401
    assert await close_code("/v1/realtime?ticket=made-up") == 4401
    ticket = await ticket_for(ada)
    async with ws_client() as c, connect(f"/v1/realtime?ticket={ticket}", c) as ws:
        assert (await ws.receive_json(timeout=2))["type"] == "ready"
    # Tickets work once.
    assert await close_code(f"/v1/realtime?ticket={ticket}") == 4401
    # Another site's page can't open one.
    other = await ticket_for(ada)
    evil = {"origin": "https://evil.test"}
    assert await close_code(f"/v1/realtime?ticket={other}", headers=evil) == 4403


async def test_socket_typing(ada: AsyncClient, ben: AsyncClient, cy: AsyncClient) -> None:
    await befriend(ada, ben, "ben")
    dm = await start(ada, "ben")
    async with (
        ws_client() as c,
        connect(f"/v1/realtime?ticket={await ticket_for(ben)}", c) as ben_ws,
        connect(f"/v1/realtime?ticket={await ticket_for(ada)}", c) as ada_ws,
        connect(f"/v1/realtime?ticket={await ticket_for(cy)}", c) as cy_ws,
    ):
        for ws in (ben_ws, ada_ws, cy_ws):
            assert (await ws.receive_json(timeout=2))["type"] == "ready"
        # Someone outside the conversation is ignored, and so is junk.
        await cy_ws.send_json({"type": "typing", "conversation_id": dm["id"]})
        await cy_ws.send_text("not json")
        await cy_ws.send_json({"type": "typing", "conversation_id": "nope"})
        await ada_ws.send_json({"type": "typing", "conversation_id": dm["id"]})
        event = await ben_ws.receive_json(timeout=2)
        assert event["type"] == "conversation.typing"
        assert event["conversation_id"] == dm["id"]
        assert event["user_id"] == (await ada.get("/v1/auth/me")).json()["id"]


async def test_socket_notifications(ada: AsyncClient, ben: AsyncClient) -> None:
    async with ws_client() as c, connect(f"/v1/realtime?ticket={await ticket_for(ben)}", c) as ws:
        assert (await ws.receive_json(timeout=2))["type"] == "ready"
        await ada.post("/v1/friend-requests", json={"username": "ben"})
        event = await ws.receive_json(timeout=2)
        assert event == {"type": "notification.created", "kind": "friend_request"}
        await ben.post("/v1/me/notifications/read", json={})
        assert (await ws.receive_json(timeout=2))["type"] == "notifications.read"
