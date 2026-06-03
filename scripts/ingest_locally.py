import argparse
import json
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure project src is importable when running scripts
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.app.main import app

client = TestClient(app)


def load_jsonl(path: Path):
    events = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events


def load_pos_csv(path: Path):
    import csv
    from datetime import datetime
    transactions = []
    with path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse DD-MM-YYYY HH:MM:SS format to ISO 8601
            date_str = row.get('order_date')  # DD-MM-YYYY
            time_str = row.get('order_time')  # HH:MM:SS
            if date_str and time_str:
                # Parse: 10-04-2026 -> day, month, year
                day, month, year = date_str.split('-')
                # Convert to ISO: YYYY-MM-DD HH:MM:SS
                iso_ts = f"{year}-{month}-{day}T{time_str}Z"
                timestamp = iso_ts
            else:
                timestamp = row.get('timestamp')
            
            transactions.append({
                'transaction_id': row.get('order_id'),
                'store_id': row.get('store_id') or 'STORE_1',
                'timestamp': timestamp,
                'basket_value_inr': float(row.get('total_amount') or 0),
            })
    return transactions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--events', required=True, help='Path to events jsonl')
    parser.add_argument('--pos', required=False, help='Path to POS CSV')
    parser.add_argument('--limit', type=int, required=False, help='Limit events to first N')
    args = parser.parse_args()

    events_path = Path(args.events)
    events = load_jsonl(events_path)
    if args.limit:
        events = events[: args.limit]
    print(f'Posting {len(events)} events to /events/ingest')
    r = client.post('/events/ingest', json={'events': events})
    print('ingest status', r.status_code)
    try:
        print(r.json())
    except Exception:
        print(r.text)

    if args.pos:
        pos_path = Path(args.pos)
        transactions = load_pos_csv(pos_path)
        print(f'Posting {len(transactions)} POS records to /pos/ingest')
        r2 = client.post('/pos/ingest', json={'transactions': transactions})
        print('pos ingest status', r2.status_code)
        try:
            print(r2.json())
        except Exception:
            print(r2.text)

    # Show metrics for STORE_1
    m = client.get('/stores/STORE_1/metrics')
    print('metrics:', m.status_code)
    try:
        print(m.json())
    except Exception:
        print(m.text)


if __name__ == '__main__':
    main()
