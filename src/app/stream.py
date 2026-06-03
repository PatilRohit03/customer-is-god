import cv2
import threading
import time
import numpy as np
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pathlib import Path
from src.pipeline.store_layouts import STORE_LAYOUTS
from src.pipeline.emit import EventEmitter
from .database import engine
import logging
from sqlmodel import Session
from .models import Event

logger = logging.getLogger("store_api")

router = APIRouter()

_emitters = {}
_init_lock = threading.Lock()
_inference_lock = threading.Lock()

def get_emitter(store_id: str, camera_id: str, store_config: dict):
    global _emitters
    with _init_lock:
        key = f"{store_id}_{camera_id}"
        if key not in _emitters:
            _emitters[key] = EventEmitter(store_config=store_config, model_path='yolov8n.pt', tracker_type='deep_sort')
    return _emitters[key]

def generate_frames(store_id: str, camera_id: str):
    config = STORE_LAYOUTS.get(store_id)
    if not config:
        return
        
    camera_type = config['camera_types'].get(camera_id)
    if not camera_type:
        return

    resource_dir = Path('/app/data/resource')
    video_path = resource_dir / config['name'] / camera_id
    if not video_path.exists():
        logger.error(f"Video file not found at {video_path}")
        return

    emitter = get_emitter(store_id, camera_id, config)
    capture = cv2.VideoCapture(str(video_path))
    frame_index = 0
    frame_skip = 15
    from datetime import datetime, timezone

    retry_count = 0
    try:
        while True:
            ret, frame = capture.read()
            if not ret:
                # Video has ended. Stop tracking and display completion screen.
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "TRACKING COMPLETE", (140, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                ret, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                time.sleep(1)
                continue
                
            retry_count = 0
            if frame_index % frame_skip != 0:
                frame_index += 1
            frame_index += 1
            
            if frame_index % emitter.frame_skip != 0:
                continue
                
            with _inference_lock:
                detections = emitter.detect_persons(frame)
                try:
                    alive = emitter.tracker.update(detections, frame_index=frame_index, frame=frame)
                except TypeError:
                    alive = emitter.tracker.update(detections, frame_index)

            timestamp = datetime.now(timezone.utc).isoformat()
            events = emitter.emit_events(alive, camera_id, camera_type, store_id, timestamp)
            
            if events:
                from dateutil.parser import isoparse
                from .session import create_or_get_session, close_session, mark_billing_seen
                try:
                    with Session(engine) as db:
                        for evt in events:
                            clean_evt = {k: v for k, v in evt.items() if hasattr(Event, k)}
                            if isinstance(clean_evt.get('timestamp'), str):
                                clean_evt['timestamp'] = isoparse(clean_evt['timestamp'])
                            db_event = Event(**clean_evt)
                            db.merge(db_event)
                        db.commit()
                        
                    try:
                        for evt in events:
                            if not evt.get('is_staff'):
                                dt = isoparse(evt['timestamp'])
                                evt_type = evt.get('event_type')
                                v_id = evt.get('visitor_id')
                                if evt_type in ('ENTRY', 'REENTRY'):
                                    create_or_get_session(store_id, v_id, dt)
                                elif evt_type == 'EXIT':
                                    close_session(store_id, v_id, dt)
                                elif evt_type == 'BILLING_QUEUE_JOIN':
                                    mark_billing_seen(store_id, v_id, dt)
                    except Exception as ex:
                        logger.error(f"Failed to apply session logic: {ex}")
                except Exception as e:
                    logger.error(f"Failed to insert events: {e}")

            for track in alive:
                if getattr(track, 'is_staff', False):
                    continue
                if getattr(track, 'confidence', 0.0) < 0.6:
                    continue
                x1, y1, x2, y2 = map(int, getattr(track, 'bbox', track.to_ltrb() if hasattr(track, 'to_ltrb') else getattr(track, 'tlbr', [0,0,0,0])))
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"VIS_{getattr(track, 'track_id', '?')}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
                
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                   
            frame_index += 1
            time.sleep(0.02)
    except Exception as stream_err:
        logger.error(f"Generator crashed: {stream_err}", exc_info=True)
        raise

    capture.release()

@router.get("/{id}/cameras")
async def get_cameras(id: str):
    config = STORE_LAYOUTS.get(id)
    if not config:
        raise HTTPException(status_code=404, detail="Store not found")
    return {"cameras": list(config['camera_types'].keys())}

@router.get("/{id}/stream/{camera_id}")
async def stream_video(id: str, camera_id: str):
    return StreamingResponse(generate_frames(id, camera_id), media_type="multipart/x-mixed-replace; boundary=frame")
