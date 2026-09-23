"""GitHub OAuth: exchange the callback code for a token and read who signed in."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Annotated, Any

import httpx
from fastapi import Depends

from app.core.config import get_settings

AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
API_URL = "https://api.github.com"
SCOPES = "read:user user:email"


class GitHubError(Exception):
    pass


@dataclass(frozen=True)
class GitHubUser:
    id: int
    login: str
    name: str | None
    # The primary address, only if GitHub has verified it.
    verified_email: str | None


async def get_http() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(timeout=10) as client:
        yield client


GitHubHttpDep = Annotated[httpx.AsyncClient, Depends(get_http)]


def callback_url() -> str:
    return f"{get_settings().web_url}/api/v1/auth/github/callback"


def authorize_url(state: str) -> str:
    params = httpx.QueryParams(
        client_id=get_settings().github_client_id or "",
        redirect_uri=callback_url(),
        scope=SCOPES,
        state=state,
        allow_signup="true",
    )
    return f"{AUTHORIZE_URL}?{params}"


async def exchange_code(http: httpx.AsyncClient, code: str) -> str:
    settings = get_settings()
    response = await http.post(
        TOKEN_URL,
        headers={"Accept": "application/json"},
        data={
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "code": code,
            "redirect_uri": callback_url(),
        },
    )
    body: dict[str, Any] = response.json() if response.is_success else {}
    token = body.get("access_token")
    if not isinstance(token, str):
        raise GitHubError(body.get("error_description") or "code exchange failed")
    return token


async def fetch_user(http: httpx.AsyncClient, access_token: str) -> GitHubUser:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    user_response = await http.get(f"{API_URL}/user", headers=headers)
    emails_response = await http.get(f"{API_URL}/user/emails", headers=headers)
    if not (user_response.is_success and emails_response.is_success):
        raise GitHubError("could not read the GitHub profile")
    user = user_response.json()
    primary = next(
        (e for e in emails_response.json() if e.get("primary") and e.get("verified")), None
    )
    return GitHubUser(
        id=int(user["id"]),
        login=str(user["login"]),
        name=user.get("name") or None,
        verified_email=str(primary["email"]).lower() if primary else None,
    )
