"""
object_extractor.py — YOLO + HRNet 기반 포즈 추출

파이프라인:
  영상 → YOLO bbox → HRNet-W48 → COCO 17관절
  → H36M 17관절 → torso 정규화 → [F, 17, 3]
"""

import cv2
import numpy as np

from core.model_loader import ModelRegistry
from repository.video_repository import fetch_video
from models.HRnet.HRnet_loader import load_hrnet, extract_keypoints_hrnet

# ============================================================
# 정규화 상수
# ============================================================  
HIP_IDX = 0
THORAX_IDX = 8
CLIP_RANGE = 1.8


# ============================================================
# 진입점
# ============================================================
def extract_objects(video_id):
    """Supabase video_id로 영상 다운로드 → 포즈 추출."""
    with fetch_video(video_id) as video_path:
        return extract_object_from_path(video_path)


# ============================================================
# 메인 추출 함수
# ============================================================
def extract_object_from_path(video_path: str, sample_rate=None) -> dict:
    """
    영상 파일에서 YOLO + HRNet으로 H36M 키포인트 추출.

    Returns:
        dict: fps, num_frames, width, height, keypoints [F, 17, 3]
    """
    yolo = ModelRegistry.get().yolo
    hrnet_model, device = ModelRegistry.get().hrnet

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"영상을 열 수 없습니다: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 노트북과 동일: 30fps→3, 60fps→6 (10fps 효과)
    if sample_rate is None:
        sample_rate = max(1, round(fps / 10))

    keypoints_seq = []
    frame_idx = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if frame_idx % sample_rate != 0:
            frame_idx += 1
            continue

        # YOLO로 사람 박스 검출
        bbox = detect_person_bbox(yolo, frame)

        if bbox is None:
            if keypoints_seq:
                keypoints_seq.append(keypoints_seq[-1].copy())
            else:
                keypoints_seq.append(np.zeros((17, 3), dtype=np.float32))
            frame_idx += 1
            continue

        # HRNet으로 포즈 추출 (COCO → H36M 변환 포함)
        kps = extract_keypoints_hrnet(hrnet_model, frame, bbox, device)

        if kps is None:
            kps = (
                keypoints_seq[-1].copy() if keypoints_seq
                else np.zeros((17, 3), dtype=np.float32)
            )

        keypoints_seq.append(kps)
        frame_idx += 1

    cap.release()

    MAX_FRAMES = 240
    if len(keypoints_seq) > MAX_FRAMES:
        keypoints_seq = keypoints_seq[:MAX_FRAMES]

    keypoints_seq = np.stack(keypoints_seq, axis=0)  # [F, 17, 3]

    # ⭐ torso 정규화
    keypoints_seq = preprocess_for_motionbert(keypoints_seq)

    return {
        "fps": fps,
        "num_frames": len(keypoints_seq),
        "width": width,
        "height": height,
        "keypoints": keypoints_seq,
    }


# ============================================================
# YOLO 검출 (기존과 동일)
# ============================================================
def detect_person_bbox(model, frame):
    """YOLO로 가장 큰 사람 bbox 검출. 없으면 None."""
    result = model(frame, conf=0.3, imgsz=416, verbose=False, classes=0)
    boxes = result[0].boxes

    if boxes is None or len(boxes) == 0:
        return None

    xywh = boxes.xywh.cpu().numpy()
    areas = xywh[:, 2] * xywh[:, 3]
    main_idx = int(np.argmax(areas))

    x1, y1, x2, y2 = boxes[main_idx].xyxy[0].cpu().numpy()
    return (float(x1), float(y1), float(x2), float(y2))


# ============================================================
# Torso 정규화
# ============================================================
def _torso_normalize(kps_seq):
    """Hip 중심 + torso 길이 정규화."""
    out = kps_seq.copy().astype(np.float32)
    xy = out[..., :2]
    hip = xy[:, HIP_IDX : HIP_IDX + 1, :]
    xy_centered = xy - hip
    torso_vec = xy_centered[:, THORAX_IDX, :]
    torso_len = np.maximum(np.linalg.norm(torso_vec, axis=-1), 1e-6)
    out[..., :2] = xy_centered / torso_len[:, None, None]
    return out


def preprocess_for_motionbert(kps_seq):
    """torso 정규화 + clip."""
    kps_seq = _torso_normalize(kps_seq)
    kps_seq[..., :2] = np.clip(kps_seq[..., :2], -CLIP_RANGE, CLIP_RANGE)
    return kps_seq