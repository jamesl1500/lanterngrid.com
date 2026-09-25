from collections.abc import Callable

from httpx import AsyncClient

from tests.helpers import member


async def test_notifications_page_and_mark_read(new_client: Callable[[], AsyncClient]) -> None:
    star = new_client()
    await member(star, "star")
    for name in ("amy", "bob", "cal"):
        fan = new_client()
        await member(fan, name)
        await fan.post("/v1/friend-requests", json={"username": "star"})

    first = (await star.get("/v1/me/notifications?limit=2")).json()
    assert [n["actor"]["username"] for n in first["items"]] == ["cal", "bob"]
    assert all(not n["read"] for n in first["items"])
    rest = (await star.get(f"/v1/me/notifications?cursor={first['next_cursor']}")).json()
    assert [n["actor"]["username"] for n in rest["items"]] == ["amy"]
    assert rest["next_cursor"] is None

    # Marking up to the newest one seen leaves anything newer unread.
    newest_seen = first["items"][1]["id"]
    response = await star.post("/v1/me/notifications/read", json={"up_to": newest_seen})
    assert response.json() == {"count": 1}
    response = await star.post("/v1/me/notifications/read", json={})
    assert response.json() == {"count": 0}
    assert all(n["read"] for n in (await star.get("/v1/me/notifications")).json()["items"])


async def test_notifications_need_a_session(client: AsyncClient) -> None:
    assert (await client.get("/v1/me/notifications")).status_code == 401
    assert (await client.get("/v1/me/notifications/unread-count")).status_code == 401
