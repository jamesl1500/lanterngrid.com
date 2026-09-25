from typing import Any

from httpx import AsyncClient

from tests.helpers import befriend
from tests.test_snippets import snippet


async def create(client: AsyncClient, **body: Any) -> Any:
    return await client.post("/v1/posts", json=body)


async def test_share_a_snippet(ada: AsyncClient, ben: AsyncClient, client: AsyncClient) -> None:
    made = await snippet(ada, title="Planner")
    response = await create(ada, snippet_id=made["id"])
    assert response.status_code == 201, response.text
    post = response.json()
    assert post["kind"] == "snippet"
    assert post["body_md"] == ""
    assert post["snippet"]["title"] == "Planner"
    assert (await client.get(f"/v1/posts/{post['id']}")).json()["snippet"]["id"] == made["id"]

    # Deleting the snippet leaves the post, without the snippet.
    await ada.delete(f"/v1/snippets/{made['id']}")
    assert (await client.get(f"/v1/posts/{post['id']}")).json()["snippet"] is None

    bens = await snippet(ben)
    assert (await create(ada, snippet_id=bens["id"])).status_code == 400  # not hers


async def test_friends_only_snippets_need_friends_only_posts(
    ada: AsyncClient, ben: AsyncClient, cy: AsyncClient
) -> None:
    await befriend(ada, ben, "ben")
    made = await snippet(ada, visibility="friends")
    assert (await create(ada, snippet_id=made["id"])).status_code == 400
    post = (await create(ada, snippet_id=made["id"], visibility="friends")).json()
    url = f"/v1/posts/{post['id']}"
    assert (await ada.patch(url, json={"visibility": "public"})).status_code == 400
    assert (await ben.get(url)).json()["snippet"]["id"] == made["id"]
    assert (await cy.get(url)).status_code == 404


async def test_hidden_snippets_stay_hidden_in_public_posts(
    ada: AsyncClient, cy: AsyncClient
) -> None:
    made = await snippet(ada)
    post = (await create(ada, body_md="Look", snippet_id=made["id"])).json()
    # Made friends only after sharing: the public post no longer shows it to strangers.
    await ada.patch(f"/v1/snippets/{made['id']}", json={"visibility": "friends"})
    seen = (await cy.get(f"/v1/posts/{post['id']}")).json()
    assert (seen["body_md"], seen["snippet"]) == ("Look", None)


async def test_achievement_posts(ada: AsyncClient) -> None:
    response = await create(
        ada, achievement={"type": "shipped", "title": " Lantern Grid v1 "}, body_md="Finally!"
    )
    assert response.status_code == 201, response.text
    post = response.json()
    assert post["kind"] == "achievement"
    assert post["achievement"] == {"type": "shipped", "title": "Lantern Grid v1"}

    url = f"/v1/posts/{post['id']}"
    edited = await ada.patch(
        url, json={"achievement": {"type": "launched", "title": "v1"}, "body_md": ""}
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["achievement"] == {"type": "launched", "title": "v1"}

    for bad in (
        {"achievement": {"type": "won_lottery", "title": "x"}},
        {"achievement": {"type": "shipped", "title": " "}},
        {"achievement": {"type": "shipped", "title": "x"}, "snippet_id": post["id"]},
    ):
        assert (await create(ada, **bad)).status_code == 422, bad
