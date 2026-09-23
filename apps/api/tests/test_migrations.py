import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.core.db import engine

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


async def test_migrations_downgrade_and_upgrade_cleanly() -> None:
    config = Config(str(ALEMBIC_INI))
    # env.py drives its own event loop, so run Alembic off this test's loop.
    await asyncio.to_thread(command.downgrade, config, "base")
    await asyncio.to_thread(command.upgrade, config, "head")
    # Recreated extensions get new type ids; drop pooled connections that cached the old ones.
    await engine.dispose()

    async with engine.connect() as conn:
        result = await conn.execute(
            text("select extname from pg_extension where extname in ('citext', 'pg_trgm')")
        )
        assert sorted(result.scalars().all()) == ["citext", "pg_trgm"]
