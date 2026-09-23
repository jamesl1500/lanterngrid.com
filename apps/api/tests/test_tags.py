import pytest
from httpx import AsyncClient

from app.modules.tags.schemas import slugify
from tests.helpers import onboard, sign_up


@pytest.mark.parametrize(
    ("name", "slug"),
    [
        ("TypeScript", "typescript"),
        ("C++", "cpp"),
        ("C#", "csharp"),
        (".NET", "dotnet"),
        ("Node.js", "node.js"),
        ("  Machine   learning ", "machine-learning"),
        ("Objective-C", "objective-c"),
        ("!!!", ""),
        ("x" * 40, "x" * 32),
    ],
)
def test_slugify(name: str, slug: str) -> None:
    assert slugify(name) == slug


async def test_suggest_prefers_prefix_matches_and_curated_tags(client: AsyncClient) -> None:
    response = await client.get("/v1/tags/suggest", params={"q": "type"})
    assert response.status_code == 200
    assert response.json()[0] == {"slug": "typescript", "name": "TypeScript", "kind": "language"}

    names = [t["name"] for t in (await client.get("/v1/tags/suggest?q=C%2B%2B")).json()]
    assert names[0] == "C++"

    # Typos still find something.
    slugs = [t["slug"] for t in (await client.get("/v1/tags/suggest?q=kubernets")).json()]
    assert "kubernetes" in slugs


async def test_suggest_without_a_query_lists_popular_tags(client: AsyncClient) -> None:
    await sign_up(client)
    await onboard(client)
    await client.put("/v1/me/tags", json={"tags": ["Zig"]})
    response = await client.get("/v1/tags/suggest", params={"limit": 3})
    assert response.json()[0]["slug"] == "zig"
    assert len(response.json()) == 3


async def test_set_tags_keeps_order_dedupes_and_creates_new_tags(client: AsyncClient) -> None:
    await sign_up(client)
    await onboard(client)
    response = await client.put(
        "/v1/me/tags", json={"tags": ["rust", "Postgres", "Rust", "  Home   lab "]}
    )
    assert response.status_code == 200, response.text
    assert response.json() == [
        {"slug": "rust", "name": "Rust", "kind": "language"},
        {"slug": "postgres", "name": "Postgres", "kind": "tool"},
        {"slug": "home-lab", "name": "Home lab", "kind": "topic"},
    ]
    profile = (await client.get("/v1/users/adapark")).json()
    assert [t["slug"] for t in profile["tags"]] == ["rust", "postgres", "home-lab"]
    # The new tag is now suggestable to everyone.
    suggested = (await client.get("/v1/tags/suggest?q=home")).json()
    assert suggested[0]["slug"] == "home-lab"

    response = await client.put("/v1/me/tags", json={"tags": []})
    assert response.json() == []


async def test_set_tags_limits(client: AsyncClient) -> None:
    await sign_up(client)
    await onboard(client)
    too_many = [f"tag{i}" for i in range(13)]
    response = await client.put("/v1/me/tags", json={"tags": too_many})
    assert response.status_code == 422
    assert "up to 12" in response.text
    response = await client.put("/v1/me/tags", json={"tags": ["???"]})
    assert response.status_code == 422


async def test_onboarding_can_set_tags(client: AsyncClient) -> None:
    await sign_up(client)
    response = await client.post(
        "/v1/me/onboarding",
        json={"username": "adapark", "display_name": "Ada Park", "tags": ["Go", "SRE"]},
    )
    assert response.status_code == 200, response.text
    profile = (await client.get("/v1/users/adapark")).json()
    assert [t["name"] for t in profile["tags"]] == ["Go", "SRE"]
