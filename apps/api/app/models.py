"""Import every model so Base.metadata is complete for Alembic and tests."""

from app.modules.auth.models import EmailToken, OAuthAccount, UserSession
from app.modules.messaging.models import Conversation, ConversationMember, Message
from app.modules.notifications.models import Notification
from app.modules.pins.models import Pin
from app.modules.posts.models import Comment, Mention, Post, PostImage, PostTag, Reaction
from app.modules.repos.models import Repo
from app.modules.snippets.models import Snippet
from app.modules.social.models import Block, FriendRequest, Friendship
from app.modules.tags.models import Tag, UserTag
from app.modules.users.models import Profile, ProfileLink, User

__all__ = [
    "Block",
    "Comment",
    "Conversation",
    "ConversationMember",
    "EmailToken",
    "FriendRequest",
    "Friendship",
    "Mention",
    "Message",
    "Notification",
    "OAuthAccount",
    "Pin",
    "Post",
    "PostImage",
    "PostTag",
    "Profile",
    "ProfileLink",
    "Reaction",
    "Repo",
    "Snippet",
    "Tag",
    "User",
    "UserSession",
    "UserTag",
]
