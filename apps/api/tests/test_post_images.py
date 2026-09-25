from typing import Any

from httpx import AsyncClient

from tests.fakes import FakeStorage
from tests.test_media import MB, upload


async def create(client: AsyncClient, **body: Any) -> Any:
    return await client.post("/v1/posts", json=body)


async def test_post_with_images_only(ada: AsyncClient, storage: FakeStorage) -> None:
    first = await upload(ada, storage, kind="post")
    second = await upload(ada, storage, kind="post", content_type="image/webp")
    assert first.startswith("posts/")
    response = await create(ada, images=[{"key": first, "alt": " A flame graph "}, {"key": second}])
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["body_md"] == ""
    assert [(i["key"], i["alt"]) for i in created["images"]] == [
        (first, "A flame graph"),
        (second, ""),
    ]
    assert created["images"][0]["url"].endswith(f"/{first}")


async def test_posts_need_text_or_an_image(ada: AsyncClient, storage: FakeStorage) -> None:
    assert (await create(ada, body_md="  ")).status_code == 422
    assert (await create(ada)).status_code == 422
    too_many = [{"key": await upload(ada, storage, kind="post")} for _ in range(5)]
    assert (await create(ada, body_md="hi", images=too_many)).status_code == 422


async def test_rejects_uploads_that_arent_yours_or_break_limits(
    ada: AsyncClient, ben: AsyncClient, storage: FakeStorage
) -> None:
    bens = await upload(ben, storage, kind="post")
    avatar = await upload(ada, storage, kind="avatar")
    missing = await upload(ada, storage, kind="post")
    del storage.objects[missing]  # a ticket was issued but nothing arrived
    for key in (bens, avatar, missing):
        response = await create(ada, body_md="hi", images=[{"key": key}])
        assert response.status_code == 400, key
    # Upload tickets check the size, but the file itself is checked again.
    big = await upload(ada, storage, kind="post")
    storage.put(big, size=6 * MB, content_type="image/png")
    assert (await create(ada, body_md="hi", images=[{"key": big}])).status_code == 400
    assert big not in storage.objects
    same = await upload(ada, storage, kind="post")
    twice = [{"key": same}, {"key": same}]
    assert (await create(ada, body_md="hi", images=twice)).status_code == 400
    assert (await create(ada, body_md="hi", images=[{"key": same}])).status_code == 201
    reused = await create(ada, body_md="again", images=[{"key": same}])
    assert reused.status_code == 400  # already on another post
    too_big = {"kind": "post", "content_type": "image/png", "size": 6 * MB}
    assert (await ada.post("/v1/me/uploads", json=too_big)).status_code == 422


async def test_edit_images_and_delete_post(ada: AsyncClient, storage: FakeStorage) -> None:
    first = await upload(ada, storage, kind="post")
    second = await upload(ada, storage, kind="post")
    created = (await create(ada, body_md="", images=[{"key": first}])).json()
    url = f"/v1/posts/{created['id']}"

    # Replace the first image with the second.
    edited = await ada.patch(url, json={"images": [{"key": second, "alt": "after"}]})
    assert edited.status_code == 200, edited.text
    assert [i["key"] for i in edited.json()["images"]] == [second]
    assert first not in storage.objects  # the dropped image is cleaned up

    # Can't remove the last image of a post with no text.
    emptied = await ada.patch(url, json={"images": []})
    assert emptied.status_code == 400
    assert [i["key"] for i in (await ada.get(url)).json()["images"]] == [second]

    # Text alone is fine once there's text.
    assert (
        await ada.patch(url, json={"body_md": "Now with words", "images": []})
    ).status_code == 200
    assert second not in storage.objects

    third = await upload(ada, storage, kind="post")
    await ada.patch(url, json={"images": [{"key": third}]})
    assert (await ada.delete(url)).status_code == 204
    assert third not in storage.objects
