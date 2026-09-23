import re
import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, Field, HttpUrl

from app.modules.tags.schemas import TagList, TagOut

USERNAME_PATTERN = r"^[A-Za-z0-9](?:[A-Za-z0-9_-]{1,28}[A-Za-z0-9])$"
_USERNAME_RE = re.compile(USERNAME_PATTERN)

# Names that would collide with routes, or that people could use to impersonate staff.
RESERVED_USERNAMES = frozenset(
    {
        "about", "account", "admin", "administrator", "api", "app", "auth", "blog", "explore",
        "feed", "forgot-password", "help", "home", "kit", "lanterngrid", "login", "logout",
        "me", "messages", "mod", "moderator", "new", "notifications", "onboarding", "privacy",
        "repos", "reset-password", "root", "search", "settings", "signin", "signout", "signup",
        "snippets", "staff", "support", "system", "tags", "terms", "u", "user", "users",
        "verify-email", "www",
    }
)  # fmt: skip

Accent = Literal["cyan", "violet", "lime", "amber", "magenta", "coral"]
LinkKind = Literal[
    "github", "gitlab", "linkedin", "x", "mastodon", "bluesky", "website", "blog", "youtube",
    "other",
]  # fmt: skip
MAX_PROFILE_LINKS = 8
UsernameProblem = Literal["invalid", "reserved", "taken"]


def username_problem(username: str) -> Literal["invalid", "reserved"] | None:
    if not _USERNAME_RE.fullmatch(username):
        return "invalid"
    if username.lower() in RESERVED_USERNAMES:
        return "reserved"
    return None


def _check_username(value: str) -> str:
    match username_problem(value):
        case "invalid":
            raise ValueError(
                "Use 3 to 30 letters, numbers, dashes or underscores, "
                "starting and ending with a letter or number."
            )
        case "reserved":
            raise ValueError("That username is reserved.")
    return value


def _blank_to_none(value: object) -> object:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def _strip(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


def _check_url(value: str) -> str:
    HttpUrl(value)  # raises on anything that isn't an absolute http(s) URL
    return value


Username = Annotated[str, BeforeValidator(_strip), AfterValidator(_check_username)]
DisplayName = Annotated[str, BeforeValidator(_strip), Field(min_length=1, max_length=50)]


# Optional free text: blank becomes null, otherwise capped in length.
Headline = Annotated[Annotated[str, Field(max_length=120)] | None, BeforeValidator(_blank_to_none)]
Bio = Annotated[Annotated[str, Field(max_length=1000)] | None, BeforeValidator(_blank_to_none)]
Location = Annotated[Annotated[str, Field(max_length=80)] | None, BeforeValidator(_blank_to_none)]
LinkUrl = Annotated[
    str, BeforeValidator(_strip), Field(min_length=1, max_length=300), AfterValidator(_check_url)
]
Website = Annotated[
    Annotated[str, Field(max_length=200), AfterValidator(_check_url)] | None,
    BeforeValidator(_blank_to_none),
]


class Me(BaseModel):
    """The signed-in account, as the web app needs it on every page."""

    id: uuid.UUID
    email: str
    email_verified: bool
    username: str | None
    display_name: str
    headline: str | None
    accent_color: Accent
    avatar_url: str | None
    has_password: bool
    github_login: str | None
    created_at: datetime


class ProfileLinkOut(BaseModel):
    kind: LinkKind
    url: str


class ProfileLinkIn(BaseModel):
    kind: LinkKind
    url: LinkUrl


class LinksUpdate(BaseModel):
    """The full list, in display order."""

    links: Annotated[list[ProfileLinkIn], Field(max_length=MAX_PROFILE_LINKS)]


class PublicProfile(BaseModel):
    username: str
    display_name: str
    headline: str | None
    bio: str | None
    location: str | None
    website: str | None
    accent_color: Accent
    avatar_url: str | None
    banner_url: str | None
    links: list[ProfileLinkOut]
    tags: list[TagOut]
    joined_at: datetime


class ProfileSettings(BaseModel):
    display_name: str
    headline: str | None
    bio: str | None
    location: str | None
    website: str | None
    accent_color: Accent
    avatar_url: str | None
    banner_url: str | None
    links: list[ProfileLinkOut]
    tags: list[TagOut]


class ProfileUpdate(BaseModel):
    """Fields left out are unchanged; fields sent as null or blank are cleared."""

    display_name: DisplayName | None = None
    headline: Headline = None
    bio: Bio = None
    location: Location = None
    website: Website = None
    accent_color: Accent | None = None


class OnboardingRequest(BaseModel):
    username: Username
    display_name: DisplayName
    headline: Headline = None
    tags: TagList = []


class UsernameAvailability(BaseModel):
    username: str
    available: bool
    problem: UsernameProblem | None
