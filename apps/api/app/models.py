"""Import every model so Base.metadata is complete for Alembic and tests."""

from app.modules.auth.models import EmailToken, OAuthAccount, UserSession
from app.modules.users.models import Profile, User

__all__ = ["EmailToken", "OAuthAccount", "Profile", "User", "UserSession"]
