import os 
import cv2
import numpy as np
import mediapipe as mp

from core.model_loader import ModelRegistry
from repository.video_repository import fetch_video
from model_pipeline.object_processor import preprocess_for_motionbert

# 최종 실행 #
def extract_objects(video_id):
    with fetch_video(video_id) as video_path:
        return extract_object_from_path(video_path)
    
# 테스트


# 객체 탐지 추출 #
def extract_object_from_path(video_path: str, sample_rate = 2) -> dict:
    yolo = ModelRegistry.get().yolo
    from models.mediapipe.pose_extractor import load_mediapipe_pose
    pose = load_mediapipe_pose()
    
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

        # ⭐ 현재 프레임의 timestamp(ms) 계산
        timestamp_ms = int(frame_idx * 1000 / fps)


        # YOLO로 사람 박스 검출
        bbox = detect_person_bbox(yolo, frame)
        if bbox is None:
            if keypoints_seq:
                keypoints_seq.append(keypoints_seq[-1].copy())
            else:
                keypoints_seq.append(np.zeros((17, 3), dtype=np.float32))
            frame_idx += 1
            continue
        
        # crop → MediaPipe → 좌표 변환 → H36M 매핑
        x1, y1, x2, y2 = bbox
        w, h = x2 - x1, y2 - y1
        margin_x, margin_y = w * 0.10, h * 0.10

        xmin = max(0, int(x1 - margin_x))
        ymin = max(0, int(y1 - margin_y))
        xmax = min(width  - 1, int(x2 + margin_x))
        ymax = min(height - 1, int(y2 + margin_y))


        cropped = frame[ymin:ymax, xmin:xmax]
        if cropped.size == 0:
            keypoints_seq.append(
                keypoints_seq[-1].copy() if keypoints_seq
                else np.zeros((17, 3), dtype=np.float32)
            )
            frame_idx += 1
            continue

        kps = extract_keypoints_mediapipe(pose, cropped, timestamp_ms)  # MP 객체 추출 33개 관절 -> 17개 관절

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
        
    keypoints_seq = np.stack(keypoints_seq, axis=0) 
    # keypoints_seq = preprocess_for_motionbert(keypoints_seq)   # ← 이 한 줄
    return {
        "fps": fps,
        "num_frames": len(keypoints_seq),
        "width": width,
        "height": height,
        "keypoints": keypoints_seq
    }


# YOLO
def detect_person_bbox(model, frame):
    result = model(frame, conf = 0.3, imgsz = 416, verbose = False, classes = 0)
    boxes = result[0].boxes

    if boxes is None or len(boxes) == 0:
        return None
    
    xywh = boxes.xywh.cpu().numpy()
    areas = xywh[:, 2] * xywh[:, 3]
    main_idx = int(np.argmax(areas))

    # xyxy 좌표 추출
    x1, y1, x2, y2 = boxes[main_idx].xyxy[0].cpu().numpy()
    return (float(x1), float(y1), float(x2), float(y2))

#MediaPipe
def extract_keypoints_mediapipe(pose, frame_bgr, timestamp_ms: int = 0) -> np.ndarray | None:
    _DIRECT_INDICES = {
    "NOSE":           0,
    "LEFT_EAR":       7,
    "RIGHT_EAR":      8,
    "LEFT_SHOULDER":  11,
    "RIGHT_SHOULDER": 12,
    "LEFT_ELBOW":     13,
    "RIGHT_ELBOW":    14,
    "LEFT_WRIST":     15,
    "RIGHT_WRIST":    16,
    "LEFT_HIP":       23,
    "RIGHT_HIP":      24,
    "LEFT_KNEE":      25,
    "RIGHT_KNEE":     26,
    "LEFT_ANKLE":     27,
    "RIGHT_ANKLE":    28,
    }
    
    """
    crop된 이미지에서 PoseLandmarker(신 API)로 키포인트 추출 후 H36M 17관절 변환.

    Args:
        pose: PoseLandmarker 인스턴스 (mp.tasks.vision)
        frame_bgr: BGR 이미지 (cv2 frame 또는 crop)
        timestamp_ms: 영상 내 타임스탬프(ms). VIDEO 모드는 단조 증가 값 필요

    Returns:
        np.ndarray [17, 3]  (x, y, visibility) 또는 None
    """
    # BGR → RGB → mp.Image로 감싸기
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

    # VIDEO 모드는 detect_for_video 사용, timestamp 필수
    result = pose.detect_for_video(mp_image, timestamp_ms)

    if not result.pose_landmarks or len(result.pose_landmarks) == 0:
        return None

    # 첫 번째 사람의 landmark만 사용 (num_poses=1로 설정했으니 어차피 1명)
    landmarks = result.pose_landmarks[0]

    by_name = {}
    for name, idx in _DIRECT_INDICES.items():
        lm = landmarks[idx]
        by_name[name] = {
            "x": lm.x,
            "y": lm.y,
            "visibility": lm.visibility,
        }

    return _convert_to_h36m(by_name)


#Convert to Proper Motion BERT Data
def _midpoint(a, b):
    """두 관절의 중점 (visibility는 더 낮은 값)"""
    return {
        "x": (a["x"] + b["x"]) / 2,
        "y": (a["y"] + b["y"]) / 2,
        "visibility": min(a["visibility"], b["visibility"]),
    }


def _convert_to_h36m(by_name: dict) -> np.ndarray:
    """
    MediaPipe 관절 dict → H36M 17관절 [17, 3] (x, y, visibility)
    노트북의 convert_frame_to_h36m 그대로.
    """
    l_hip      = by_name["LEFT_HIP"]
    r_hip      = by_name["RIGHT_HIP"]
    l_knee     = by_name["LEFT_KNEE"]
    r_knee     = by_name["RIGHT_KNEE"]
    l_ankle    = by_name["LEFT_ANKLE"]
    r_ankle    = by_name["RIGHT_ANKLE"]
    l_shoulder = by_name["LEFT_SHOULDER"]
    r_shoulder = by_name["RIGHT_SHOULDER"]
    l_elbow    = by_name["LEFT_ELBOW"]
    r_elbow    = by_name["RIGHT_ELBOW"]
    l_wrist    = by_name["LEFT_WRIST"]
    r_wrist    = by_name["RIGHT_WRIST"]
    
    # 계산이 필요한 관절
    hip    = _midpoint(l_hip, r_hip)
    thorax = _midpoint(l_shoulder, r_shoulder)
    spine  = _midpoint(hip, thorax)
    
    # 머리 — NOSE는 항상 있음
    neck_nose = by_name["NOSE"]
    head      = _midpoint(by_name["LEFT_EAR"], by_name["RIGHT_EAR"])
    
    # H36M 17관절 순서대로
    joints_17 = [
        hip,         # 0: Hip
        r_hip,       # 1: RHip
        r_knee,      # 2: RKnee
        r_ankle,     # 3: RFoot
        l_hip,       # 4: LHip
        l_knee,      # 5: LKnee
        l_ankle,     # 6: LFoot
        spine,       # 7: Spine
        thorax,      # 8: Thorax
        neck_nose,   # 9: Neck/Nose
        head,        # 10: Head
        l_shoulder,  # 11: LShoulder
        l_elbow,     # 12: LElbow
        l_wrist,     # 13: LWrist
        r_shoulder,  # 14: RShoulder
        r_elbow,     # 15: RElbow
        r_wrist,     # 16: RWrist
    ]
    
    result = np.zeros((17, 3), dtype=np.float32)
    for i, j in enumerate(joints_17):
        result[i, 0] = j["x"]
        result[i, 1] = j["y"]
        result[i, 2] = j["visibility"]
    return result