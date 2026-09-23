import pytest
from httpx import AsyncClient

from tests.fakes import FakeStorage
from tests.helpers import onboard, sign_up

MB = 1024 * 1024


@pytest.fixture
async def signed_in(client: AsyncClient) -> AsyncClient:
    await sign_up(client)
    await onboard(client)
    return client


async def upload(
    client: AsyncClient,
    storage: FakeStorage,
    kind: str = "avatar",
    content_type: str = "image/png",
    size: int = 1000,
) -> str:
    response = await client.post(
        "/v1/me/uploads", json={"kind": kind, "content_type": content_type, "size": size}
    )
    assert response.status_code == 201, response.text
    ticket = response.json()
    assert ticket["headers"] == {"Content-Type": content_type}
    storage.put(ticket["key"], size=size, content_type=content_type)
    return str(ticket["key"])


async def test_upload_ticket_is_scoped_to_the_person(
    signed_in: AsyncClient, storage: FakeStorage
) -> None:
    me = (await signed_in.get("/v1/auth/me")).json()
    response = await signed_in.post(
        "/v1/me/uploads", json={"kind": "banner", "content_type": "image/webp", "size": 4 * MB}
    )
    assert response.status_code == 201
    ticket = response.json()
    assert ticket["key"].startswith(f"banners/{me['id']}/")
    assert ticket["key"].endswith(".webp")
    assert ticket["upload_url"].startswith("https://storage.test/upload/")
    assert storage.presigned == [(ticket["key"], "image/webp", 4 * MB)]


@pytest.mark.parametrize(
    ("kind", "content_type", "size", "message"),
    [
        ("avatar", "image/png", 2 * MB + 1, "Avatars can be up to 2 MB."),
        ("banner", "image/png", 5 * MB + 1, "Banners can be up to 5 MB."),
        ("avatar", "image/svg+xml", 100, None),
        ("avatar", "image/png", 0, None),
    ],
)
async def test_upload_limits(
    signed_in: AsyncClient, kind: str, content_type: str, size: int, message: str | None
) -> None:
    response = await signed_in.post(
        "/v1/me/uploads", json={"kind": kind, "content_type": content_type, "size": size}
    )
    assert response.status_code == 422
    if message:
        assert message in response.text


async def test_uploads_need_a_session(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/me/uploads", json={"kind": "avatar", "content_type": "image/png", "size": 10}
    )
    assert response.status_code == 401


async def test_attach_replace_and_remove_avatar(
    signed_in: AsyncClient, storage: FakeStorage
) -> None:
    first = await upload(signed_in, storage)
    response = await signed_in.put("/v1/me/images/avatar", json={"key": first})
    assert response.status_code == 200, response.text
    assert response.json() == {
        "avatar_url": f"http://localhost:9000/lanterngrid-media/{first}",
        "banner_url": None,
    }
    assert (await signed_in.get("/v1/auth/me")).json()["avatar_url"].endswith(first)
    profile = (await signed_in.get("/v1/users/adapark")).json()
    assert profile["avatar_url"].endswith(first)

    second = await upload(signed_in, storage, content_type="image/jpeg")
    await signed_in.put("/v1/me/images/avatar", json={"key": second})
    assert first not in storage.objects  # the replaced file is cleaned up
    assert second in storage.objects

    response = await signed_in.delete("/v1/me/images/avatar")
    assert response.json()["avatar_url"] is None
    assert storage.objects == {}


async def test_attach_rejects_missing_or_foreign_uploads(
    signed_in: AsyncClient, client: AsyncClient, storage: FakeStorage
) -> None:
    key = await upload(signed_in, storage)
    # Never uploaded.
    missing = key.replace(key.rsplit("/", 1)[1], "0199aaaa-0000-7000-8000-000000000000.png")
    response = await signed_in.put("/v1/me/images/avatar", json={"key": missing})
    assert response.status_code == 400
    # Uploaded as an avatar, attached as a banner.
    response = await signed_in.put("/v1/me/images/banner", json={"key": key})
    assert response.status_code == 400
    # Someone else's file.
    await signed_in.post("/v1/auth/signout")
    await sign_up(client, email="grace@example.com")
    await onboard(client, "grace")
    response = await client.put("/v1/me/images/avatar", json={"key": key})
    assert response.status_code == 400
    assert key in storage.objects


async def test_attach_rejects_files_that_break_the_limits(
    signed_in: AsyncClient, storage: FakeStorage
) -> None:
    key = await upload(signed_in, storage)
    # The browser sent something other than what the ticket was for.
    storage.put(key, size=3 * MB, content_type="image/png")
    response = await signed_in.put("/v1/me/images/avatar", json={"key": key})
    assert response.status_code == 400
    assert key not in storage.objects
