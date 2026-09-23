from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__, models  # noqa: F401  (registers every model)
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.modules.auth.router import router as auth_router
from app.modules.health.router import router as health_router
from app.modules.users.router import router as users_router

API_PREFIX = "/v1"
UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(json_logs=settings.environment in ("staging", "production"))

    app = FastAPI(title="Lantern Grid API", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def reject_cross_site_writes(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Session cookies are SameSite=Lax; this closes the remaining gap for writes that
        # come from a page on another site.
        origin = request.headers.get("origin")
        if (
            request.method in UNSAFE_METHODS
            and origin is not None
            and origin not in settings.trusted_origins
        ):
            return JSONResponse(
                {"detail": "Cross-site request blocked."}, status_code=status.HTTP_403_FORBIDDEN
            )
        return await call_next(request)

    for router in (health_router, auth_router, users_router):
        app.include_router(router, prefix=API_PREFIX)
    return app


app = create_app()
