import uuid

from fastapi import APIRouter, HTTPException, status

from app.core.db import SessionDep
from app.modules.auth.deps import MemberDep, OptionalUserDep
from app.modules.pins import service
from app.modules.pins.schemas import MAX_PINS, PinIn, Pins, PinType
from app.modules.users.deps import ProfileOwnerDep

router = APIRouter(tags=["pins"])


@router.get("/users/{username}/pins", operation_id="listPins")
async def list_pins(owner: ProfileOwnerDep, viewer: OptionalUserDep, db: SessionDep) -> Pins:
    return await service.pins(db, viewer, owner)


@router.put("/me/pins/{type}/{item_id}", operation_id="pinItem")
async def pin_item(type: PinType, item_id: uuid.UUID, user: MemberDep, db: SessionDep) -> Pins:
    try:
        return await service.pin(db, user, PinIn(type=type, id=item_id))
    except service.PinNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"That {type} doesn't exist or isn't yours."
        ) from None
    except service.TooManyPinsError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"You can pin up to {MAX_PINS} things. Unpin one first.",
        ) from None


@router.delete("/me/pins/{type}/{item_id}", operation_id="unpinItem")
async def unpin_item(type: PinType, item_id: uuid.UUID, user: MemberDep, db: SessionDep) -> Pins:
    return await service.unpin(db, user, PinIn(type=type, id=item_id))
