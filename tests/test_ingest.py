# PROMPT: Generate a pytest file for testing POST /events/ingest in a FastAPI app. Include validation for idempotent ingest and malformed payload handling.
# CHANGES MADE: Updated the generated test to use the actual FastAPI app layout, simplified storage assumptions, and verified response shapes.

import uuid
from fastapi.testclient import TestClient
from src.app.main import app
from src.app.database import get_session, init_db
from src.app.models import Event

client = TestClient(app)

init_db()

def test_ingest_idempotent():
    event_id = f'evt-{uuid.uuid4()}'
    session = get_session()
    existing = session.get(Event, event_id)
    if existing:
        session.delete(existing)
        session.commit()

    payload = {
        'events': [
            {
                'event_id': event_id,
                'store_id': 'STORE_001',
                'camera_id': 'CAM_ENTRY',
                'visitor_id': 'VIS_001',
                'event_type': 'ENTRY',
                'timestamp': '2026-03-03T14:00:00Z',
                'zone_id': None,
                'dwell_ms': None,
                'is_staff': False,
                'confidence': 0.8,
                'metadata': {}
            }
        ]
    }

    response1 = client.post('/events/ingest', json=payload)
    assert response1.status_code == 200
    assert response1.json()['inserted'] == 1

    response2 = client.post('/events/ingest', json=payload)
    assert response2.status_code == 200
    assert response2.json()['inserted'] == 0
