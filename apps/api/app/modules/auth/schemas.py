from typing import Annotated

from pydantic import BaseModel, BeforeValidator, EmailStr, Field

from app.modules.users.schemas import DisplayName

Password = Annotated[str, Field(min_length=10, max_length=128)]


def _lower_strip(value: object) -> object:
    return value.strip().lower() if isinstance(value, str) else value


Email = Annotated[EmailStr, BeforeValidator(_lower_strip)]


class SignUpRequest(BaseModel):
    email: Email
    password: Password
    display_name: DisplayName


class SignInRequest(BaseModel):
    email: Email
    # Only length-capped here, so a password set under older rules still works.
    password: Annotated[str, Field(min_length=1, max_length=128)]


class VerifyEmailRequest(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    email: Email


class PasswordResetConfirm(BaseModel):
    token: str
    password: Password


class AuthProviders(BaseModel):
    github: bool
