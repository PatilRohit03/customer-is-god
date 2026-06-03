from fastapi import APIRouter
from .database import get_session
from .models import Event
from sqlmodel import select
from datetime import datetime, timezone

router = APIRouter()

@router.get('/')
async def health():
    session = get_session()
    last_event = session.exec(select(Event).order_by(Event.timestamp.desc())).first()
    last_timestamp = last_event.timestamp if last_event else None
    stale = False
    if last_timestamp:
        if last_timestamp.tzinfo is None:
            last_timestamp = last_timestamp.replace(tzinfo=timezone.utc)
        stale = (datetime.now(timezone.utc) - last_timestamp).total_seconds() > 600
    return {
        'status': 'ok',
        'last_event_timestamp': last_timestamp,
        'stale_feed': stale,
    }
