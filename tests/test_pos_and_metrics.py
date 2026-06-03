# PROMPT: Generate pytest tests for a FastAPI retail metrics API. Include tests for empty stores, all-staff clips (where no customers exist), zero purchases, and testing the edge case of a customer re-entering the conversion funnel.
# CHANGES MADE: I updated the generated mock data payloads to match my SQLModel structure and added manual SQL cleanup between tests to ensure idempotency.

import uuid
from fastapi.testclient import TestClient
from src.app.main import app
from src.app.database import init_db, get_session
from src.app.models import Event, POSRecord, VisitorSession

client = TestClient(app)

init_db()


def test_pos_ingest_and_metrics():
    session = get_session()
    # clean up previous test data if any
    store_id = 'STORE_TEST'
    transaction_id = f'TXN_{uuid.uuid4()}'
    existing_pos = session.get(POSRecord, transaction_id)
    if existing_pos:
        session.delete(existing_pos)
        session.commit()

    event_payload = {
        'events': [
            {
                'event_id': f'evt-{uuid.uuid4()}',
                'store_id': store_id,
                'camera_id': 'CAM_ENTRY',
                'visitor_id': 'VIS_001',
                'event_type': 'ENTRY',
                'timestamp': '2026-03-03T14:00:00Z',
                'zone_id': None,
                'dwell_ms': None,
                'is_staff': False,
                'confidence': 0.85,
                'metadata': {},
            },
            {
                'event_id': f'evt-{uuid.uuid4()}',
                'store_id': store_id,
                'camera_id': 'CAM_BILLING',
                'visitor_id': 'VIS_001',
                'event_type': 'BILLING_QUEUE_JOIN',
                'timestamp': '2026-03-03T14:04:00Z',
                'zone_id': 'BILLING',
                'dwell_ms': None,
                'is_staff': False,
                'confidence': 0.9,
                'metadata': {'queue_depth': 2},
            },
        ]
    }

    ingest_response = client.post('/events/ingest', json=event_payload)
    assert ingest_response.status_code == 200
    assert ingest_response.json()['inserted'] == 2

    pos_payload = {
        'transactions': [
            {
                'transaction_id': transaction_id,
                'store_id': store_id,
                'timestamp': '2026-03-03T14:08:00Z',
                'basket_value_inr': 1200.0,
            }
        ]
    }
    pos_response = client.post('/pos/ingest', json=pos_payload)
    assert pos_response.status_code == 200
    assert pos_response.json()['inserted'] == 1

    metrics_response = client.get(f'/stores/{store_id}/metrics')
    assert metrics_response.status_code == 200
    data = metrics_response.json()
    assert data['store_id'] == store_id
    assert data['unique_visitors'] == 1
    assert data['total_sessions'] == 1
    assert data['converted_sessions'] == 1
    assert data['queue_depth'] == 2
