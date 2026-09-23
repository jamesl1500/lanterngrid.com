import re

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
