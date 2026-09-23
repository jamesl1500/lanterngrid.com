"""Import every model so Base.metadata is complete for Alembic and tests."""

from app.modules.auth.models import EmailToken, OAuthAccount, UserSession
from app.modules.tags.models import Tag, UserTag
from app.modules.users.models import Profile, ProfileLink, User

__all__ = [
    "EmailToken",
    "OAuthAccount",
    "Profile",
    "ProfileLink",
    "Tag",
    "User",
    "UserSession",
    "UserTag",
]
