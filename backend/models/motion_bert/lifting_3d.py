"""
models/motion_bert/3d_extractor.py
===================================
MotionBERT 3D Lifting — HRNet 2D 좌표 → 3D 좌표 추출

기존 embedder.py와 동일 모델 사용, 호출 방식만 다름:
  - embedder:      model(x, return_rep=True)  → [F, 17, 512] 임베딩
  - 3d_extractor:  model(x)                   → [F, 17, 3]   3D 좌표

[입력]  HRNet .npy [F, 17, 3] (torso 정규화 완료, x_norm/y_norm/conf)
[출력]  3D 좌표 [F', 17, 3] (x, y, z)




from models.motion_bert.lifting_3d import extract_3d, extract_3d_from_dict

#2.
# 방법 1 — keypoints 직접 전달
kps_3d = extract_3d(keypoints, fps=30.0)    # [F', 17, 3]

# 방법 2 — object_extractor 결과 dict 전달
result = extract_object_from_path(video_path)
kps_3d = extract_3d_from_dict(result)       # [F', 17, 3]


"""

import numpy as np
import torch

from core.model_loader import ModelRegistry

# ============================================================
# 상수
# ============================================================
TARGET_FPS = 10
MAX_FRAMES = 243


# ============================================================
# 리샘플링 (노트북 그대로)
# ============================================================
def _resample_to_target_fps(data, original_fps, target_fps=TARGET_FPS):
    """원본 FPS → TARGET_FPS로 리샘플링, MAX_FRAMES 제한."""
    n_frames = len(data)
    duration = n_frames / original_fps
    target_n = min(int(duration * target_fps), MAX_FRAMES)
    if target_n <= 0:
        target_n = 1
    indices = np.linspace(0, n_frames - 1, target_n).astype(int)
    return data[indices]


def _estimate_fps_from_frames(n_frames, max_duration=23):
    """프레임 수로 원본 FPS 추정 (메타데이터 없을 때 사용)."""
    if n_frames > max_duration * 15:
        return round(n_frames / max_duration)
    return 30


# ============================================================
# 3D Lifting 메인 함수
# ============================================================
def extract_3d(keypoints: np.ndarray, fps: float = None) -> np.ndarray:
    """
    MotionBERT로 2D 키포인트 → 3D 좌표 추출.

    Args:
        keypoints: [F, 17, 3] HRNet 출력 (torso 정규화 완료)
        fps: 원본 영상 FPS. None이면 프레임 수로 추정

    Returns:
        np.ndarray [F', 17, 3] — 3D 좌표 (x, y, z)
    """
    model = ModelRegistry.get().motion_bert
    device = next(model.parameters()).device

    # FPS 추정 (메타데이터 없는 경우)
    if fps is None:
        fps = _estimate_fps_from_frames(len(keypoints))

    # TARGET_FPS로 리샘플링
    resampled = _resample_to_target_fps(keypoints, fps)

    # [F, 17, 3] → [1, F, 17, 3] 텐서 변환
    x = torch.tensor(resampled, dtype=torch.float32).unsqueeze(0).to(device)

    # ⭐ 3D Lifting: model(x) — return_rep 없음
    with torch.no_grad():
        out_3d = model(x)  # [1, F', 17, 3]

    out_3d = out_3d.squeeze(0).cpu().numpy()  # [F', 17, 3]

    return out_3d


def extract_3d_from_dict(extract_result: dict) -> np.ndarray:
    """
    object_extractor의 출력 dict를 받아서 3D 추출.

    Args:
        extract_result: extract_object_from_path()의 반환값
            {
                "fps": float,
                "num_frames": int,
                "keypoints": np.ndarray [F, 17, 3]
            }

    Returns:
        np.ndarray [F', 17, 3] — 3D 좌표
    """
    return extract_3d(
        keypoints=extract_result["keypoints"],
        fps=extract_result["fps"],
    )