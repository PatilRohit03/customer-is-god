# Technical Choices & Trade-offs

Building this real-time analytics pipeline required balancing speed, accuracy, and ease of use. Below are the three major architectural and model decisions made during development, explicitly detailing how AI assistance shaped the outcomes.

## 1. Detection Model Choice
**Decision:** We chose the Ultralytics **YOLOv8 Nano (`yolov8n.pt`)** paired with the **ByteTrack** tracker.
- **Options Considered:** YOLOv8 Nano vs YOLOv8 X (Extra Large) vs SSD MobileNet. We also considered DeepSORT vs ByteTrack for the tracking algorithm.
- **What AI Suggested & The Prompt Used:** 
  I used the following prompt to ask the LLM for a model recommendation:
  > *# PROMPT: I need to run a computer vision pipeline on 4 simultaneous 1080p retail store CCTV video streams on a standard CPU/GPU setup. I need to detect people and track them across frames to measure dwell time. Should I use YOLOv8 or something else? Which size and which tracker is best for real-time performance?*
  
  The AI suggested using YOLOv8 Nano (`yolov8n.pt`) because the larger YOLO models would instantly bottleneck the system when processing 4 streams simultaneously. For tracking, the AI strongly recommended ByteTrack over DeepSORT because ByteTrack is natively integrated into Ultralytics YOLO and has significantly lower overhead since it primarily relies on intersection-over-union (IoU) of bounding boxes rather than heavy feature extraction.
- **What We Chose & Why:** I **agreed** with the AI and implemented YOLOv8n with ByteTrack. 
- **Evaluation of the Prompt:** The AI's suggestion worked perfectly. The combination of the Nano model with ByteTrack and a `frame_skip` of 15 allowed the system to multiplex all 4 camera streams in real-time without crashing the backend or starving the API threads.

## 2. Event Schema Design Rationale
**Decision:** We chose a **Decoupled, Lightweight Event-Driven Schema** rather than a stateful database polling system.
- **Options Considered:** 
  1. The computer vision pipeline writes raw bounding boxes directly to the SQLite database, and the API constantly queries the DB to figure out where people are.
  2. The CV pipeline calculates zone overlaps internally and sends lightweight JSON HTTP POST events (like `ZONE_DWELL`, `ENTRY`, `BILLING_QUEUE_JOIN`) to the API.
- **What AI Suggested:** The AI suggested Option 2 (event-driven). It pointed out that writing raw bounding boxes to a database at 30 FPS for multiple cameras would cause severe SQLite locking issues (Database is Locked errors) and ruin the graceful degradation requirements.
- **What We Chose & Why:** I **agreed** with this suggestion. I built the `EventEmitter` class in the CV pipeline to hold the store's zone polygons in memory. It calculates the intersections locally and only emits a JSON payload to the FastAPI `/events/ingest` endpoint when a state changes (e.g., someone enters a zone or stays for >X seconds). This keeps the database size extremely small and prevents locking.

## 3. API Architecture Choice
**Decision:** We chose **FastAPI with Async Endpoints and SQLite (SQLModel)** over a synchronous Flask app with PostgreSQL.
- **Options Considered:** Flask + PostgreSQL vs FastAPI + SQLite.
- **What AI Suggested:** The AI initially suggested using PostgreSQL to handle concurrent writes from the 4 video streams safely, but recommended FastAPI for its async streaming capabilities to overcome typical web server blocking.
- **What We Chose & Why:** I **partially overrode** the AI. I agreed to use FastAPI because its native async support is absolutely critical for keeping 4 long-lived MJPEG streams open via `multipart/x-mixed-replace` without starving the metrics polling endpoints. However, I overrode the PostgreSQL suggestion and chose SQLite mapped with SQLModel. Given the hackathon requirement that the project must spin up with a single `docker compose up` without manual steps, SQLite was much simpler, required zero configuration, and—because of our lightweight event schema—handled the concurrent writes perfectly without locking. *Note: The AI was also crucial in helping diagnose browser limitations; when testing hot-swapping between store streams, the browser hit a hard 6-connection limit per domain causing some videos to render black. The AI identified this as a client-side socket issue, allowing us to document the F5 refresh workaround rather than unnecessarily over-engineering a WebSocket solution.*
