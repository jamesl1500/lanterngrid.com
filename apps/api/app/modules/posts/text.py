"""Pull #tags and @mentions out of a post's Markdown, ignoring anything inside code."""

import re

from app.modules.tags.schemas import MAX_TAG_LENGTH, slugify
from app.modules.users.schemas import username_problem

MAX_TAGS_PER_POST = 10
MAX_MENTIONS_PER_POST = 10

_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})[^\n]*\n.*?(?:^ {0,3}\1[ \t]*$|\Z)", re.M | re.S)
_INLINE_CODE = re.compile(r"(`+)(?!`).+?(?<!`)\1(?!`)", re.S)
# A tag starts with a letter so "#1" and "issue #42" aren't tags.
HASHTAG = re.compile(r"(?<![\w#&/])#([A-Za-z][A-Za-z0-9_+#.-]*)")
MENTION = re.compile(r"(?<![\w@/.])@([A-Za-z0-9][A-Za-z0-9_-]*[A-Za-z0-9])")


def strip_code(markdown: str) -> str:
    return _INLINE_CODE.sub(" ", _FENCE.sub("\n", markdown))


def hashtags(markdown: str) -> list[str]:
    """Tag names as written, in order, deduplicated by slug."""
    seen: set[str] = set()
    names: list[str] = []
    for match in HASHTAG.finditer(strip_code(markdown)):
        # Sentence punctuation isn't part of the tag: "I like #rust." -> "rust".
        name = match.group(1).rstrip(".-")[:MAX_TAG_LENGTH]
        slug = slugify(name)
        if slug and slug not in seen:
            seen.add(slug)
            names.append(name)
    return names[:MAX_TAGS_PER_POST]


def mentions(markdown: str) -> list[str]:
    """Usernames mentioned, lowercased, in order, deduplicated."""
    seen: list[str] = []
    for match in MENTION.finditer(strip_code(markdown)):
        username = match.group(1).lower()
        if username_problem(username) != "invalid" and username not in seen:
            seen.append(username)
    return seen[:MAX_MENTIONS_PER_POST]
