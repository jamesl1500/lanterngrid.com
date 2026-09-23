from httpx import AsyncClient

from app.core.email import outbox
from tests.helpers import PASSWORD, sign_up, token_from_last_email


async def test_sign_up_signs_in_and_sends_a_verification_email(client: AsyncClient) -> None:
    response = await sign_up(client, email="  Ada@Example.com ")

    me = response.json()
    assert me["email"] == "ada@example.com"
    assert me["email_verified"] is False
    assert me["username"] is None
    assert me["has_password"] is True
    assert "lg_session" in response.cookies
    set_cookie = response.headers["set-cookie"].lower()
    assert "httponly" in set_cookie and "samesite=lax" in set_cookie

    assert (await client.get("/v1/auth/me")).json()["id"] == me["id"]
    assert len(outbox) == 1
    assert outbox[0].to == "ada@example.com"
    assert "http://testserver/verify-email?token=" in outbox[0].text


async def test_sign_up_rejects_a_taken_email_in_any_case(client: AsyncClient) -> None:
    await sign_up(client)
    response = await client.post(
        "/v1/auth/signup",
        json={"email": "ADA@example.com", "password": PASSWORD, "display_name": "Other"},
    )
    assert response.status_code == 409


async def test_sign_up_validates_input(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/auth/signup", json={"email": "nope", "password": "short", "display_name": " "}
    )
    assert response.status_code == 422
    fields = {error["loc"][-1] for error in response.json()["detail"]}
    assert fields == {"email", "password", "display_name"}


async def test_me_requires_a_session(client: AsyncClient) -> None:
    assert (await client.get("/v1/auth/me")).status_code == 401


async def test_sign_in_and_sign_out(client: AsyncClient) -> None:
    await sign_up(client)
    client.cookies.clear()

    bad = await client.post(
        "/v1/auth/signin", json={"email": "ada@example.com", "password": "wrong password"}
    )
    assert bad.status_code == 401
    unknown = await client.post(
        "/v1/auth/signin", json={"email": "nobody@example.com", "password": PASSWORD}
    )
    assert unknown.status_code == 401

    good = await client.post(
        "/v1/auth/signin", json={"email": "ADA@example.com", "password": PASSWORD}
    )
    assert good.status_code == 200
    assert (await client.get("/v1/auth/me")).status_code == 200

    assert (await client.post("/v1/auth/signout")).status_code == 204
    assert (await client.get("/v1/auth/me")).status_code == 401


async def test_sign_in_is_rate_limited_per_email(client: AsyncClient) -> None:
    await sign_up(client)
    for _ in range(10):
        await client.post(
            "/v1/auth/signin", json={"email": "ada@example.com", "password": "wrong password"}
        )
    response = await client.post(
        "/v1/auth/signin", json={"email": "ada@example.com", "password": PASSWORD}
    )
    assert response.status_code == 429


async def test_sign_out_everywhere_ends_every_session(client: AsyncClient) -> None:
    await sign_up(client)
    other_browser = client.cookies.get("lg_session")
    signin = await client.post(
        "/v1/auth/signin", json={"email": "ada@example.com", "password": PASSWORD}
    )
    assert signin.status_code == 200

    assert (await client.post("/v1/auth/signout-everywhere")).status_code == 204
    client.cookies.set("lg_session", other_browser or "")
    assert (await client.get("/v1/auth/me")).status_code == 401


async def test_verify_email_link_works_once(client: AsyncClient) -> None:
    await sign_up(client)
    token = token_from_last_email("verify-email")

    first = await client.post("/v1/auth/verify-email", json={"token": token})
    assert first.status_code == 200
    assert first.json()["email_verified"] is True

    again = await client.post("/v1/auth/verify-email", json={"token": token})
    assert again.status_code == 400


async def test_resending_verification_replaces_the_old_link(client: AsyncClient) -> None:
    await sign_up(client)
    old = token_from_last_email("verify-email")
    assert (await client.post("/v1/auth/verify-email/resend")).status_code == 202
    new = token_from_last_email("verify-email")

    assert (await client.post("/v1/auth/verify-email", json={"token": old})).status_code == 400
    assert (await client.post("/v1/auth/verify-email", json={"token": new})).status_code == 200


async def test_password_reset_flow(client: AsyncClient) -> None:
    await sign_up(client)
    signed_in_elsewhere = client.cookies.get("lg_session")
    client.cookies.clear()

    unknown = await client.post("/v1/auth/password-reset", json={"email": "who@example.com"})
    assert unknown.status_code == 202
    assert len(outbox) == 1  # only the sign-up email

    response = await client.post("/v1/auth/password-reset", json={"email": "ada@example.com"})
    assert response.status_code == 202
    token = token_from_last_email("reset-password")

    confirm = await client.post(
        "/v1/auth/password-reset/confirm",
        json={"token": token, "password": "a brand new password"},
    )
    assert confirm.status_code == 204

    # The reset ends existing sessions, verifies the email and only the new password works.
    client.cookies.set("lg_session", signed_in_elsewhere or "")
    assert (await client.get("/v1/auth/me")).status_code == 401
    client.cookies.clear()
    old = await client.post(
        "/v1/auth/signin", json={"email": "ada@example.com", "password": PASSWORD}
    )
    assert old.status_code == 401
    new = await client.post(
        "/v1/auth/signin", json={"email": "ada@example.com", "password": "a brand new password"}
    )
    assert new.status_code == 200
    assert new.json()["email_verified"] is True

    reused = await client.post(
        "/v1/auth/password-reset/confirm", json={"token": token, "password": "yet another one"}
    )
    assert reused.status_code == 400


async def test_cross_site_writes_are_blocked(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/auth/signup",
        json={"email": "ada@example.com", "password": PASSWORD, "display_name": "Ada"},
        headers={"Origin": "https://evil.example"},
    )
    assert response.status_code == 403

    same_site = await client.post(
        "/v1/auth/signup",
        json={"email": "ada@example.com", "password": PASSWORD, "display_name": "Ada"},
        headers={"Origin": "http://testserver"},
    )
    assert same_site.status_code == 201
