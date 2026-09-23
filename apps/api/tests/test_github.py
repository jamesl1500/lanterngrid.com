from collections.abc import Callable, Iterator
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from httpx import AsyncClient

from app.main import app
from app.modules.auth import github
from tests.helpers import onboard, sign_up

GITHUB_USER = {"id": 4242, "login": "octoada", "name": "Ada Octo"}
EMAILS = [
    {"email": "old@example.com", "primary": False, "verified": True},
    {"email": "Ada@Example.com", "primary": True, "verified": True},
]


def fake_github(
    user: dict[str, object] = GITHUB_USER, emails: list[dict[str, object]] = EMAILS
) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        match request.url.path:
            case "/login/oauth/access_token":
                assert b"code=good-code" in request.content
                return httpx.Response(200, json={"access_token": "gho_test"})
            case "/user":
                return httpx.Response(200, json=user)
            case "/user/emails":
                return httpx.Response(200, json=emails)
        return httpx.Response(404)

    return handler


@pytest.fixture
def use_github() -> Iterator[Callable[..., None]]:
    def install(**kwargs: object) -> None:
        transport = httpx.MockTransport(fake_github(**kwargs))  # type: ignore[arg-type]

        async def override() -> httpx.AsyncClient:
            return httpx.AsyncClient(transport=transport)

        app.dependency_overrides[github.get_http] = override

    yield install
    app.dependency_overrides.pop(github.get_http, None)


async def start(client: AsyncClient, next_path: str = "/feed") -> str:
    response = await client.get("/v1/auth/github/start", params={"next": next_path})
    assert response.status_code == 302
    query = parse_qs(urlparse(response.headers["location"]).query)
    assert query["redirect_uri"] == ["http://testserver/api/v1/auth/github/callback"]
    return query["state"][0]


async def callback(client: AsyncClient, state: str, code: str = "good-code") -> httpx.Response:
    return await client.get("/v1/auth/github/callback", params={"code": code, "state": state})


async def test_github_sign_in_creates_a_verified_account(
    client: AsyncClient, use_github: Callable[..., None]
) -> None:
    use_github()
    response = await callback(client, await start(client))

    assert response.status_code == 302
    assert response.headers["location"] == "http://testserver/onboarding?suggested=octoada"
    me = (await client.get("/v1/auth/me")).json()
    assert me["email"] == "ada@example.com"
    assert me["email_verified"] is True
    assert me["has_password"] is False
    assert me["github_login"] == "octoada"
    assert me["display_name"] == "Ada Octo"


async def test_github_sign_in_returns_to_next_once_onboarded(
    client: AsyncClient, use_github: Callable[..., None]
) -> None:
    use_github()
    await callback(client, await start(client))
    await onboard(client)
    client.cookies.delete("lg_session")

    response = await callback(client, await start(client, "/u/adapark"))
    assert response.headers["location"] == "http://testserver/u/adapark"


async def test_github_links_to_an_existing_account_with_the_same_email(
    client: AsyncClient, use_github: Callable[..., None]
) -> None:
    created = (await sign_up(client, email="ada@example.com")).json()
    client.cookies.clear()
    use_github()

    await callback(client, await start(client))
    me = (await client.get("/v1/auth/me")).json()
    assert me["id"] == created["id"]
    assert me["github_login"] == "octoada"


async def test_github_connects_to_the_signed_in_account(
    client: AsyncClient, use_github: Callable[..., None]
) -> None:
    created = (await sign_up(client, email="someone-else@example.com")).json()
    use_github()

    await callback(client, await start(client))
    me = (await client.get("/v1/auth/me")).json()
    assert me["id"] == created["id"]
    assert me["github_login"] == "octoada"


async def test_github_callback_rejects_a_bad_state(
    client: AsyncClient, use_github: Callable[..., None]
) -> None:
    use_github()
    await start(client)
    response = await callback(client, "forged-state")
    assert response.headers["location"] == "http://testserver/signin?error=github_state"
    assert (await client.get("/v1/auth/me")).status_code == 401


async def test_github_requires_a_verified_email(
    client: AsyncClient, use_github: Callable[..., None]
) -> None:
    use_github(emails=[{"email": "ada@example.com", "primary": True, "verified": False}])
    response = await callback(client, await start(client))
    assert response.headers["location"] == "http://testserver/signin?error=github_email"


async def test_github_start_rejects_offsite_next(client: AsyncClient) -> None:
    response = await client.get("/v1/auth/github/start", params={"next": "//evil.example"})
    assert response.cookies["lg_oauth_state"].endswith("|")


async def test_providers_reports_github(client: AsyncClient) -> None:
    assert (await client.get("/v1/auth/providers")).json() == {"github": True}


async def test_connecting_a_second_github_account_is_refused(
    client: AsyncClient, use_github: Callable[..., None]
) -> None:
    use_github()
    await callback(client, await start(client))
    use_github(user={"id": 999, "login": "someone-else", "name": None})

    response = await callback(client, await start(client))
    assert response.headers["location"] == (
        "http://testserver/settings/account?error=github_other_account"
    )
    assert (await client.get("/v1/auth/me")).json()["github_login"] == "octoada"
