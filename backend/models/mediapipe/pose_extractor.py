"""
MediaPipe Pose 래퍼.
17 관절(H36M) 또는 33 관절(MediaPipe 기본) 키포인트 추출에 사용.
"""
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

from core.config import MEDIAPIPE_POSE_TASK

def load_mediapipe_pose():
    """
    PoseLandmarker 인스턴스 생성.
    
    영상 프레임 시퀀스 처리에 적합한 VIDEO 모드로 설정.
    """
    if not MEDIAPIPE_POSE_TASK.exists():
        raise FileNotFoundError(
            f"MediaPipe 모델 파일을 찾을 수 없습니다: {MEDIAPIPE_POSE_TASK}\n"
            f"다음에서 다운로드해서 위 경로에 저장하세요:\n"
            f"https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
            f"pose_landmarker_full/float16/latest/pose_landmarker_full.task"
        )
    
    base_options = mp_python.BaseOptions(
        model_asset_path=str(MEDIAPIPE_POSE_TASK)
    )
    
    options = mp_vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=mp_vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        output_segmentation_masks=False,
    )
    
    return mp_vision.PoseLandmarker.create_from_options(options)


