from typing import Any

import httpx

from app.core.storage import StoredObject


class FakeStorage:
    """In-memory bucket. Tests "upload" by calling put() with what the browser would send."""

    def __init__(self) -> None:
        self.objects: dict[str, StoredObject] = {}
        self.presigned: list[tuple[str, str, int]] = []

    def presign_upload(self, key: str, *, content_type: str, size: int) -> str:
        self.presigned.append((key, content_type, size))
        return f"https://storage.test/upload/{key}?signature=fake"

    async def head(self, key: str) -> StoredObject | None:
        return self.objects.get(key)

    async def delete(self, key: str) -> None:
        self.objects.pop(key, None)

    def put(self, key: str, *, size: int, content_type: str) -> None:
        self.objects[key] = StoredObject(size=size, content_type=content_type)


class FakeGitHub:
    """Answers the GitHub REST calls the repos module makes, from repos added with add()."""

    def __init__(self) -> None:
        self.repos: dict[int, dict[str, Any]] = {}
        self.rate_limited = False
        self.requests: list[httpx.Request] = []

    def add(self, full_name: str, **fields: Any) -> dict[str, Any]:
        repo: dict[str, Any] = {
            "id": len(self.repos) + 1000,
            "full_name": full_name,
            "description": f"{full_name} does things",
            "homepage": None,
            "language": "Python",
            "stargazers_count": 10,
            "forks_count": 2,
            "open_issues_count": 1,
            "topics": ["cli"],
            "fork": False,
            "archived": False,
            "private": False,
            "pushed_at": "2026-09-20T12:00:00Z",
            **fields,
        }
        self.repos[repo["id"]] = repo
        return repo

    def etag(self, repo: dict[str, Any]) -> str:
        return f'W/"{repo["id"]}-{repo["stargazers_count"]}"'

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.rate_limited:
            return httpx.Response(403, headers={"x-ratelimit-remaining": "0"})
        path = request.url.path
        found: dict[str, Any] | None = None
        if path.startswith("/repositories/"):
            found = self.repos.get(int(path.removeprefix("/repositories/")))
        elif path.startswith("/repos/"):
            name = path.removeprefix("/repos/").lower()
            found = next((r for r in self.repos.values() if r["full_name"].lower() == name), None)
        if found is None:
            return httpx.Response(404, json={"message": "Not Found"})
        etag = self.etag(found)
        if request.headers.get("if-none-match") == etag:
            return httpx.Response(304)
        return httpx.Response(200, json=found, headers={"etag": etag})

    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(self.handle))
