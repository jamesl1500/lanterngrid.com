import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.core.db import SessionDep
from app.modules.auth.deps import CurrentUserDep
from app.modules.notifications import service
from app.modules.notifications.schemas import MarkRead, NotificationPage, UnreadCount

router = APIRouter(tags=["notifications"])


@router.get("/me/notifications", operation_id="listNotifications")
async def list_notifications(
    user: CurrentUserDep,
    db: SessionDep,
    cursor: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> NotificationPage:
    return await service.page(db, user.id, cursor=cursor, limit=limit)


@router.get("/me/notifications/unread-count", operation_id="getUnreadNotificationCount")
async def get_unread_count(user: CurrentUserDep, db: SessionDep) -> UnreadCount:
    return UnreadCount(count=await service.unread_count(db, user.id))


@router.post("/me/notifications/read", operation_id="markNotificationsRead")
async def mark_notifications_read(
    data: MarkRead, user: CurrentUserDep, db: SessionDep
) -> UnreadCount:
    await service.mark_read(db, user.id, data.up_to)
    await db.commit()
    return UnreadCount(count=await service.unread_count(db, user.id))
