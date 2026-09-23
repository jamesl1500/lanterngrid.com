from httpx import AsyncClient


async def test_health_reports_ok_when_services_are_up(client: AsyncClient) -> None:
    response = await client.get("/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"] == {"database": "ok", "redis": "ok"}
