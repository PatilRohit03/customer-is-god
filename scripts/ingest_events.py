import argparse
import json
import requests
from pathlib import Path


def load_jsonl(path: Path):
    events = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events


def main():
    parser = argparse.ArgumentParser(description='Ingest events JSONL into Store Intelligence API')
    parser.add_argument('--file', required=True, help='Path to events.jsonl')
    parser.add_argument('--url', default='http://localhost:8000/events/ingest', help='API ingest endpoint')
    args = parser.parse_args()

    path = Path(args.file)
    events = load_jsonl(path)
    response = requests.post(args.url, json={'events': events})
    response.raise_for_status()
    print(response.json())


if __name__ == '__main__':
    main()
