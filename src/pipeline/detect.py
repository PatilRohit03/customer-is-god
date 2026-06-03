from ultralytics import YOLO
import cv2
from pathlib import Path

MODEL_PATH = 'yolov8n.pt'

class Detector:
    def __init__(self, model_path: str = MODEL_PATH):
        self.model = YOLO(model_path)

    def detect_frame(self, frame):
        results = self.model(frame)
        return results

    def process_video(self, video_path: str):
        capture = cv2.VideoCapture(video_path)
        while capture.isOpened():
            ret, frame = capture.read()
            if not ret:
                break
            results = self.detect_frame(frame)
            yield results
        capture.release()
