"""
중앙 설정 파일.
모든 경로/디바이스/하이퍼파라미터를 여기서 관리합니다.
"""

import os
from pathlib import Path

# ===== 경로 =====
BASE_DIR = Path(__file__).resolve().parent.parent          # backend/
MODELS_DIR = BASE_DIR / "models"
TEMP_DIR = BASE_DIR / "temp"                               # 다운로드 임시 영상
TEMP_DIR.mkdir(exist_ok=True)

# 모델 가중치 경로
YOLO_WEIGHTS = MODELS_DIR / "yolo" / "weights" / "yolov8n.pt"
MOTION_BERT_WEIGHTS = MODELS_DIR / "motion_bert" / "weights" / "mega_latest_epoch.bin"
GCN_MLP_WEIGHTS = MODELS_DIR / "gcn_mlp" / "weights" / "best_global_model.pth"
MEDIAPIPE_POSE_TASK = MODELS_DIR / "mediapipe" / "pose_landmarker_full.task"

# ===== 디바이스 =====
# 로컬 환경은 GPU 없음 → 항상 CPU
DEVICE = "cpu"

# ===== CPU 스레드 예산 =====
# analyze.py가 두 영상을 ThreadPoolExecutor로 병렬 처리할 때,
# 각 워커의 torch/OpenCV가 전체 코어를 점유하려 들면 경합이 발생.
# 여기서 정한 예산을 main.py lifespan에서 torch/cv2 전역으로 적용한다.
CPU_COUNT = os.cpu_count() or 4
PARALLEL_VIDEOS = 2                                    # analyze.py의 max_workers와 동일해야 함
TORCH_THREADS = max(1, CPU_COUNT // PARALLEL_VIDEOS)
CV2_THREADS = max(1, CPU_COUNT // PARALLEL_VIDEOS)

# ===== 로컬 영상 캐시 =====
# 업로드 직후 Supabase로 올린 영상을 로컬 TEMP_DIR에 {vid}.mp4로 보관해서
# 이어지는 /api/analyze 단계에서 재다운로드를 피한다.
CACHE_TTL_SEC = 3600                                   # 1시간 지나면 stale로 간주

# ===== 모델 하이퍼파라미터 =====
NUM_JOINTS = 17                # H36M 17 관절
BERT_DIM = 512                 # MotionBERT 출력 차원
GCN_HIDDEN = 256
GCN_OUT = 128

# ===== Supabase =====
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "videos")
