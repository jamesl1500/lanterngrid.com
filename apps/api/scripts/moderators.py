"""Give someone the moderator role, take it away, or list who has it.

python -m scripts.moderators list
python -m scripts.moderators grant <username>
python -m scripts.moderators revoke <username>
"""

import asyncio
import sys

from sqlalchemy import select

from app import models  # noqa: F401  (registers every model)
from app.core.db import SessionLocal, engine
from app.modules.users.models import User

USAGE = "usage: python -m scripts.moderators list | grant <username> | revoke <username>"


async def run(args: list[str]) -> str:
    async with SessionLocal() as db:
        match args:
            case ["list"]:
                names = await db.scalars(
                    select(User.username).where(User.is_moderator).order_by(User.username)
                )
                return "\n".join(str(n) for n in names) or "no moderators yet"
            case ["grant" | "revoke" as action, username]:
                user = await db.scalar(select(User).where(User.username == username))
                if user is None:
                    raise SystemExit(f"no one is called @{username}")
                user.is_moderator = action == "grant"
                await db.commit()
                return (
                    f"@{user.username} is {'now' if user.is_moderator else 'no longer'} a moderator"
                )
            case _:
                raise SystemExit(USAGE)


async def main() -> None:
    try:
        print(await run(sys.argv[1:]))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
