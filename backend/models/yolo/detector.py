"""
YOLO 객체 감지 래퍼.
공식 Ultralytics YOLOv8 사용 (별도 학습 가중치 없음).

"""
import logging

import numpy as np
from ultralytics import YOLO

from core.config import YOLO_WEIGHTS, DEVICE

logger = logging.getLogger(__name__)


def load_yolo() -> YOLO:
    weights_path = str(YOLO_WEIGHTS) if YOLO_WEIGHTS.exists() else "yolov8n.pt"
    model = YOLO(weights_path)
    # CPU 모드 명시
    model.to(DEVICE)

    # ── 병렬 호출 대비 사전 fuse + warmup ────────────────────────
    # YOLOv8은 첫 추론 시 Conv+BN을 lazy fuse하면서 self.bn을 제거한다.
    # analyze.py의 ThreadPoolExecutor가 두 영상을 동시에 호출하면
    # "AttributeError: 'Conv' object has no attribute 'bn'" 경쟁 상태가 발생.
    # 로드 시점에 단일 스레드에서 fuse를 완료해두면 이후엔 fuse가 재진입하지 않는다.
    try:
        model.fuse()
    except Exception as e:
        logger.warning(f"YOLO 사전 fuse 생략: {e}")

    # 내부 파이프라인(예: predictor 초기화, 메모리 레이아웃)도 1회 호출로 확정.
    # 실제 추론(detect_person_bbox)과 동일한 imgsz로 warmup해야 첫 실측 호출에서
    # predictor 내부 buffer 재할당 비용이 발생하지 않는다.
    dummy = np.zeros((416, 416, 3), dtype=np.uint8)
    _ = model(dummy, conf=0.3, imgsz=416, verbose=False, classes=0)

    return model
