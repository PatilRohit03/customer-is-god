from fastapi import APIRouter
from .database import get_session
from .models import Event, VisitorSession
from sqlmodel import select

router = APIRouter()

@router.get('/{store_id}/funnel')
def store_funnel(store_id: str):
    with get_session() as session:
        events = session.exec(select(Event).where(Event.store_id == store_id)).all()
        sessions = session.exec(select(VisitorSession).where(VisitorSession.store_id == store_id)).all()

    entry_visitors = set()
    zone_visitors = set()
    billing_visitors = set()
    purchase_visitors = set()

    for event in events:
        if event.is_staff:
            continue
        if event.event_type in ('ENTRY', 'REENTRY'):
            entry_visitors.add(event.visitor_id)
        if event.event_type == 'ZONE_ENTER':
            zone_visitors.add(event.visitor_id)
        if event.event_type == 'BILLING_QUEUE_JOIN':
            billing_visitors.add(event.visitor_id)
        if event.event_type == 'PURCHASE':
            purchase_visitors.add(event.visitor_id)

    entry_count = len(entry_visitors)
    purchase_count = len(purchase_visitors)
    overall_conversion = 0.0
    if entry_count > 0:
        overall_conversion = purchase_count / entry_count

    return {
        'store_id': store_id,
        'funnel': {
            'total_sessions': entry_count,
            'billing_queue_joins': len(billing_visitors),
            'purchases': purchase_count,
            'overall_conversion': round(overall_conversion, 4),
        }
    }
