import math
import cv2
import numpy as np
from typing import List, Dict


class Track:
    def __init__(self, track_id: int, bbox: List[float], frame_index: int, feature=None, confidence=0.0):
        self.track_id = track_id
        self.bbox = bbox
        self.first_seen = frame_index
        self.last_seen = frame_index
        self.lost_count = 0
        self.zone = None
        self.feature = feature
        self.confidence = confidence

    @property
    def center(self):
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)


class CentroidTracker:
    """A lightweight centroid-based tracker with visual Re-ID.
    
    - Assigns incremental integer IDs to new detections.
    - Matches by Euclidean distance + Bhattacharyya distance of color histograms.
    - Removes tracks after exceeding `max_lost` frames without match.
    """

    def __init__(self, max_lost: int = 15, max_distance: float = 100.0, reid_threshold: float = 0.4):
        self.next_id = 1
        self.tracks: Dict[int, Track] = {}
        self.max_lost = max_lost
        self.max_distance = max_distance
        self.reid_threshold = reid_threshold
        
    def _extract_feature(self, frame, bbox):
        if frame is None:
            return None
        x1, y1, x2, y2 = map(int, bbox)
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 - x1 < 10 or y2 - y1 < 10:
            return None
            
        crop = frame[y1:y2, x1:x2]
        # Crop center 60% to avoid background noise
        ch, cw = crop.shape[:2]
        crop = crop[int(ch*0.2):int(ch*0.8), int(cw*0.2):int(cw*0.8)]
        if crop.size == 0:
            return None
            
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [16, 16], [0, 180, 0, 256])
        cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        return hist

    @staticmethod
    def _bbox_center(bbox: List[float]):
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    @staticmethod
    def _distance(a, b):
        return math.dist(a, b)

    def update(self, detections: List[dict], frame_index: int, frame=None) -> List[Track]:
        matched = set()
        updated_tracks: Dict[int, Track] = {}
        unmatched_detections = []
        
        # Extract features for all current detections
        det_features = []
        for det in detections:
            det_features.append(self._extract_feature(frame, det['bbox']))

        # Step 1: Try to match existing active/lost tracks
        for idx, det in enumerate(detections):
            bbox = det['bbox']
            conf = det.get('confidence', 0.0)
            cx, cy = self._bbox_center(bbox)
            det_feat = det_features[idx]
            
            best_id = None
            best_score = float('inf')
            
            for tid, tr in self.tracks.items():
                if tid in matched:
                    continue
                    
                dist = self._distance(tr.center, (cx, cy))
                
                # Check visual similarity if available
                feat_dist = float('inf')
                if tr.feature is not None and det_feat is not None:
                    feat_dist = cv2.compareHist(tr.feature, det_feat, cv2.HISTCMP_BHATTACHARYYA)
                
                # Match if spatially close OR visually very similar (Re-ID for occlusions)
                if (dist <= self.max_distance) or (feat_dist < self.reid_threshold and tr.lost_count > 0):
                    # Combine distance and appearance score
                    score = (dist / self.max_distance) if feat_dist == float('inf') else feat_dist
                    if score < best_score:
                        best_score = score
                        best_id = tid
                        
            if best_id is not None:
                tr = self.tracks[best_id]
                tr.bbox = bbox
                tr.last_seen = frame_index
                tr.lost_count = 0
                tr.confidence = conf
                if det_feat is not None:
                    tr.feature = det_feat # update to latest appearance
                updated_tracks[best_id] = tr
                matched.add(best_id)
            else:
                unmatched_detections.append((bbox, det_feat, conf))

        # Step 2: Create new tracks for unmatched detections
        for bbox, feat, conf in unmatched_detections:
            tr = Track(self.next_id, bbox, frame_index, feature=feat, confidence=conf)
            updated_tracks[self.next_id] = tr
            self.next_id += 1

        # Step 3: Increment lost count for unmatched tracks
        for tid, tr in self.tracks.items():
            if tid not in matched:
                tr.lost_count += 1
                if tr.lost_count < self.max_lost:
                    updated_tracks[tid] = tr

        self.tracks = updated_tracks
        return list(self.tracks.values())

    def assign_visitor_id(self, track: Track) -> str:
        return f'VIS_{track.track_id}'
