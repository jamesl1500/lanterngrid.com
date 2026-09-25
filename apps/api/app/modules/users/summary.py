from app.core.storage import public_url
from app.modules.users.models import User
from app.modules.users.schemas import UserSummary


def summarize(user: User) -> UserSummary:
    """The small card other features show for a person: name, handle, avatar."""
    assert user.username is not None, "only onboarded users appear to others"
    return UserSummary(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        headline=user.profile.headline,
        avatar_url=public_url(user.profile.avatar_key),
        accent_color=user.profile.accent_color,
    )
