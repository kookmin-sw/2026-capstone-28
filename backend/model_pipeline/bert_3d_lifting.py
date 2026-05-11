
import numpy as np
import torch

from core.model_loader import ModelRegistry
from core.config import DEVICE

TARGET_FPS = 10
MAX_FRAMES = 243

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


def lifting_motion(keypoints: np.ndarray, fps=None) -> np.ndarray:

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


def extract_3d_from_hrnet(extract_result: dict) -> np.ndarray:
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
    return lifting_motion(
        keypoints=extract_result["keypoints"],
        fps=extract_result["fps"],
    )