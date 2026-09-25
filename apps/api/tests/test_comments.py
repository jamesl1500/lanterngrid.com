from typing import Any

from httpx import AsyncClient

from tests.helpers import befriend, post


async def comment(client: AsyncClient, post_id: object, body: str) -> dict[str, Any]:
    response = await client.post(f"/v1/posts/{post_id}/comments", json={"body_md": body})
    assert response.status_code == 201, response.text
    return dict(response.json())


async def notes(client: AsyncClient) -> list[dict[str, Any]]:
    return list((await client.get("/v1/me/notifications")).json()["items"])


async def test_comment_notifies_the_author_and_mentions(
    ada: AsyncClient, ben: AsyncClient, cy: AsyncClient, client: AsyncClient
) -> None:
    created = await post(ada, "New planner is out")
    made = await comment(ben, created["id"], "  Nice! @cyd you'll like this. @nobody  ")
    assert made["body_md"] == "Nice! @cyd you'll like this. @nobody"
    assert made["author"]["username"] == "ben"
    assert made["mentions"] == ["cyd"]  # only people who exist

    [to_author] = await notes(ada)
    assert to_author["kind"] == "comment"
    assert to_author["subject_id"] == made["id"]
    assert to_author["post_id"] == created["id"]
    [to_cy] = await notes(cy)
    assert (to_cy["kind"], to_cy["post_id"]) == ("mention", created["id"])

    # Commenting on your own post notifies no one.
    await comment(ada, created["id"], "Thanks!")
    assert len(await notes(ada)) == 1

    page = (await client.get(f"/v1/posts/{created['id']}/comments")).json()
    assert [c["author"]["username"] for c in page["items"]] == ["ben", "ada"]  # oldest first
    assert (await client.get(f"/v1/posts/{created['id']}")).json()["comment_count"] == 2


async def test_comment_paging(ada: AsyncClient) -> None:
    created = await post(ada, "Count with me")
    for n in range(5):
        await comment(ada, created["id"], str(n))
    url = f"/v1/posts/{created['id']}/comments"
    first = (await ada.get(url, params={"limit": 3})).json()
    second = (await ada.get(url, params={"limit": 3, "cursor": first["next_cursor"]})).json()
    assert [c["body_md"] for c in first["items"] + second["items"]] == ["0", "1", "2", "3", "4"]
    assert second["next_cursor"] is None


async def test_comments_follow_post_visibility(
    ada: AsyncClient, ben: AsyncClient, cy: AsyncClient, client: AsyncClient
) -> None:
    await befriend(ada, ben, "ben")
    private = await post(ada, "Friends only", "friends")
    assert (
        await cy.post(f"/v1/posts/{private['id']}/comments", json={"body_md": "hi"})
    ).status_code == 404
    assert (await client.get(f"/v1/posts/{private['id']}/comments")).status_code == 404
    # Ben can comment, but mentioning Cy doesn't notify her: she can't see the post.
    await comment(ben, private["id"], "@cyd look")
    assert await notes(cy) == []
    assert (
        await client.post(f"/v1/posts/{private['id']}/comments", json={"body_md": "hi"})
    ).status_code == 401
    empty = await ben.post(f"/v1/posts/{private['id']}/comments", json={"body_md": "   "})
    assert empty.status_code == 422


async def test_blocked_commenters_are_hidden(
    ada: AsyncClient, ben: AsyncClient, cy: AsyncClient
) -> None:
    created = await post(ada, "Hello")
    await comment(ben, created["id"], "From Ben")
    await comment(cy, created["id"], "From Cy")
    assert (await cy.put("/v1/me/blocks/ben")).status_code == 204
    seen = (await cy.get(f"/v1/posts/{created['id']}/comments")).json()["items"]
    assert [c["body_md"] for c in seen] == ["From Cy"]
    assert (await cy.get(f"/v1/posts/{created['id']}")).json()["comment_count"] == 1
    assert (await ada.get(f"/v1/posts/{created['id']}")).json()["comment_count"] == 2


async def test_delete_comments(ada: AsyncClient, ben: AsyncClient, cy: AsyncClient) -> None:
    created = await post(ada, "Hello")
    bens = await comment(ben, created["id"], "Mine")
    cys = await comment(cy, created["id"], "Also mine")

    assert (await cy.delete(f"/v1/comments/{bens['id']}")).status_code == 404  # not hers
    assert (await ben.delete(f"/v1/comments/{bens['id']}")).status_code == 204
    assert (await ada.delete(f"/v1/comments/{cys['id']}")).status_code == 204  # her post
    assert (await ada.delete(f"/v1/comments/{cys['id']}")).status_code == 404
    assert (await ada.get(f"/v1/posts/{created['id']}/comments")).json()["items"] == []
    assert await notes(ada) == []  # both notifications withdrawn


async def test_deleting_a_post_withdraws_comment_notifications(
    ada: AsyncClient, ben: AsyncClient
) -> None:
    created = await post(ada, "Hello")
    await comment(ben, created["id"], "Hi")
    assert len(await notes(ada)) == 1
    assert (await ada.delete(f"/v1/posts/{created['id']}")).status_code == 204
    assert await notes(ada) == []
