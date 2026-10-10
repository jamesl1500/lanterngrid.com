"""How often one account may make each kind of write.

Accounts that haven't verified their email get the smaller `unverified` number. A real person
rarely notices, but a script making throwaway accounts gets much less out of each one.
"""

from dataclasses import dataclass
from typing import Literal

from app.core.rate_limit import DAY, HOUR, MINUTE, Rule, enforce
from app.modules.users.models import User

WriteAction = Literal[
    "post", "edit", "comment", "reaction", "friend_request", "conversation", "message", "snippet",
    "repo", "upload", "profile", "report",
]  # fmt: skip


@dataclass(frozen=True)
class WriteLimit:
    rule: Rule
    unverified: int


WRITE_LIMITS: dict[WriteAction, WriteLimit] = {
    "post": WriteLimit(Rule(30, HOUR, "That's a lot of posts for one hour. Try later."), 5),
    # Changing posts and snippets.
    "edit": WriteLimit(Rule(120, HOUR, "That's a lot of edits for one hour. Try later."), 30),
    "comment": WriteLimit(Rule(120, HOUR, "That's a lot of comments for one hour. Try later."), 20),
    "reaction": WriteLimit(Rule(600, HOUR, "You're reacting very fast. Slow down a bit."), 100),
    "friend_request": WriteLimit(
        Rule(50, DAY, "That's a lot of requests for one day. Try tomorrow."), 10
    ),
    # Starting conversations and adding people to groups.
    "conversation": WriteLimit(
        Rule(30, HOUR, "That's a lot of new conversations for one hour. Try later."), 5
    ),
    "message": WriteLimit(
        Rule(60, MINUTE, "You're sending messages very fast. Slow down a bit."), 20
    ),
    "snippet": WriteLimit(Rule(30, HOUR, "That's a lot of snippets for one hour. Try later."), 10),
    "repo": WriteLimit(Rule(30, HOUR, "That's a lot of repos for one hour. Try later."), 10),
    "upload": WriteLimit(Rule(30, HOUR, "Too many uploads. Try later."), 10),
    # Profile, links, tags, README and layout changes.
    "profile": WriteLimit(
        Rule(120, HOUR, "You're changing your profile very often. Try later."), 30
    ),
    "report": WriteLimit(
        Rule(30, DAY, "That's a lot of reports for one day. Moderators will get to them."), 10
    ),
}


async def limit_writes(user: User, action: WriteAction) -> None:
    """Count one write by this person; raises 429 once they've made too many."""
    write = WRITE_LIMITS[action]
    rule = write.rule
    if user.email_verified_at is None:
        rule = Rule(
            write.unverified,
            rule.window_seconds,
            f"{rule.message} Verify your email to raise this limit.",
        )
    await enforce(f"{action}:{user.id}", rule)
