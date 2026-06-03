from fastapi import APIRouter, HTTPException
from typing import List
from sqlmodel import select
from .database import get_session
from .models import Event
from .session import create_or_get_session, close_session, mark_billing_seen
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter()

class EventPayload(BaseModel):
    event_id: str
    store_id: str
    camera_id: str
    visitor_id: str
    event_type: str
    timestamp: datetime
    zone_id: str | None = None
    dwell_ms: int | None = None
    is_staff: bool = False
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict | None = None

class BulkIngestRequest(BaseModel):
    events: List[EventPayload]

@router.post('/ingest')
async def ingest_events(payload: BulkIngestRequest):
    inserted = 0
    errors = []
    with get_session() as session:
        for idx, event in enumerate(payload.events):
            try:
                existing = session.exec(select(Event).where(Event.event_id == event.event_id)).first()
                if existing:
                    continue
                event_data = event.model_dump(by_alias=True)
                record = Event(**event_data)
                session.add(record)
                session.commit()
                inserted += 1

                if not event.is_staff:
                    if event.event_type in ('ENTRY', 'REENTRY'):
                        create_or_get_session(event.store_id, event.visitor_id, event.timestamp)
                    elif event.event_type == 'EXIT':
                        close_session(event.store_id, event.visitor_id, event.timestamp)
                    elif event.event_type == 'BILLING_QUEUE_JOIN':
                        mark_billing_seen(event.store_id, event.visitor_id, event.timestamp)
            except Exception as exc:
                session.rollback()
                errors.append({
                    'index': idx,
                    'event_id': getattr(event, 'event_id', None),
                    'error': str(exc),
                })
    return {
        'inserted': inserted,
        'errors': errors,
        'received': len(payload.events),
    }
