from datetime import UTC, datetime, timedelta

from fastapi import Request, Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    hash_password,
    hash_token,
    new_token,
    password_needs_rehash,
    verify_password,
)
from app.core.storage import public_url
from app.modules.auth.models import EmailToken, OAuthAccount, TokenPurpose, UserSession
from app.modules.users.models import Profile, User
from app.modules.users.schemas import Me

TOKEN_TTL: dict[TokenPurpose, timedelta] = {
    "verify_email": timedelta(hours=24),
    "reset_password": timedelta(hours=1),
}


class EmailTakenError(Exception):
    pass


def now() -> datetime:
    return datetime.now(UTC)


# --- accounts -------------------------------------------------------------------------------


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    return (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()


def new_user(email: str, display_name: str, *, password: str | None = None) -> User:
    return User(
        email=email,
        display_name=display_name,
        password_hash=hash_password(password) if password else None,
        profile=Profile(),
    )


async def sign_up(db: AsyncSession, *, email: str, password: str, display_name: str) -> User:
    if await get_by_email(db, email):
        raise EmailTakenError
    user = new_user(email, display_name, password=password)
    db.add(user)
    await db.flush()
    return user


async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_by_email(db, email)
    if not verify_password(user.password_hash if user else None, password):
        return None
    assert user is not None and user.password_hash is not None
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    return user


async def github_login(db: AsyncSession, user: User) -> str | None:
    stmt = select(OAuthAccount.provider_login).where(
        OAuthAccount.user_id == user.id, OAuthAccount.provider == "github"
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def build_me(db: AsyncSession, user: User) -> Me:
    return Me(
        id=user.id,
        email=user.email,
        email_verified=user.email_verified_at is not None,
        username=user.username,
        display_name=user.display_name,
        headline=user.profile.headline,
        accent_color=user.profile.accent_color,
        avatar_url=public_url(user.profile.avatar_key),
        has_password=user.password_hash is not None,
        github_login=await github_login(db, user),
        created_at=user.created_at,
    )


# --- sessions -------------------------------------------------------------------------------


async def create_session(db: AsyncSession, user: User, request: Request) -> str:
    token = new_token()
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=hash_token(token),
            ip=request.client.host if request.client else None,
            user_agent=(request.headers.get("user-agent") or "")[:400] or None,
            expires_at=now() + timedelta(days=get_settings().session_ttl_days),
        )
    )
    return token


async def user_for_session(db: AsyncSession, token: str) -> tuple[User, UserSession] | None:
    row = (
        await db.execute(
            select(User, UserSession)
            .join(UserSession, UserSession.user_id == User.id)
            .where(UserSession.token_hash == hash_token(token), UserSession.expires_at > now())
        )
    ).first()
    return (row[0], row[1]) if row else None


async def end_session(db: AsyncSession, token: str) -> None:
    await db.execute(delete(UserSession).where(UserSession.token_hash == hash_token(token)))


async def end_all_sessions(db: AsyncSession, user: User) -> None:
    await db.execute(delete(UserSession).where(UserSession.user_id == user.id))


def set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_ttl_days * 24 * 3600,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        settings.session_cookie_name,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )


# --- email tokens ---------------------------------------------------------------------------


async def create_email_token(db: AsyncSession, user: User, purpose: TokenPurpose) -> str:
    # Only the newest link of each kind works.
    await db.execute(
        delete(EmailToken).where(
            EmailToken.user_id == user.id,
            EmailToken.purpose == purpose,
            EmailToken.used_at.is_(None),
        )
    )
    token = new_token()
    db.add(
        EmailToken(
            user_id=user.id,
            purpose=purpose,
            token_hash=hash_token(token),
            expires_at=now() + TOKEN_TTL[purpose],
        )
    )
    return token


async def consume_email_token(db: AsyncSession, token: str, purpose: TokenPurpose) -> User | None:
    record = await db.scalar(
        select(EmailToken)
        .where(
            EmailToken.token_hash == hash_token(token),
            EmailToken.purpose == purpose,
            EmailToken.used_at.is_(None),
            EmailToken.expires_at > now(),
        )
        .with_for_update()
    )
    if record is None:
        return None
    record.used_at = now()
    return await db.get(User, record.user_id)


async def reset_password(db: AsyncSession, user: User, password: str) -> None:
    user.password_hash = hash_password(password)
    # Opening the emailed link proves the person controls the address.
    user.email_verified_at = user.email_verified_at or now()
    await end_all_sessions(db, user)
