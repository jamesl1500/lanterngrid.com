"""Import every model so Base.metadata is complete for Alembic and tests."""

from app.modules.auth.models import EmailToken, OAuthAccount, UserSession
from app.modules.notifications.models import Notification
from app.modules.posts.models import Comment, Mention, Post, PostImage, PostTag, Reaction
from app.modules.snippets.models import Pin, Snippet
from app.modules.social.models import Block, FriendRequest, Friendship
from app.modules.tags.models import Tag, UserTag
from app.modules.users.models import Profile, ProfileLink, User

__all__ = [
    "Block",
    "Comment",
    "EmailToken",
    "FriendRequest",
    "Friendship",
    "Mention",
    "Notification",
    "OAuthAccount",
    "Pin",
    "Post",
    "PostImage",
    "PostTag",
    "Profile",
    "ProfileLink",
    "Reaction",
    "Snippet",
    "Tag",
    "User",
    "UserSession",
    "UserTag",
]
