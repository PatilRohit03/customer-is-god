# CHOICES.md

## Decision 1: Detection Model & Tracker

**Options considered:**
- YOLOv8 + DeepSORT
- YOLOv9 + ByteTrack
- YOLOv8 + Custom Centroid/HSV ReID Tracker

**Choice:** `YOLOv8 + Custom Centroid/HSV ReID Tracker`

**Why:**
- *What AI Suggested:* The AI suggested pairing YOLOv8 with ByteTrack for state-of-the-art performance.
- *Why I Disagreed:* While ByteTrack handles continuous motion beautifully, it fails gracefully during long static occlusions (like a cashier bending down), leading to severe track fragmentation (turning 4 people into 14).
- *Final Choice:* I built a custom CentroidTracker enhanced with Hue-Saturation-Value (HSV) histogram extraction. By computing Bhattacharyya distance on lost tracks, we can stitch fragmented tracks back to their original `visitor_id` with virtually no CPU overhead compared to a heavy neural network ReID.

## Decision 2: Event Schema and Abandonment Logic

**Options considered:**
- Simple ENTRY/EXIT events
- Strict adherence to the PDF Schema with ABANDON/REENTRY states

**Choice:** `Strict Schema with ABANDON/REENTRY tracking`

**Why:**
- *What AI Suggested:* The AI initially generated a simple pipeline that only tracked when a customer was inside the camera frame.
- *Why I Disagreed:* A simple schema cannot accurately calculate the North Star Metric (Conversion Rate) or Queue Wait Times. If a customer joins the billing queue but leaves without buying anything, ignoring them skews the metric.
- *Final Choice:* I explicitly engineered the tracker to maintain a `has_exited` state and a `joined_billing` state. When tracks are permanently lost in the billing zone, it emits a `BILLING_QUEUE_ABANDON` event. The API leverages this to calculate a highly accurate average dwell time for the billing queue, rather than just returning 0.0s.

## Decision 3: API Architecture & Storage Engine

**Options considered:**
- Express/Node.js with PostgreSQL
- FastAPI with SQLite

**Choice:** `FastAPI with SQLite`

**Why:**
- *What AI Suggested:* The AI suggested PostgreSQL for robust production-ready data persistence.
- *Why I Disagreed:* The challenge emphasizes ease of setup ("docker compose up starts everything") and portability. A dedicated Postgres container adds unnecessary complexity and memory overhead for evaluating an offline pipeline.
- *Final Choice:* I chose FastAPI coupled with SQLite (via SQLModel). It provides incredible speed, native Pydantic validation (ensuring our ingested events strictly match the required schema), and requires zero external database configuration, perfectly balancing production readiness with evaluation simplicity.
