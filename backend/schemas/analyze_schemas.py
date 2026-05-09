from pydantic import BaseModel
from typing import List

class FrameObjects(BaseModel):
    frame_idx: int
    timestamp: float
    persons: List[dict]   # YOLO 박스 + MediaPipe 키포인트
    
class ObjectFeatures(BaseModel):
    fps: float
    duration: float
    frames: List[FrameObjects]

class AnalysisResult(BaseModel):
    overall_similarity: float
    segments: List[dict]
    summary: str