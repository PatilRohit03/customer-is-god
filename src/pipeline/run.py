import argparse
from pathlib import Path
from .emit import EventEmitter
from .store_layouts import STORE_LAYOUTS


def main():
    parser = argparse.ArgumentParser(description='Run YOLOv8 detection pipeline on CCTV clips and emit structured events.')
    parser.add_argument('--store-id', required=True, help='Store identifier, e.g. STORE_1 or STORE_2')
    parser.add_argument('--resource-dir', required=True, help='Path to the raw resource directory')
    parser.add_argument('--output', default='events.jsonl', help='Output JSONL file path')
    parser.add_argument('--model', default='yolov8n.pt', help='YOLOv8 model name or path')
    parser.add_argument('--frame-skip', type=int, default=15, help='Process every Nth frame to reduce throughput')
    parser.add_argument('--tracker', choices=['centroid', 'deep_sort', 'bytetrack'], default='bytetrack', help='Tracker backend to use')
    args = parser.parse_args()

    config = STORE_LAYOUTS.get(args.store_id)
    if not config:
        raise SystemExit(f'Unknown store ID: {args.store_id}')

    resource_path = Path(args.resource_dir)
    if not resource_path.exists():
        raise SystemExit(f'Resource path not found: {resource_path}')

    emitter = EventEmitter(store_config=config, model_path=args.model, frame_skip=args.frame_skip, tracker_type=args.tracker)
    output_path = Path(args.output)
    emitter.process_store(resource_path, output_path)
    print(f'Events written to {output_path.absolute()}')


if __name__ == '__main__':
    main()
