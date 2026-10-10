import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.core.db import SessionDep
from app.core.storage import StorageDep
from app.modules.auth.deps import MemberDep, ModeratorDep
from app.modules.auth.limits import limit_writes
from app.modules.moderation import service
from app.modules.moderation.schemas import (
    CaseOut,
    CasePage,
    CaseResolve,
    ModerationSummary,
    QueueFilter,
    ReportCreate,
)

router = APIRouter(tags=["moderation"])

Limit = Annotated[int, Query(ge=1, le=50)]


@router.post("/reports", operation_id="createReport", status_code=status.HTTP_204_NO_CONTENT)
async def create_report(data: ReportCreate, user: MemberDep, db: SessionDep) -> None:
    """Flag something for moderators. The person reported isn't told who reported them."""
    await limit_writes(user, "report")
    try:
        await service.report(db, user, data)
    except service.SubjectNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "That doesn't exist anymore, or you can't see it."
        ) from None
    except service.OwnSubjectError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "You can't report yourself or your own things."
        ) from None


@router.get("/moderation/summary", operation_id="getModerationSummary")
async def get_summary(user: ModeratorDep, db: SessionDep) -> ModerationSummary:
    return ModerationSummary(open_cases=await service.open_count(db))


@router.get("/moderation/cases", operation_id="listModerationCases")
async def list_cases(
    user: ModeratorDep,
    db: SessionDep,
    status: QueueFilter = "open",
    cursor: uuid.UUID | None = None,
    limit: Limit = 20,
) -> CasePage:
    return await service.queue(db, status, cursor=cursor, limit=limit)


@router.post("/moderation/cases/{case_id}/resolve", operation_id="resolveModerationCase")
async def resolve_case(
    case_id: uuid.UUID, data: CaseResolve, user: ModeratorDep, db: SessionDep, storage: StorageDep
) -> CaseOut:
    try:
        return await service.resolve(db, storage, user, case_id, data)
    except service.CaseNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such case.") from None
    except service.CaseClosedError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Another moderator already closed this case."
        ) from None
    except service.ActionError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from None


@router.delete(
    "/moderation/suspensions/{user_id}",
    operation_id="liftSuspension",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def lift_suspension(user_id: uuid.UUID, user: ModeratorDep, db: SessionDep) -> None:
    try:
        await service.lift_suspension(db, user_id)
    except service.SubjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such account.") from None
