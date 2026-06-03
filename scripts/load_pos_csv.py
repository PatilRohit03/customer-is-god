import argparse
import csv
import requests
from pathlib import Path
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description='Load POS CSV into Store Intelligence API')
    parser.add_argument('--csv', required=True, help='Path to POS CSV file')
    parser.add_argument('--url', default='http://localhost:8000/pos/ingest', help='API POS ingest endpoint')
    args = parser.parse_args()

    path = Path(args.csv)
    transactions = []
    with path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamp = row.get('order_date') + 'T' + row.get('order_time') + 'Z'
            transactions.append({
                'transaction_id': row.get('order_id'),
                'store_id': row.get('store_id'),
                'timestamp': timestamp,
                'basket_value_inr': float(row.get('total_amount') or 0),
            })

    response = requests.post(args.url, json={'transactions': transactions})
    response.raise_for_status()
    print(response.json())


if __name__ == '__main__':
    main()
