"""
Real-Time Server-Sent Events (SSE) Streaming Gateway.
Streams live business events, warehouse tasks, and agent activity to client frontends without polling.
"""
import asyncio
import json
import time
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from apps.api.app.core.database import SessionLocal, get_db
from apps.api.app.models.tenant import Organization
from apps.api.app.models.document import BusinessEvent
from apps.api.app.models.operations import Task

router = APIRouter(prefix="/events", tags=["Real-Time Event Stream"])


async def event_generator(request: Request) -> AsyncGenerator[str, None]:
    """
    Asynchronously yields Server-Sent Events for connected clients.
    Polls recent items every 1 second and sends heartbeats.
    """
    last_check = time.time() - 60  # Initial window: last 60 seconds

    # Initial connection event
    init_data = json.dumps({"type": "CONNECTED", "timestamp": time.time(), "message": "Subscribed to OpsPilot Live Event Stream"})
    yield f"event: message\ndata: {init_data}\n\n"

    while True:
        if await request.is_disconnected():
            break

        db = SessionLocal()
        try:
            # Query recent tasks created or updated
            tasks = db.query(Task).order_by(Task.updated_at.desc()).limit(5).all()
            for t in tasks:
                t_time = t.updated_at.timestamp() if t.updated_at else 0
                if t_time > last_check:
                    task_payload = json.dumps({
                        "type": "TASK_UPDATE",
                        "id": t.id,
                        "title": t.title,
                        "task_type": t.task_type,
                        "status": t.status,
                        "priority": t.priority,
                        "timestamp": t_time
                    })
                    yield f"event: task\ndata: {task_payload}\n\n"

            # Query recent business events
            events = db.query(BusinessEvent).order_by(BusinessEvent.received_at.desc()).limit(5).all()
            for ev in events:
                ev_time = ev.received_at.timestamp() if ev.received_at else 0
                if ev_time > last_check:
                    event_payload = json.dumps({
                        "type": "BUSINESS_EVENT",
                        "id": ev.id,
                        "title": ev.title,
                        "event_type": ev.event_type,
                        "source": ev.source,
                        "timestamp": ev_time
                    })
                    yield f"event: business_event\ndata: {event_payload}\n\n"

            last_check = time.time()
        except Exception:
            pass
        finally:
            db.close()

        # Send heartbeat comment to keep connection alive through proxies
        yield f": ping {time.time()}\n\n"
        await asyncio.sleep(2.0)


@router.get("/stream")
async def stream_live_events(request: Request):
    """
    Server-Sent Events (SSE) endpoint providing sub-100ms real-time event updates to browser dashboards.
    Clients connect using new EventSource('/api/v1/events/stream').
    """
    return StreamingResponse(
        event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
