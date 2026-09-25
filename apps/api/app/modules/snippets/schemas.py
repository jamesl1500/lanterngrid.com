import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, Field

from app.modules.users.schemas import UserSummary

# Shiki language ids the editor and renderer both support, "text" for none.
Language = Literal[
    "text",
    "bash",
    "c",
    "clojure",
    "cpp",
    "csharp",
    "css",
    "dart",
    "diff",
    "dockerfile",
    "elixir",
    "erlang",
    "fsharp",
    "go",
    "graphql",
    "haskell",
    "hcl",
    "html",
    "java",
    "javascript",
    "json",
    "jsx",
    "julia",
    "kotlin",
    "lua",
    "markdown",
    "nix",
    "ocaml",
    "php",
    "powershell",
    "python",
    "r",
    "ruby",
    "rust",
    "scala",
    "scss",
    "sql",
    "svelte",
    "swift",
    "toml",
    "tsx",
    "typescript",
    "vue",
    "xml",
    "yaml",
    "zig",
]
Visibility = Literal["public", "friends"]

MAX_SNIPPET_LENGTH = 50_000


def _trim(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


def _trim_or_none(value: object) -> object:
    if isinstance(value, str):
        return value.strip() or None
    return value


Title = Annotated[str, BeforeValidator(_trim), Field(min_length=1, max_length=100)]
Filename = Annotated[
    Annotated[str, Field(max_length=100, pattern=r"^[^/\\]+$")] | None,
    BeforeValidator(_trim_or_none),
]
Description = Annotated[str, BeforeValidator(_trim), Field(max_length=500)]
# Code keeps its whitespace, apart from trailing blank lines.
Content = Annotated[
    str,
    BeforeValidator(lambda v: v.rstrip() if isinstance(v, str) else v),
    Field(min_length=1, max_length=MAX_SNIPPET_LENGTH),
]


class SnippetCreate(BaseModel):
    title: Title
    filename: Filename = None
    language: Language = "text"
    content: Content
    description: Description = ""
    visibility: Visibility = "public"


class SnippetUpdate(BaseModel):
    """Fields left out are unchanged."""

    title: Title | None = None
    filename: Filename = None
    language: Language | None = None
    content: Content | None = None
    description: Description | None = None
    visibility: Visibility | None = None


class SnippetOut(BaseModel):
    id: uuid.UUID
    owner: UserSummary
    title: str
    filename: str | None
    language: Language
    content: str
    description: str
    visibility: Visibility
    # Lines of code, for "42 lines" labels without counting on the client.
    line_count: int
    created_at: datetime
    updated_at: datetime


class SnippetPage(BaseModel):
    items: list[SnippetOut]
    next_cursor: uuid.UUID | None
