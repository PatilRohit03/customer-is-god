from fastapi import APIRouter
from .database import get_session
from .models import Event
from sqlmodel import select
from datetime import datetime, timedelta, timezone
from collections import defaultdict

router = APIRouter()

@router.get('/{store_id}/anomalies')
def get_anomalies(store_id: str):
    with get_session() as session:
        events = session.exec(select(Event).where(Event.store_id == store_id)).all()

    now = datetime.now(timezone.utc)
    anomalies = []
    if not events:
        return {'store_id': store_id, 'anomalies': []}

    queue_depths = []
    conversion_rates = []
    zone_last_seen = defaultdict(lambda: None)
    visitor_entries = set()
    purchase_visitors = set()
    join_count = 0
    abandon_count = 0

    for event in events:
        if event.event_type == 'BILLING_QUEUE_JOIN' and event.metadata_:
            queue_depths.append(int(event.metadata_.get('queue_depth', 0) or 0))
            join_count += 1
        if event.event_type == 'BILLING_QUEUE_ABANDON':
            abandon_count += 1
        if event.event_type == 'PURCHASE':
            purchase_visitors.add(event.visitor_id)
        if event.event_type in ('ENTRY', 'REENTRY') and not event.is_staff:
            visitor_entries.add(event.visitor_id)
        if event.event_type == 'ZONE_ENTER' and event.zone_id:
            zone_last_seen[event.zone_id] = event.timestamp

    if queue_depths:
        latest_depth = queue_depths[-1]
        avg_depth = sum(queue_depths) / len(queue_depths)
        if latest_depth >= max(5, avg_depth * 1.8):
            anomalies.append({
                'type': 'BILLING_QUEUE_SPIKE',
                'severity': 'WARN',
                'message': f'Queue depth spike detected: {latest_depth} vs avg {avg_depth:.1f}',
                'suggested_action': 'Check billing staffing or queue dividers',
            })

    total_entries = len(visitor_entries)
    conversion_rate = 0.0
    if total_entries > 0:
        conversion_rate = len(purchase_visitors) / total_entries
    if total_entries >= 5 and conversion_rate < 0.1:
        anomalies.append({
            'type': 'CONVERSION_DROP',
            'severity': 'INFO',
            'message': f'Conversion rate is low: {conversion_rate:.2f}',
            'suggested_action': 'Review billing flow and customer support at point-of-sale',
        })

    dead_zones = []
    threshold = now - timedelta(minutes=30)
    for zone_id, last_seen in zone_last_seen.items():
        if last_seen and last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        if not last_seen or last_seen < threshold:
            dead_zones.append(zone_id)
    if dead_zones:
        anomalies.append({
            'type': 'DEAD_ZONE',
            'severity': 'INFO',
            'message': f'Zones with no visits in last 30 min: {dead_zones}',
            'suggested_action': 'Inspect signage or product placement in dead zones',
        })

    if join_count > 0 and abandon_count / join_count > 0.25:
        anomalies.append({
            'type': 'BILLING_QUEUE_ABANDONMENT',
            'severity': 'WARN',
            'message': f'Abandonment rate is high: {abandon_count}/{join_count}',
            'suggested_action': 'Investigate billing queue wait times',
        })

    return {'store_id': store_id, 'anomalies': anomalies}
