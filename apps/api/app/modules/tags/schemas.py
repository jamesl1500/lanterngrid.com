import re
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator

TagKind = Literal["language", "tool", "topic"]

MAX_TAG_LENGTH = 32
MAX_PROFILE_TAGS = 12

_SPELLED_OUT = (("#", "sharp"), ("+", "p"))
_DISALLOWED = re.compile(r"[^a-z0-9.-]+")


def slugify(name: str) -> str:
    """A URL-safe key for a tag name, or "" when nothing usable is left.

    "TypeScript" -> "typescript", "C++" -> "cpp", "C#" -> "csharp", ".NET" -> "dotnet",
    "Node.js" -> "node.js", "Machine learning" -> "machine-learning".
    """
    slug = name.strip().lower()
    for char, word in _SPELLED_OUT:
        slug = slug.replace(char, word)
    if slug.startswith("."):
        slug = "dot" + slug[1:]
    slug = re.sub(r"-{2,}", "-", _DISALLOWED.sub("-", slug))
    return slug[:MAX_TAG_LENGTH].strip("-.")


def _clean_name(value: object) -> object:
    return " ".join(value.split()) if isinstance(value, str) else value


def _check_name(value: str) -> str:
    if len(value) > MAX_TAG_LENGTH:
        raise ValueError(f"Keep tags to {MAX_TAG_LENGTH} characters.")
    if not slugify(value):
        raise ValueError("Tags need at least one letter or number.")
    return value


def _dedupe(names: list[str]) -> list[str]:
    seen: set[str] = set()
    unique = []
    for name in names:
        if (slug := slugify(name)) not in seen:
            seen.add(slug)
            unique.append(name)
    if len(unique) > MAX_PROFILE_TAGS:
        raise ValueError(f"Pick up to {MAX_PROFILE_TAGS} tags.")
    return unique


TagName = Annotated[str, BeforeValidator(_clean_name), AfterValidator(_check_name)]
# Duplicates (by slug) are dropped, keeping the first spelling.
TagList = Annotated[list[TagName], AfterValidator(_dedupe)]


class TagOut(BaseModel):
    slug: str
    name: str
    kind: TagKind


class TagsUpdate(BaseModel):
    """The full list, in order. Tags nobody has used yet are created."""

    tags: TagList
