"""File storage for uploads. Browsers upload straight to the bucket with presigned URLs."""

import asyncio
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Annotated, Protocol

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import Depends

from app.core.config import get_settings

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

UPLOAD_URL_TTL_SECONDS = 300


@dataclass(frozen=True)
class StoredObject:
    size: int
    content_type: str


class Storage(Protocol):
    def presign_upload(self, key: str, *, content_type: str, size: int) -> str: ...

    async def head(self, key: str) -> StoredObject | None: ...

    async def delete(self, key: str) -> None: ...


class S3Storage:
    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.storage_bucket
        self.client: S3Client = boto3.client(
            "s3",
            endpoint_url=settings.storage_endpoint_url,
            region_name=settings.storage_region,
            aws_access_key_id=settings.storage_access_key,
            aws_secret_access_key=settings.storage_secret_key,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def presign_upload(self, key: str, *, content_type: str, size: int) -> str:
        # Content-Type and Content-Length are signed, so the browser must send exactly these.
        return self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": content_type,
                "ContentLength": size,
            },
            ExpiresIn=UPLOAD_URL_TTL_SECONDS,
        )

    async def head(self, key: str) -> StoredObject | None:
        try:
            response = await asyncio.to_thread(self.client.head_object, Bucket=self.bucket, Key=key)
        except ClientError:
            return None
        return StoredObject(
            size=response["ContentLength"], content_type=response.get("ContentType", "")
        )

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self.client.delete_object, Bucket=self.bucket, Key=key)


@lru_cache
def _s3() -> S3Storage:
    return S3Storage()


def get_storage() -> Storage:
    return _s3()


StorageDep = Annotated[Storage, Depends(get_storage)]


def public_url(key: str | None) -> str | None:
    return f"{get_settings().storage_public_url.rstrip('/')}/{key}" if key else None
