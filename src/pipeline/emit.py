import json
from pathlib import Path
from datetime import datetime, timezone
from ultralytics import YOLO
import cv2
from .store_layouts import STORE_LAYOUTS
from typing import Dict, List, Optional
import uuid
from .tracker import CentroidTracker
from typing import Any
import math


class EventEmitter:
    def __init__(self, store_config: Dict, model_path: str = 'yolov8n.pt', frame_skip: int = 15, tracker_type: str = 'centroid'):
        self.store_config = store_config
        self.model = YOLO(model_path)
        self.frame_skip = max(1, frame_skip)
        self.tracker: Any
        if tracker_type == 'deep_sort':
            try:
                from .deepsort_adapter import DeepSortAdapter
                self.tracker = DeepSortAdapter()
            except Exception as exc:
                # Fallback to centroid tracker if deep sort unavailable
                print('DeepSortAdapter init failed, falling back to CentroidTracker:', exc)
                self.tracker = CentroidTracker(max_lost=15, max_distance=100.0)
        elif tracker_type == 'bytetrack':
            try:
                from .bytetrack_adapter import ByteTrackAdapter
                self.tracker = ByteTrackAdapter()
            except Exception as exc:
                print('ByteTrackAdapter init failed, falling back to CentroidTracker:', exc)
                self.tracker = CentroidTracker(max_lost=15, max_distance=100.0)
        else:
            self.tracker = CentroidTracker(max_lost=15, max_distance=100.0)

    def process_store(self, resource_dir: Path, output_path: Path):
        events = []
        for camera_file, camera_type in self.store_config['camera_types'].items():
            path = resource_dir / self.store_config['name'] / camera_file
            if not path.exists():
                print(f"Warning: {camera_file} not found. Emitting DEAD_ZONE anomaly.")
                timestamp = datetime.now(timezone.utc).isoformat()
                events.append({
                    'event_id': str(uuid.uuid4()),
                    'store_id': self.store_config['store_id'],
                    'camera_id': camera_file,
                    'visitor_id': 'SYSTEM',
                    'event_type': 'SYSTEM_ANOMALY',
                    'timestamp': timestamp,
                    'zone_id': None,
                    'dwell_ms': None,
                    'is_staff': False,
                    'confidence': 1.0,
                    'metadata': {'type': 'DEAD_ZONE', 'description': 'Camera feed missing'}
                })
                continue
            events += self.process_video(path, camera_file, camera_type)
        self.save_events(output_path, events)

    def process_video(self, video_path: Path, camera_id: str, camera_type: str):
        capture = cv2.VideoCapture(str(video_path))
        events = []
        frame_index = 0
        fps = capture.get(cv2.CAP_PROP_FPS) or 15
        store_id = self.store_config['store_id']

        while True:
            ret, frame = capture.read()
            if not ret:
                break
            if frame_index % self.frame_skip != 0:
                frame_index += 1
                continue

            timestamp = datetime.now(timezone.utc).isoformat()
            detections = self.detect_persons(frame)
            try:
                alive = self.tracker.update(detections, frame_index=frame_index, frame=frame)
            except TypeError:
                alive = self.tracker.update(detections, frame_index)
                
            events += self.emit_events(alive, camera_id, camera_type, store_id, timestamp)
            frame_index += 1

        capture.release()
        return events

    def detect_persons(self, frame):
        results = self.model(frame, imgsz=640)
        persons = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                if int(box.cls) != 0:
                    continue
                xyxy = box.xyxy[0].cpu().numpy().tolist()
                confidence = float(box.conf[0].cpu().numpy())
                persons.append({'bbox': xyxy, 'confidence': confidence})
        return persons

    def update_tracks(self, detections, frame_index):
        # Deprecated: tracking is handled by CentroidTracker
        raise RuntimeError('update_tracks should not be called; use CentroidTracker')

    def emit_events(self, tracks: List[Any], camera_id: str, camera_type: str, store_id: str, timestamp: str):
        events = []
        # Get staff zone for billing if available
        staff_zone = None
        if 'BILLING' in self.store_config.get('zones', {}):
            if self.store_config['zones']['BILLING'].get('camera') == camera_id or camera_id in self.store_config['zones']['BILLING'].get('camera', []):
                staff_zone = self.store_config['zones']['BILLING'].get('staff_zone')
                
        for track in tracks:
            event_type = None
            metadata = {}
            confidence = track.confidence if hasattr(track, 'confidence') else 0.85
            is_staff = getattr(track, 'is_staff', False)
            
            # 1. Spatial Staff Identification (Instant)
            if not is_staff and staff_zone and hasattr(track, 'center'):
                cx, cy = track.center
                sx1, sy1, sx2, sy2 = staff_zone
                if sx1 <= cx <= sx2 and sy1 <= cy <= sy2:
                    is_staff = True
                    track.is_staff = True
            
            # 2. Behavioral Staff Heuristic (REMOVED)
            # We no longer use lifespan > 450 to identify staff because customers frequently dwell for over 30 seconds.
                    
            visitor_id = f'VIS_{track.track_id}'

            if camera_type == 'entry':
                event_type = 'ENTRY' if getattr(track, 'center', [0,0])[0] < 500 else 'EXIT'
                # Simple REENTRY check logic can be expanded.
                if event_type == 'ENTRY' and getattr(track, 'has_exited', False):
                    event_type = 'REENTRY'
                if event_type == 'EXIT':
                    track.has_exited = True
            elif camera_type == 'billing':
                queue_zone = self.store_config['zones']['BILLING'].get('queue_zone')
                qx1 = qy1 = qx2 = qy2 = 0
                if queue_zone:
                    qx1, qy1, qx2, qy2 = queue_zone
                    
                in_queue = True
                if queue_zone and hasattr(track, 'center'):
                    cx, cy = track.center
                    if not (qx1 <= cx <= qx2 and qy1 <= cy <= qy2):
                        in_queue = False
                
                if in_queue and not getattr(track, 'joined_billing_emitted', False):
                    event_type = 'BILLING_QUEUE_JOIN'
                    # Don't count staff or people outside queue zone in queue depth
                    queue_tracks = []
                    for t in tracks:
                        if getattr(t, 'is_staff', False): continue
                        t_in_queue = True
                        if queue_zone and hasattr(t, 'center'):
                            tcx, tcy = t.center
                            if not (qx1 <= tcx <= qx2 and qy1 <= tcy <= qy2):
                                t_in_queue = False
                        if t_in_queue:
                            queue_tracks.append(t)
                            
                    metadata['queue_depth'] = len(queue_tracks)
                    track.joined_billing = True
                    track.joined_billing_emitted = True
            elif camera_type == 'zone':
                event_type = 'ZONE_ENTER' if getattr(track, 'zone', None) is None else 'ZONE_DWELL'
                track.zone = 'MAIN_FLOOR'
                if event_type == 'ZONE_DWELL':
                    metadata['dwell_ms'] = self.frame_skip * 1000

            if event_type:
                events.append({
                    'event_id': str(uuid.uuid4()),
                    'store_id': store_id,
                    'camera_id': camera_id,
                    'visitor_id': visitor_id,
                    'event_type': event_type,
                    'timestamp': timestamp,
                    'zone_id': getattr(track, 'zone', None),
                    'dwell_ms': metadata.get('dwell_ms'),
                    'is_staff': is_staff,
                    'confidence': confidence,
                    'metadata': metadata,
                })
        
        # Check for abandoned billing queues (lost tracks that joined billing)
        for track in tracks:
            if hasattr(track, 'joined_billing') and getattr(track, 'lost_count', 0) > 10 and not getattr(track, 'abandon_emitted', False):
                events.append({
                    'event_id': str(uuid.uuid4()),
                    'store_id': store_id,
                    'camera_id': camera_id,
                    'visitor_id': f'VIS_{track.track_id}',
                    'event_type': 'BILLING_QUEUE_ABANDON',
                    'timestamp': timestamp,
                    'zone_id': None,
                    'dwell_ms': None,
                    'is_staff': getattr(track, 'is_staff', False),
                    'confidence': 0.9,
                    'metadata': {'abandoned': True}
                })
                track.abandon_emitted = True
                
        return events

    def save_events(self, output_path: Path, events: List[dict]):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open('w', encoding='utf-8') as f:
            for event in events:
                f.write(json.dumps(event) + '\n')

    @staticmethod
    def bbox_center(bbox):
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    @staticmethod
    def distance(a, b):
        return math.dist(a, b)
