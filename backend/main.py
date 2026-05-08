"""
FastAPI 진입점.
서버 시작 시 모델을 한 번만 로드하고, 종료 시 정리합니다.
"""

from dotenv import load_dotenv
load_dotenv()

# ===== CPU 스레드 예산 (torch/OpenMP import 이전에 환경변수 지정) =====
# torch 백엔드(OpenMP/MKL)는 프로세스 초기에 환경변수를 읽어서 스레드 풀을 만든다.
# core.model_loader → ultralytics → torch 체인이 아래 import보다 먼저 발생하지 않도록
# 이 블록은 반드시 다른 무거운 import 위에 둔다.
import os
from core.config import TORCH_THREADS, CV2_THREADS

os.environ.setdefault("OMP_NUM_THREADS", str(TORCH_THREADS))
os.environ.setdefault("MKL_NUM_THREADS", str(TORCH_THREADS))
os.environ.setdefault("OPENBLAS_NUM_THREADS", str(TORCH_THREADS))

import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import TEMP_DIR, CACHE_TTL_SEC
from core.model_loader import ModelRegistry

# ===== 로깅 =====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ===== Lifespan: 서버 시작/종료 시 1회만 실행 =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 서버 시작 — 모델 로딩 중...")

    # torch/cv2 스레드 예산을 프로세스 전역으로 고정.
    # (환경변수는 위쪽에서 이미 export됨 — 여기서는 Python API로 한 번 더 맞춘다)
    import torch
    import cv2
    torch.set_num_threads(TORCH_THREADS)
    try:
        torch.set_num_interop_threads(TORCH_THREADS)
    except RuntimeError:
        # 이미 다른 코드가 interop 스레드를 건드렸으면 경고만 남기고 진행
        logger.warning("torch.set_num_interop_threads 실패 — 이미 초기화된 것으로 간주")
    cv2.setNumThreads(CV2_THREADS)
    logger.info(f"  · 스레드 예산 설정: torch={TORCH_THREADS}, cv2={CV2_THREADS}")

    # 1시간 넘은 로컬 영상 캐시 정리 (업로드-분석 간 재사용용 {vid}.mp4 파일들)
    _cleanup_stale_cache()

    ModelRegistry.get().load_all()
    logger.info("✅ 서버 준비 완료")
    yield
    logger.info("🛑 서버 종료")


def _cleanup_stale_cache() -> None:
    """TEMP_DIR 내부에서 CACHE_TTL_SEC을 초과한 mp4 파일을 삭제한다."""
    now = time.time()
    removed = 0
    for f in TEMP_DIR.glob("*.mp4"):
        try:
            if now - f.stat().st_mtime > CACHE_TTL_SEC:
                f.unlink()
                removed += 1
        except OSError as e:
            logger.warning(f"캐시 정리 실패: {f.name} ({e})")
    if removed:
        logger.info(f"  · 오래된 캐시 {removed}개 삭제")


# ===== FastAPI 앱 =====
app = FastAPI(
    title="Tenein · K-pop Visual Studio API",
    description="K-pop 안무 영상 비교 분석 백엔드",
    version="0.1.0",
    lifespan=lifespan,
)

# ===== CORS — 프론트엔드(Vite localhost:5173) 허용 =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Health check =====
@app.get("/")
def root():
    return {"status": "ok", "service": "Tenein API"}


@app.get("/health")
def health():
    registry = ModelRegistry.get()
    return {
        "status": "healthy",
        "models_loaded": registry._loaded,
    }


# ===== 라우터 등록 =====
from api.video_upload import router as upload_router
app.include_router(upload_router, prefix="/api/videos", tags=["videos"])

from api.router import router as analyze_router
app.include_router(analyze_router, prefix="/api", tags=["analyze"])