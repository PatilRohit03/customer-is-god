# DESIGN.md

## Architecture Overview

This project implements an end-to-end Store Intelligence System anchored by four main components:

1. **Detection Pipeline (`src/pipeline`)**: Uses YOLOv8 for robust people detection in real-world CCTV lighting conditions. It integrates a custom visual Re-Identification (Re-ID) engine relying on HSV color histograms.
2. **Tracking & Emission Logic**: A spatial centroid tracker matched with Bhattacharyya distance handles Identity Switching when tracks are lost due to partial occlusions. It emits strict JSON-schema-compliant events for entries, exits, zone dwells, and billing queues.
3. **Intelligence API (`src/app`)**: A FastAPI backend featuring idempotent ingestion, SQLModel storage, and analytics endpoints for funnels, heatmaps, and operational anomalies (like missing dead zones).
4. **Deployment**: Containerized using Docker Compose for 5-command spin-up reliability and 503 graceful degradation handling.

## AI-Assisted Decisions

1. **Architecting the Visual Re-ID Engine**:
   - *Prompt*: "How can I solve ByteTrack fragmentation and track identity swapping when a customer is occluded behind a billing counter, without the CPU overhead of running a heavy deep learning OSNet extractor on every frame?"
   - *Critique & Usage*: The AI originally suggested using a pre-trained ResNet feature extractor. I rejected this due to edge-compute constraints for this challenge. Instead, I prompted it to refine a lightweight `cv2.calcHist` (HSV color space) extraction mixed with a spatial momentum fallback. I adopted this because it achieves high accuracy for track re-linking with near-zero latency penalty.
2. **Staff Classification Heuristic**:
   - *Prompt*: "I need to accurately classify store cashiers without a dedicated VLM or uniform-detection dataset."
   - *Critique & Usage*: The AI proposed using GPT-4V to classify cropped frames every 5 seconds. I rejected this as computationally infeasible and a violation of real-time pipeline needs. Instead, I agreed with its secondary suggestion: a deterministic spatial-temporal heuristic. Any tracked entity dwelling strictly within the billing queue's cashier bounding box for >45 seconds is internally flagged as `is_staff = True`.
3. **Graceful Degradation Middleware**:
   - *Prompt*: "Write a FastAPI middleware for structured logging (trace_id, latency) and a global exception handler that returns a 503 instead of crashing on DB disconnects."
   - *Usage*: I adopted the generated code but heavily modified the logging format to ensure `store_id` is always parsed safely from path params, which the AI initially missed.
