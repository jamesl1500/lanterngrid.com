import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, Field, model_validator

from app.modules.users.schemas import UserSummary

SubjectKind = Literal["post", "comment", "snippet", "message", "user"]
ReportReason = Literal["spam", "harassment", "hate", "explicit", "impersonation", "other"]
CaseStatus = Literal["open", "dismissed", "removed", "suspended"]
# dismiss: nothing wrong. remove: delete the reported thing. suspend: suspend its author,
# which hides everything they wrote and closes their other open cases.
CaseAction = Literal["dismiss", "remove", "suspend"]
QueueFilter = Literal["open", "closed"]

# Long posts and snippets are cut down to this for the queue.
MAX_SNAPSHOT = 4000


def _blank_to_none(value: object) -> object:
    if isinstance(value, str):
        return value.strip() or None
    return value


Details = Annotated[Annotated[str, Field(max_length=1000)] | None, BeforeValidator(_blank_to_none)]
Note = Annotated[Annotated[str, Field(max_length=500)] | None, BeforeValidator(_blank_to_none)]


class ReportCreate(BaseModel):
    subject_kind: SubjectKind
    subject_id: uuid.UUID
    reason: ReportReason
    details: Details = None

    @model_validator(mode="after")
    def _explain_other(self) -> "ReportCreate":
        if self.reason == "other" and self.details is None:
            raise ValueError("Say what's wrong so a moderator knows what to look for.")
        return self


class ReportOut(BaseModel):
    id: uuid.UUID
    reporter: UserSummary
    reason: ReportReason
    details: str | None
    created_at: datetime


class CaseOut(BaseModel):
    id: uuid.UUID
    subject_kind: SubjectKind
    subject_id: uuid.UUID
    # Null once the author's account is gone.
    subject_author: UserSummary | None
    author_suspended: bool
    # The post a comment is on.
    post_id: uuid.UUID | None
    # The reported text when it was first reported.
    snapshot: str
    # True when the thing has since been deleted, by its author or a moderator.
    subject_gone: bool
    status: CaseStatus
    report_count: int
    # The latest reports first.
    reports: list[ReportOut]
    created_at: datetime
    resolved_at: datetime | None
    resolved_by: UserSummary | None
    note: str | None


class CasePage(BaseModel):
    items: list[CaseOut]
    # Pass as `cursor` to get the next (older) page; null when there are no more.
    next_cursor: uuid.UUID | None


class CaseResolve(BaseModel):
    action: CaseAction
    note: Note = None


class ModerationSummary(BaseModel):
    open_cases: int
