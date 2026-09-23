import secrets
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Cookie, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import SessionDep
from app.core.email import send_email
from app.core.rate_limit import allow
from app.modules.auth import github, service
from app.modules.auth.deps import CurrentUserDep, OptionalUserDep
from app.modules.auth.emails import password_reset_email, verification_email
from app.modules.auth.models import OAuthAccount
from app.modules.auth.schemas import (
    AuthProviders,
    PasswordResetConfirm,
    PasswordResetRequest,
    SignInRequest,
    SignUpRequest,
    VerifyEmailRequest,
)
from app.modules.users.models import User
from app.modules.users.schemas import Me

router = APIRouter(prefix="/auth", tags=["auth"])

OAUTH_STATE_COOKIE = "lg_oauth_state"


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _safe_next(path: str | None) -> str | None:
    """Only same-site paths, so the redirect after sign-in can't send people elsewhere."""
    if path and path.startswith("/") and not path.startswith("//") and "\\" not in path:
        return path
    return None


@router.get("/providers", operation_id="getAuthProviders")
async def get_providers() -> AuthProviders:
    return AuthProviders(github=get_settings().github_enabled)


@router.get("/me", operation_id="getMe")
async def get_me(user: CurrentUserDep, db: SessionDep) -> Me:
    return await service.build_me(db, user)


@router.post("/signup", operation_id="signUp", status_code=status.HTTP_201_CREATED)
async def sign_up(
    data: SignUpRequest,
    request: Request,
    response: Response,
    background: BackgroundTasks,
    db: SessionDep,
) -> Me:
    if not await allow(f"signup:{_client_ip(request)}", limit=10, window_seconds=3600):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many sign-ups. Try later.")
    try:
        user = await service.sign_up(
            db, email=data.email, password=data.password, display_name=data.display_name
        )
    except service.EmailTakenError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "An account with this email already exists."
        ) from None
    verify_token = await service.create_email_token(db, user, "verify_email")
    session_token = await service.create_session(db, user, request)
    await db.commit()
    service.set_session_cookie(response, session_token)
    background.add_task(send_email, verification_email(user.email, user.display_name, verify_token))
    return await service.build_me(db, user)


@router.post("/signin", operation_id="signIn")
async def sign_in(data: SignInRequest, request: Request, response: Response, db: SessionDep) -> Me:
    if not await allow(f"signin:{data.email}", limit=10, window_seconds=900):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many sign-in attempts for this email. Wait 15 minutes or reset your password.",
        )
    user = await service.authenticate(db, data.email, data.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "That email and password don't match.")
    token = await service.create_session(db, user, request)
    await db.commit()
    service.set_session_cookie(response, token)
    return await service.build_me(db, user)


@router.post("/signout", operation_id="signOut", status_code=status.HTTP_204_NO_CONTENT)
async def sign_out(request: Request, response: Response, db: SessionDep) -> None:
    token = request.cookies.get(get_settings().session_cookie_name)
    if token:
        await service.end_session(db, token)
        await db.commit()
    service.clear_session_cookie(response)


@router.post(
    "/signout-everywhere", operation_id="signOutEverywhere", status_code=status.HTTP_204_NO_CONTENT
)
async def sign_out_everywhere(user: CurrentUserDep, response: Response, db: SessionDep) -> None:
    await service.end_all_sessions(db, user)
    await db.commit()
    service.clear_session_cookie(response)


@router.post("/verify-email", operation_id="verifyEmail")
async def verify_email(data: VerifyEmailRequest, db: SessionDep) -> Me:
    user = await service.consume_email_token(db, data.token, "verify_email")
    if user is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "This link has expired or was already used."
        )
    user.email_verified_at = user.email_verified_at or service.now()
    await db.commit()
    return await service.build_me(db, user)


@router.post(
    "/verify-email/resend", operation_id="resendVerification", status_code=status.HTTP_202_ACCEPTED
)
async def resend_verification(
    user: CurrentUserDep, background: BackgroundTasks, db: SessionDep
) -> None:
    if user.email_verified_at is not None:
        return
    if not await allow(f"verify-resend:{user.id}", limit=5, window_seconds=3600):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many emails. Try later.")
    token = await service.create_email_token(db, user, "verify_email")
    await db.commit()
    background.add_task(send_email, verification_email(user.email, user.display_name, token))


@router.post(
    "/password-reset", operation_id="requestPasswordReset", status_code=status.HTTP_202_ACCEPTED
)
async def request_password_reset(
    data: PasswordResetRequest, background: BackgroundTasks, db: SessionDep
) -> None:
    # Same response whether or not the account exists, so this can't be used to probe emails.
    if not await allow(f"reset:{data.email}", limit=5, window_seconds=3600):
        return
    user = await service.get_by_email(db, data.email)
    if user is None:
        return
    token = await service.create_email_token(db, user, "reset_password")
    await db.commit()
    background.add_task(send_email, password_reset_email(user.email, user.display_name, token))


@router.post(
    "/password-reset/confirm",
    operation_id="confirmPasswordReset",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def confirm_password_reset(data: PasswordResetConfirm, db: SessionDep) -> None:
    user = await service.consume_email_token(db, data.token, "reset_password")
    if user is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "This link has expired or was already used."
        )
    await service.reset_password(db, user, data.password)
    await db.commit()


# --- GitHub ---------------------------------------------------------------------------------


@router.get("/github/start", operation_id="startGitHubSignIn", include_in_schema=False)
async def github_start(next: str | None = None) -> RedirectResponse:
    settings = get_settings()
    if not settings.github_enabled:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "GitHub sign-in isn't set up.")
    state = secrets.token_urlsafe(24)
    response = RedirectResponse(github.authorize_url(state), status.HTTP_302_FOUND)
    response.set_cookie(
        OAUTH_STATE_COOKIE,
        f"{state}|{_safe_next(next) or ''}",
        max_age=600,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )
    return response


@router.get("/github/callback", operation_id="finishGitHubSignIn", include_in_schema=False)
async def github_callback(
    request: Request,
    db: SessionDep,
    http: github.GitHubHttpDep,
    current: OptionalUserDep,
    code: str | None = None,
    state: str | None = None,
    oauth_state: Annotated[str | None, Cookie(alias=OAUTH_STATE_COOKIE)] = None,
) -> RedirectResponse:
    web = get_settings().web_url

    def fail(reason: str) -> RedirectResponse:
        # Someone connecting GitHub from settings goes back there; everyone else to sign-in.
        page = "/settings/account" if current is not None else "/signin"
        response = RedirectResponse(f"{web}{page}?error={reason}", status.HTTP_302_FOUND)
        response.delete_cookie(OAUTH_STATE_COOKIE, path="/")
        return response

    expected_state, _, next_path = (oauth_state or "").partition("|")
    if not code or not state or not secrets.compare_digest(state, expected_state or "\0"):
        return fail("github_state")
    try:
        gh_user = await github.fetch_user(http, await github.exchange_code(http, code))
    except (github.GitHubError, ValueError, KeyError):
        return fail("github_failed")

    account = await db.scalar(
        select(OAuthAccount).where(
            OAuthAccount.provider == "github", OAuthAccount.provider_user_id == str(gh_user.id)
        )
    )
    user: User | None
    if account is not None:
        user = await db.get(User, account.user_id)
        account.provider_login = gh_user.login
    else:
        if current is not None:
            # Signed in already: this connects GitHub to the current account.
            user = current
        elif gh_user.verified_email is None:
            return fail("github_email")
        else:
            user = await service.get_by_email(db, gh_user.verified_email)
            if user is None:
                user = service.new_user(gh_user.verified_email, gh_user.name or gh_user.login)
                db.add(user)
                await db.flush()
            # GitHub verified this address, so it counts as verified here too.
            user.email_verified_at = user.email_verified_at or service.now()
        if await github_already_linked(db, user):
            return fail("github_other_account")
        db.add(
            OAuthAccount(
                user_id=user.id,
                provider="github",
                provider_user_id=str(gh_user.id),
                provider_login=gh_user.login,
            )
        )
    assert user is not None

    token = await service.create_session(db, user, request) if current is None else None
    await db.commit()

    if user.username is None:
        destination = f"/onboarding?suggested={gh_user.login}"
    else:
        destination = _safe_next(next_path) or "/"
    response = RedirectResponse(f"{web}{destination}", status.HTTP_302_FOUND)
    response.delete_cookie(OAUTH_STATE_COOKIE, path="/")
    if token:
        service.set_session_cookie(response, token)
    return response


async def github_already_linked(db: SessionDep, user: User) -> bool:
    return await service.github_login(db, user) is not None
