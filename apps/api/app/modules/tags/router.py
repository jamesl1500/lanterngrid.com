from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.core.db import SessionDep
from app.modules.auth.deps import CurrentUserDep
from app.modules.tags import service
from app.modules.tags.schemas import TagOut, TagsUpdate

router = APIRouter(tags=["tags"])


@router.get("/tags/suggest", operation_id="suggestTags")
async def suggest_tags(
    db: SessionDep,
    q: Annotated[str, Query(max_length=32)] = "",
    limit: Annotated[int, Query(ge=1, le=20)] = 8,
) -> list[TagOut]:
    return await service.suggest(db, q, limit)


@router.put("/me/tags", operation_id="setMyTags")
async def set_my_tags(data: TagsUpdate, user: CurrentUserDep, db: SessionDep) -> list[TagOut]:
    await service.set_user_tags(db, user.id, data.tags)
    await db.commit()
    return await service.user_tags(db, user.id)


# Registered after /tags/suggest so "suggest" isn't read as a slug.
@router.get("/tags/{slug}", operation_id="getTag")
async def get_tag(slug: str, db: SessionDep) -> TagOut:
    tag = await service.get(db, slug)
    if tag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such tag.")
    return service.to_out(tag)
