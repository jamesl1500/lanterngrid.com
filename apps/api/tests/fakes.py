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
