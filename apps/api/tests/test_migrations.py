import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SessionLocal

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


async def test_migrations_upgrade_and_downgrade_cleanly() -> None:
    config = Config(str(ALEMBIC_INI))
    # env.py drives its own event loop, so run Alembic off this test's loop.
    await asyncio.to_thread(command.upgrade, config, "head")

    session: AsyncSession
    async with SessionLocal() as session:
        result = await session.execute(
            text("select extname from pg_extension where extname in ('citext', 'pg_trgm')")
        )
        assert sorted(result.scalars().all()) == ["citext", "pg_trgm"]

    await asyncio.to_thread(command.downgrade, config, "base")
    await asyncio.to_thread(command.upgrade, config, "head")
