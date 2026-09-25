from typing import Any

from httpx import AsyncClient

from tests.helpers import befriend

CODE = 'fn main() {\n    println!("hi");\n}\n\n\n'


async def snippet(client: AsyncClient, **fields: Any) -> dict[str, Any]:
    body = {"title": "Hello", "language": "rust", "content": CODE, **fields}
    response = await client.post("/v1/snippets", json=body)
    assert response.status_code == 201, response.text
    return dict(response.json())


async def test_create_edit_and_delete(ada: AsyncClient, client: AsyncClient) -> None:
    made = await snippet(ada, title="  Hello  ", filename=" main.rs ", description=" Classic ")
    assert (made["title"], made["filename"], made["description"]) == ("Hello", "main.rs", "Classic")
    assert made["content"] == 'fn main() {\n    println!("hi");\n}'  # trailing blank lines go
    assert made["line_count"] == 3
    assert made["owner"]["username"] == "ada"
    url = f"/v1/snippets/{made['id']}"
    assert (await client.get(url)).json()["title"] == "Hello"

    edited = (await ada.patch(url, json={"title": "Hi", "filename": None})).json()
    assert (edited["title"], edited["filename"], edited["language"]) == ("Hi", None, "rust")

    assert (await ada.delete(url)).status_code == 204
    assert (await client.get(url)).status_code == 404
    assert (await ada.patch(url, json={"title": "x"})).status_code == 404


async def test_validation(ada: AsyncClient) -> None:
    base = {"title": "t", "content": "x"}
    for bad in (
        {"title": " "},
        {"content": "\n\n"},
        {"language": "brainfuck"},
        {"filename": "src/main.rs"},
        {"content": "x" * 50_001},
    ):
        response = await ada.post("/v1/snippets", json={**base, **bad})
        assert response.status_code == 422, bad
    assert (await ada.post("/v1/snippets", json=base)).json()["language"] == "text"


async def test_only_the_owner_can_edit(ada: AsyncClient, ben: AsyncClient) -> None:
    made = await snippet(ada)
    url = f"/v1/snippets/{made['id']}"
    assert (await ben.patch(url, json={"title": "Mine now"})).status_code == 404
    assert (await ben.delete(url)).status_code == 404


async def test_visibility_and_listing(
    ada: AsyncClient, ben: AsyncClient, cy: AsyncClient, client: AsyncClient
) -> None:
    await befriend(ada, ben, "ben")
    public = await snippet(ada, title="Public")
    private = await snippet(ada, title="Friends", visibility="friends")

    def titles(page: Any) -> list[str]:
        return [s["title"] for s in page.json()["items"]]

    assert titles(await ben.get("/v1/users/ada/snippets")) == ["Friends", "Public"]
    assert titles(await cy.get("/v1/users/ada/snippets")) == ["Public"]
    assert titles(await client.get("/v1/users/ada/snippets")) == ["Public"]
    assert (await cy.get(f"/v1/snippets/{private['id']}")).status_code == 404
    assert (await ben.get(f"/v1/snippets/{private['id']}")).status_code == 200

    first = (await ben.get("/v1/users/ada/snippets", params={"limit": 1})).json()
    rest = await ben.get(
        "/v1/users/ada/snippets", params={"limit": 1, "cursor": first["next_cursor"]}
    )
    assert titles(rest) == ["Public"] and public["title"] == "Public"

    assert (await cy.put("/v1/me/blocks/ada")).status_code == 204
    assert (await ada.get("/v1/users/cyd/snippets")).status_code == 404
    assert (await cy.get(f"/v1/snippets/{public['id']}")).status_code == 404


async def test_pins(ada: AsyncClient, ben: AsyncClient, client: AsyncClient) -> None:
    first = await snippet(ada, title="First")
    second = await snippet(ada, title="Second", visibility="friends")
    bens = await snippet(ben, title="Ben's")

    assert (await ada.put(f"/v1/me/pins/snippet/{second['id']}")).status_code == 200
    pins = (await ada.put(f"/v1/me/pins/snippet/{first['id']}")).json()["items"]
    assert [p["snippet"]["title"] for p in pins] == ["Second", "First"]  # pinned order
    again = await ada.put(f"/v1/me/pins/snippet/{first['id']}")
    assert len(again.json()["items"]) == 2  # pinning twice changes nothing
    assert (await ada.put(f"/v1/me/pins/snippet/{bens['id']}")).status_code == 404

    # Strangers only see pins they're allowed to see.
    seen = (await client.get("/v1/users/ada/pins")).json()["items"]
    assert [p["snippet"]["title"] for p in seen] == ["First"]

    after = (await ada.delete(f"/v1/me/pins/snippet/{second['id']}")).json()["items"]
    assert [p["snippet"]["title"] for p in after] == ["First"]
    # Deleting a snippet unpins it.
    await ada.delete(f"/v1/snippets/{first['id']}")
    assert (await ada.get("/v1/users/ada/pins")).json()["items"] == []


async def test_pin_limit(ada: AsyncClient) -> None:
    for n in range(6):
        made = await snippet(ada, title=str(n))
        assert (await ada.put(f"/v1/me/pins/snippet/{made['id']}")).status_code == 200
    seventh = await snippet(ada, title="7")
    assert (await ada.put(f"/v1/me/pins/snippet/{seventh['id']}")).status_code == 400
