import re
from typing import Any

from httpx import AsyncClient, Response

from app.core.email import outbox

PASSWORD = "correct horse battery"


async def sign_up(
    client: AsyncClient,
    email: str = "ada@example.com",
    password: str = PASSWORD,
    display_name: str = "Ada Park",
) -> Response:
    response = await client.post(
        "/v1/auth/signup",
        json={"email": email, "password": password, "display_name": display_name},
    )
    assert response.status_code == 201, response.text
    return response


async def onboard(client: AsyncClient, username: str = "adapark") -> Response:
    response = await client.post(
        "/v1/me/onboarding", json={"username": username, "display_name": "Ada Park"}
    )
    assert response.status_code == 200, response.text
    return response


def token_from_last_email(path: str) -> str:
    match = re.search(rf"{path}\?token=([\w-]+)", outbox[-1].text)
    assert match, outbox[-1].text
    return match.group(1)


async def member(client: AsyncClient, username: str, display_name: str | None = None) -> str:
    """Sign up and onboard someone on this client; returns their username."""
    await sign_up(client, email=f"{username}@example.com", display_name=display_name or username)
    response = await client.post(
        "/v1/me/onboarding",
        json={"username": username, "display_name": display_name or username.capitalize()},
    )
    assert response.status_code == 200, response.text
    return username


async def befriend(a: AsyncClient, b: AsyncClient, b_username: str) -> None:
    sent = (await a.post("/v1/friend-requests", json={"username": b_username})).json()
    assert (await b.post(f"/v1/friend-requests/{sent['id']}/accept")).status_code == 200


async def post(client: AsyncClient, body: str, visibility: str = "public") -> dict[str, Any]:
    response = await client.post("/v1/posts", json={"body_md": body, "visibility": visibility})
    assert response.status_code == 201, response.text
    return dict(response.json())
