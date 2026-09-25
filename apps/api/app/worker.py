"""Background jobs.

`python -m app.worker` runs the job runner and its schedule in one process. Run one of it:
two would both fire each scheduled job.
"""

import asyncio

import httpx
import structlog
from taskiq import TaskiqScheduler
from taskiq.api import run_receiver_task, run_scheduler_task
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import ListQueueBroker

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.logging import configure_logging
from app.modules.repos import service as repos

log = structlog.get_logger()

broker = ListQueueBroker(get_settings().redis_url, queue_name="lanterngrid:jobs")
scheduler = TaskiqScheduler(broker, sources=[LabelScheduleSource(broker)])


# Named explicitly: under `python -m` this module is __main__, not app.worker.
@broker.task(task_name="refresh_repos", schedule=[{"cron": "*/15 * * * *"}])
async def refresh_repos() -> int:
    """Keep repo cards' stars and forks fresh (see Settings.repo_refresh_hours)."""
    async with SessionLocal() as db, httpx.AsyncClient(timeout=10) as http:
        return await repos.refresh_stale(db, http)


async def main() -> None:
    await broker.startup()
    log.info("worker.started")
    try:
        await asyncio.gather(run_receiver_task(broker), run_scheduler_task(scheduler))
    finally:
        await broker.shutdown()


if __name__ == "__main__":
    configure_logging(json_logs=get_settings().environment in ("staging", "production"))
    asyncio.run(main())
