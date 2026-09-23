from typing import Literal

from pydantic import BaseModel

CheckStatus = Literal["ok", "down"]


class HealthChecks(BaseModel):
    database: CheckStatus
    redis: CheckStatus


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    checks: HealthChecks
