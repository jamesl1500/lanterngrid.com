from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.core.db import SessionDep
from app.core.redis import redis
from app.modules.health.schemas import CheckStatus, HealthChecks, HealthResponse

router = APIRouter(tags=["health"])


async def _check_database(session: AsyncSession) -> CheckStatus:
    try:
        await session.execute(text("select 1"))
    except Exception:
        return "down"
    return "ok"


async def _check_redis() -> CheckStatus:
    try:
        await redis.ping()
    except Exception:
        return "down"
    return "ok"


@router.get("/health", operation_id="getHealth")
async def get_health(session: SessionDep) -> HealthResponse:
    checks = HealthChecks(database=await _check_database(session), redis=await _check_redis())
    healthy = checks.database == "ok" and checks.redis == "ok"
    return HealthResponse(
        status="ok" if healthy else "degraded", version=__version__, checks=checks
    )
