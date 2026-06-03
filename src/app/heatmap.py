from fastapi import APIRouter
from .database import get_session
from .models import Event
from sqlmodel import select
from collections import defaultdict

router = APIRouter()

@router.get('/{store_id}/heatmap')
def store_heatmap(store_id: str):
    with get_session() as session:
        events = session.exec(select(Event).where(Event.store_id == store_id)).all()

    zone_visits = defaultdict(int)
    zone_dwell = defaultdict(list)
    sessions = {event.visitor_id for event in events if not event.is_staff and event.event_type in ('ENTRY', 'REENTRY')}

    for event in events:
        if event.event_type == 'ZONE_ENTER' and event.zone_id:
            zone_visits[event.zone_id] += 1
        if event.event_type == 'ZONE_DWELL' and event.zone_id and event.dwell_ms:
            zone_dwell[event.zone_id].append(event.dwell_ms)

    if not zone_visits:
        return {
            'store_id': store_id,
            'heatmap': {},
            'zones': [],
            'data_confidence': False,
        }

    max_visits = max(zone_visits.values()) if zone_visits else 1
    zones = []
    for zone_id, visits in zone_visits.items():
        avg_dwell = sum(zone_dwell.get(zone_id, [])) / len(zone_dwell.get(zone_id, [])) if zone_dwell.get(zone_id) else 0
        zones.append({
            'zone_id': zone_id,
            'visit_count': visits,
            'avg_dwell_ms': round(avg_dwell, 2),
            'heat_score': round((visits / max_visits) * 100, 1),
        })

    return {
        'store_id': store_id,
        'heatmap': {z['zone_id']: z['visit_count'] for z in zones},
        'zones': zones,
        'data_confidence': len(sessions) >= 20,
    }
