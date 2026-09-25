from httpx import AsyncClient

from tests.helpers import befriend, post


async def test_react_and_unreact(ada: AsyncClient, ben: AsyncClient, client: AsyncClient) -> None:
    created = await post(ada, "Shipped it")
    url = f"/v1/posts/{created['id']}/reactions"
    assert created["reactions"] == []

    assert (await ben.put(f"{url}/ship")).status_code == 200
    assert (await ben.put(f"{url}/ship")).status_code == 200  # idempotent
    assert (await ben.put(f"{url}/like")).status_code == 200
    mine = (await ada.put(f"{url}/ship")).json()["reactions"]
    # In the fixed order, with counts and whether the viewer used each.
    assert mine == [
        {"kind": "like", "count": 1, "mine": False},
        {"kind": "ship", "count": 2, "mine": True},
    ]

    seen_by_ben = (await ben.get(f"/v1/posts/{created['id']}")).json()["reactions"]
    assert seen_by_ben == [
        {"kind": "like", "count": 1, "mine": True},
        {"kind": "ship", "count": 2, "mine": True},
    ]
    signed_out = (await client.get("/v1/explore")).json()["items"][0]["reactions"]
    assert [r["mine"] for r in signed_out] == [False, False]

    after = (await ben.delete(f"{url}/like")).json()["reactions"]
    assert after == [{"kind": "ship", "count": 2, "mine": True}]
    assert (await ben.delete(f"{url}/like")).status_code == 200  # idempotent


async def test_reactions_need_a_visible_post_and_a_known_kind(
    ada: AsyncClient, ben: AsyncClient, client: AsyncClient
) -> None:
    private = await post(ada, "Friends only", "friends")
    url = f"/v1/posts/{private['id']}/reactions"
    assert (await ben.put(f"{url}/like")).status_code == 404
    assert (await client.put(f"{url}/like")).status_code == 401
    await befriend(ada, ben, "ben")
    assert (await ben.put(f"{url}/like")).status_code == 200
    assert (await ben.put(f"{url}/party")).status_code == 422
