import uuid
from typing import Literal

from pydantic import BaseModel

from app.modules.repos.schemas import RepoOut
from app.modules.snippets.schemas import SnippetOut

PinType = Literal["snippet", "repo"]

MAX_PINS = 6


class PinIn(BaseModel):
    type: PinType
    id: uuid.UUID


class PinOut(BaseModel):
    type: PinType
    # The one matching `type` is set.
    snippet: SnippetOut | None = None
    repo: RepoOut | None = None


class Pins(BaseModel):
    """In the order they were pinned. Only what the viewer can see."""

    items: list[PinOut]
