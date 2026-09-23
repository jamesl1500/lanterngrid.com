from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.modules.health.router import router as health_router

API_PREFIX = "/v1"


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
    app.include_router(health_router, prefix=API_PREFIX)
    return app


app = create_app()
