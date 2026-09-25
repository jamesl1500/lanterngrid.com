"""The realtime socket: pushes messages, read receipts and conversation changes.

Browsers can't send the session cookie to the API's own domain, so they swap it for a
one-time ticket over the same-origin /api proxy first.
"""

import asyncio
import contextlib
import hashlib
import json
import secrets
import uuid

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.config import get_settings
from app.core.redis import redis
from app.modules.auth.deps import MemberDep
from app.modules.realtime import bus
from app.modules.realtime.schemas import RealtimeTicket

router = APIRouter(tags=["realtime"])
log = structlog.get_logger()

TICKET_SECONDS = 60
# Close codes in the 4000s are ours; the browser reconnects with a new ticket.
CLOSE_BAD_TICKET = 4401
CLOSE_BAD_ORIGIN = 4403


def _ticket_key(ticket: str) -> str:
    return f"rt:ticket:{hashlib.sha256(ticket.encode()).hexdigest()}"


@router.post("/realtime/ticket", operation_id="createRealtimeTicket")
async def create_ticket(user: MemberDep) -> RealtimeTicket:
    ticket = secrets.token_urlsafe(32)
    await redis.set(_ticket_key(ticket), str(user.id), ex=TICKET_SECONDS)
    return RealtimeTicket(ticket=ticket, url=get_settings().realtime_url)


async def _forward(ws: WebSocket, user_id: uuid.UUID) -> None:
    async with redis.pubsub() as pubsub:
        await pubsub.subscribe(bus.channel(user_id))
        await ws.send_json({"type": "ready"})
        async for message in pubsub.listen():
            if message["type"] == "message":
                await ws.send_text(message["data"])


async def _receive(ws: WebSocket) -> None:
    while True:
        data = await ws.receive_text()
        with contextlib.suppress(ValueError):
            if json.loads(data).get("type") == "ping":
                await ws.send_json({"type": "pong"})


@router.websocket("/realtime")
async def realtime(ws: WebSocket, ticket: str = "") -> None:
    origin = ws.headers.get("origin")
    if origin is not None and origin not in get_settings().trusted_origins:
        await ws.close(code=CLOSE_BAD_ORIGIN)
        return
    user_id = await redis.getdel(_ticket_key(ticket)) if ticket else None
    if user_id is None:
        await ws.close(code=CLOSE_BAD_TICKET)
        return
    await ws.accept()
    tasks = [
        asyncio.create_task(_forward(ws, uuid.UUID(str(user_id)))),
        asyncio.create_task(_receive(ws)),
    ]
    try:
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            if (error := task.exception()) and not isinstance(error, WebSocketDisconnect):
                log.warning("realtime.socket_failed", error=repr(error))
    finally:
        for task in tasks:
            task.cancel()
        with contextlib.suppress(Exception):
            await ws.close(code=status.WS_1000_NORMAL_CLOSURE)
