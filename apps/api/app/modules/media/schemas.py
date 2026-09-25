from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

# What an upload is for. Profile images attach through /me/images; post images through a post.
UploadKind = Literal["avatar", "banner", "post"]
ImageKind = Literal["avatar", "banner"]
ImageType = Literal["image/png", "image/jpeg", "image/webp", "image/gif"]

EXTENSIONS: dict[str, str] = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
    "image/gif": "gif",
}
MAX_BYTES: dict[str, int] = {
    "avatar": 2 * 1024 * 1024,
    "banner": 5 * 1024 * 1024,
    "post": 5 * 1024 * 1024,
}


class UploadRequest(BaseModel):
    kind: UploadKind
    content_type: ImageType
    size: int = Field(gt=0)

    @model_validator(mode="after")
    def _check_size(self) -> Self:
        limit = MAX_BYTES[self.kind]
        if self.size > limit:
            label = {"avatar": "Avatars", "banner": "Banners", "post": "Images"}[self.kind]
            raise ValueError(f"{label} can be up to {limit // (1024 * 1024)} MB.")
        return self


class UploadTicket(BaseModel):
    """PUT the file to `upload_url` with exactly these headers, then attach `key`."""

    key: str
    upload_url: str
    headers: dict[str, str]


class AttachImage(BaseModel):
    key: str = Field(max_length=300)


class ProfileImages(BaseModel):
    avatar_url: str | None
    banner_url: str | None
