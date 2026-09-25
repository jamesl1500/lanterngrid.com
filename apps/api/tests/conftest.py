"""Test setup: a separate database and Redis db, so running tests never touches dev data.

Environment variables are set before any app module is imported, because settings and the
database engine are created at import time.
"""

import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import asyncpg
from sqlalchemy.engine import make_url

os.environ["ENVIRONMENT"] = "test"
os.environ["EMAIL_BACKEND"] = "memory"
os.environ["WEB_URL"] = "http://testserver"
os.environ["CORS_ORIGINS"] = "http://testserver"
os.environ["GITHUB_CLIENT_ID"] = "test-client-id"
os.environ["GITHUB_CLIENT_SECRET"] = "test-client-secret"

_dev_db = make_url(
    os.environ.get(
        "DATABASE_URL", "postgresql+asyncpg://lanterngrid:lanterngrid@localhost:5432/lanterngrid"
    )
)
TEST_DB_URL = (
    make_url(os.environ["TEST_DATABASE_URL"])
    if os.environ.get("TEST_DATABASE_URL")
    else _dev_db.set(database=f"{_dev_db.database}_test")
)
os.environ["DATABASE_URL"] = TEST_DB_URL.render_as_string(hide_password=False)
_redis = os.environ.get("REDIS_URL", "redis://localhost:6379/0").rsplit("/", 1)[0]
os.environ["REDIS_URL"] = f"{_redis}/15"


async def _ensure_database() -> None:
    conn = await asyncpg.connect(
        user=TEST_DB_URL.username,
        password=TEST_DB_URL.password,
        host=TEST_DB_URL.host,
        port=TEST_DB_URL.port,
        database="postgres",
    )
    try:
        exists = await conn.fetchval(
            "select 1 from pg_database where datname = $1", TEST_DB_URL.database
        )
        if not exists:
            await conn.execute(f'create database "{TEST_DB_URL.database}"')
    finally:
        await conn.close()


asyncio.run(_ensure_database())

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.db import Base, engine  # noqa: E402
from app.core.email import outbox  # noqa: E402
from app.core.redis import redis  # noqa: E402
from app.core.storage import get_storage  # noqa: E402
from app.main import app  # noqa: E402
from tests.fakes import FakeStorage  # noqa: E402

# Seeded by migrations; tests remove only the rows they add.
KEEP_TABLES = frozenset({"tags"})


@pytest.fixture(autouse=True)
async def clean_state() -> AsyncIterator[None]:
    yield
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables if t.name not in KEEP_TABLES)
    async with engine.begin() as conn:
        await conn.execute(text(f"truncate {tables} cascade"))
        await conn.execute(text("delete from tags where not curated"))
    await redis.flushdb()
    outbox.clear()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
        yield c


@pytest.fixture(autouse=True)
def storage() -> Iterator[FakeStorage]:
    fake = FakeStorage()
    app.dependency_overrides[get_storage] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_storage, None)
