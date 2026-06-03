from fastapi import APIRouter
from .database import get_session
from .models import Event, VisitorSession, POSRecord
from sqlmodel import select
from collections import defaultdict
from datetime import datetime, timezone, timedelta

import logging
from fastapi import APIRouter

logger = logging.getLogger("store_api")
router = APIRouter()

@router.get('/{store_id}/metrics')
def store_metrics(store_id: str):
    with get_session() as session:
        events = session.exec(select(Event).where(Event.store_id == store_id)).all()
        sessions = session.exec(select(VisitorSession).where(VisitorSession.store_id == store_id)).all()
        pos_records = session.exec(select(POSRecord).where(POSRecord.store_id == store_id)).all()

    unique_visitors = len({s.visitor_id for s in sessions})
    total_exited = len({s.visitor_id for s in sessions if s.exit_timestamp})
    currently_in_store = max(0, unique_visitors - total_exited)
    total_sessions = len(sessions)

    dwell_by_zone = defaultdict(list)
    join_count = 0
    abandon_count = 0
    latest_queue_depth = 0
    converted_session_ids = set()

    for event in events:
        if event.event_type == 'ZONE_DWELL' and event.zone_id and event.dwell_ms:
            dwell_by_zone[event.zone_id].append(event.dwell_ms)
        elif event.event_type == 'BILLING_QUEUE_JOIN' and getattr(event, 'metadata_', None):
            join_count += 1
            latest_queue_depth = int(event.metadata_.get('queue_depth', latest_queue_depth) or latest_queue_depth)
        elif event.event_type == 'BILLING_QUEUE_ABANDON':
            abandon_count += 1

    # Dwell logic for billing queue using session data
    billing_dwells = []
    for s in sessions:
        if s.billing_first_seen and s.exit_timestamp:
            dur = (s.exit_timestamp - s.billing_first_seen).total_seconds() * 1000
            if dur > 0:
                billing_dwells.append(dur)
    if billing_dwells:
        dwell_by_zone['BILLING'] = billing_dwells

    for pos in pos_records:
        for visitor_session in sessions:
            if not visitor_session.billing_first_seen:
                continue
            if visitor_session.billing_first_seen <= pos.timestamp <= visitor_session.billing_first_seen + timedelta(minutes=5):
                converted_session_ids.add(visitor_session.id)

    conversion_rate = 0.0
    if total_sessions > 0:
        conversion_rate = len(converted_session_ids) / total_sessions

    avg_dwell_per_zone = {
        zone: (sum(values) / len(values)) if len(values) > 0 else 0.0
        for zone, values in dwell_by_zone.items()
    }

    abandonment_rate = 0.0
    if join_count > 0:
        abandonment_rate = abandon_count / join_count

    return {
        'store_id': store_id,
        'unique_visitors': unique_visitors,
        'currently_in_store': currently_in_store,
        'total_exited': total_exited,
        'conversion_rate': round(conversion_rate, 4),
        'avg_dwell_per_zone': avg_dwell_per_zone,
        'queue_depth': latest_queue_depth,
        'abandonment_rate': round(abandonment_rate, 4),
        'total_sessions': total_sessions,
        'converted_sessions': len(converted_session_ids),
    }
