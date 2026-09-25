import pytest
from httpx import AsyncClient

from tests.helpers import onboard, sign_up


async def test_onboarding_sets_username_and_profile(client: AsyncClient) -> None:
    await sign_up(client)
    response = await client.post(
        "/v1/me/onboarding",
        json={"username": "AdaPark", "display_name": " Ada P. ", "headline": "Backend at Grid"},
    )
    assert response.status_code == 200
    me = response.json()
    assert me["username"] == "AdaPark"
    assert me["display_name"] == "Ada P."
    assert me["headline"] == "Backend at Grid"

    again = await client.post(
        "/v1/me/onboarding", json={"username": "another", "display_name": "Ada"}
    )
    assert again.status_code == 409


async def test_usernames_are_unique_ignoring_case(client: AsyncClient) -> None:
    await sign_up(client, email="ada@example.com")
    await onboard(client, "adapark")
    client.cookies.clear()
    await sign_up(client, email="ben@example.com")

    response = await client.post(
        "/v1/me/onboarding", json={"username": "ADAPARK", "display_name": "Ben"}
    )
    assert response.status_code == 409
    check = await client.get("/v1/usernames/AdaPark")
    assert check.json() == {"username": "AdaPark", "available": False, "problem": "taken"}


@pytest.mark.parametrize(
    ("username", "problem"),
    [
        ("ab", "invalid"),
        ("-ada", "invalid"),
        ("ada park", "invalid"),
        ("a" * 31, "invalid"),
        ("settings", "reserved"),
        ("Admin", "reserved"),
        ("ada_park-99", None),
    ],
)
async def test_username_rules(client: AsyncClient, username: str, problem: str | None) -> None:
    check = (await client.get(f"/v1/usernames/{username}")).json()
    assert check["problem"] == problem
    assert check["available"] is (problem is None)

    await sign_up(client)
    response = await client.post(
        "/v1/me/onboarding", json={"username": username, "display_name": "Ada"}
    )
    assert response.status_code == (200 if problem is None else 422)


async def test_public_profile(client: AsyncClient) -> None:
    await sign_up(client)
    assert (await client.get("/v1/users/adapark")).status_code == 404
    await onboard(client, "adapark")

    response = await client.get("/v1/users/ADAPARK")
    assert response.status_code == 200
    profile = response.json()
    assert profile["username"] == "adapark"
    assert profile["accent_color"] == "violet"
    assert "email" not in profile


async def test_update_profile(client: AsyncClient) -> None:
    await sign_up(client)
    await onboard(client)

    response = await client.patch(
        "/v1/me/profile",
        json={
            "headline": "Staff engineer",
            "bio": "I like fast queries.",
            "website": "https://ada.dev",
            "accent_color": "lime",
        },
    )
    assert response.status_code == 200
    assert response.json()["accent_color"] == "lime"

    cleared = await client.patch("/v1/me/profile", json={"website": "", "bio": None})
    body = cleared.json()
    assert body["website"] is None and body["bio"] is None
    assert body["headline"] == "Staff engineer"  # untouched

    profile = (await client.get("/v1/users/adapark")).json()
    assert profile["headline"] == "Staff engineer"
    assert profile["accent_color"] == "lime"


async def test_update_profile_validates(client: AsyncClient) -> None:
    await sign_up(client)
    response = await client.patch(
        "/v1/me/profile",
        json={"website": "javascript:alert(1)", "accent_color": "beige", "headline": "x" * 121},
    )
    assert response.status_code == 422
    fields = {error["loc"][1] for error in response.json()["detail"]}
    assert fields == {"website", "accent_color", "headline"}


async def test_profile_endpoints_need_a_session(client: AsyncClient) -> None:
    assert (await client.get("/v1/me/profile")).status_code == 401
    assert (await client.patch("/v1/me/profile", json={})).status_code == 401
    assert (await client.put("/v1/me/links", json={"links": []})).status_code == 401
    assert (await client.put("/v1/me/tags", json={"tags": []})).status_code == 401


async def test_set_links_replaces_the_list_in_order(client: AsyncClient) -> None:
    await sign_up(client)
    await onboard(client)
    links = [
        {"kind": "github", "url": "https://github.com/adapark"},
        {"kind": "mastodon", "url": "https://hachyderm.io/@ada"},
        {"kind": "blog", "url": " https://ada.dev/blog "},
    ]
    response = await client.put("/v1/me/links", json={"links": links})
    assert response.status_code == 200, response.text
    assert [link["kind"] for link in response.json()] == ["github", "mastodon", "blog"]
    assert response.json()[2]["url"] == "https://ada.dev/blog"

    await client.put("/v1/me/links", json={"links": links[1:2]})
    settings = (await client.get("/v1/me/profile")).json()
    assert settings["links"] == [{"kind": "mastodon", "url": "https://hachyderm.io/@ada"}]
    profile = (await client.get("/v1/users/adapark")).json()
    assert profile["links"] == settings["links"]


async def test_set_links_validates(client: AsyncClient) -> None:
    await sign_up(client)
    bad = [
        {"kind": "github", "url": "javascript:alert(1)"},
        {"kind": "myspace", "url": "https://myspace.com/ada"},
        {"kind": "blog", "url": ""},
    ]
    response = await client.put("/v1/me/links", json={"links": bad})
    assert response.status_code == 422
    assert {tuple(e["loc"][2:4]) for e in response.json()["detail"]} == {
        (0, "url"),
        (1, "kind"),
        (2, "url"),
    }
    nine = [{"kind": "other", "url": f"https://example.com/{i}"} for i in range(9)]
    assert (await client.put("/v1/me/links", json={"links": nine})).status_code == 422
