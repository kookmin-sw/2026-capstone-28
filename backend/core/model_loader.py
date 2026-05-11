"""
모델 싱글톤 레지스트리.
서버가 시작될 때 한 번만 모델을 로드하고, 모든 파이프라인 단계가 공유합니다.
요청마다 모델을 다시 로드하면 매번 수십 초가 낭비되므로 절대 그렇게 만들지 마세요.

사용 예:
    from core.model_loader import ModelRegistry
    yolo = ModelRegistry.get().yolo
    bert = ModelRegistry.get().motion_bert
    sim = ModelRegistry.get().similarity_model
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


class ModelRegistry:
    _instance: "ModelRegistry | None" = None

    def __init__(self):
        # 각 모델 슬롯 — load_all() 호출 후에 채워집니다
        self.yolo = None             # ultralytics.YOLO
        self.hrnet = None   # mediapipe Pose 인스턴스
        self.motion_bert = None      # MotionBERT (DSTformer) torch.nn.Module
        self.similarity_model = None # GlobalSimilarityModel (GCN + Pooling + MLP 통합)
        self.gcn = None  
        self._loaded = False

    # ===== 싱글톤 접근 =====
    @classmethod
    def get(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ===== 전체 모델 로드 (서버 시작 시 1회) =====
    def load_all(self) -> None:
        if self._loaded:
            logger.warning("ModelRegistry.load_all() 이미 로드됨 — 무시")
            return

        logger.info("📦 모델 로드 시작...")
        self._load_yolo()
        self._load_hrnet()
        self._load_motion_bert()
        self._load_similarity_model()
        self._load_gcn()
        self._loaded = True
        logger.info("✅ 모든 모델 로드 완료")

    # ----- 개별 로더 -----
    def _load_yolo(self) -> None:
        from models.yolo.detector import load_yolo
        self.yolo = load_yolo()
        logger.info("  ✓ YOLO 로드 완료")

    def _load_hrnet(self) -> None:
        from models.HRnet.HRnet_loader import load_hrnet
        self.hrnet = load_hrnet()
        logger.info("  ✓ Hrnet 로드 완료")

    def _load_motion_bert(self) -> None:
        from models.motion_bert.embedder import load_motion_bert
        self.motion_bert = load_motion_bert()
        logger.info("  ✓ MotionBERT 로드 완료")

    def _load_similarity_model(self) -> None:
        from models.gcn_mlp.inferencer import load_global_similarity_model
        self.similarity_model = load_global_similarity_model()
        logger.info("  ✓ GlobalSimilarityModel 로드 완료")

    def _load_gcn(self) -> None:
        from models.gcn_mlp.inferencer import load_gcn_only
        self.gcn = load_gcn_only()
        logger.info("  ✓ GCN 로드 완료")