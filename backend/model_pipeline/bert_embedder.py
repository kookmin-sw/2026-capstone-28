
import numpy as np
import torch

from core.model_loader import ModelRegistry
from core.config import DEVICE


def embed_motion(keypoints: np.ndarray) -> np.ndarray:

    # 입력 검증
    if keypoints.ndim != 3 or keypoints.shape[1] != 17 or keypoints.shape[2] != 3:
        raise ValueError(
            f"keypoints shape이 [F, 17, 3]이어야 합니다. 현재: {keypoints.shape}"
        )
    
    F = keypoints.shape[0]
    if F == 0:
        raise ValueError("프레임 수가 0입니다.")
    if F > 243:
        raise ValueError(
            f"프레임 수가 {F}로 maxlen(243)을 초과합니다. "
            "extract_object_from_path에서 240으로 자르세요."
        )
    
    # 모델 가져오기 (싱글톤 — 이미 로드된 상태)
    model = ModelRegistry.get().motion_bert
    if model is None:
        raise RuntimeError(
            "MotionBERT가 로드되지 않았습니다. ModelRegistry.get().load_all()을 먼저 호출하세요."
        )
    
    # numpy → torch tensor, 배치 차원 추가
    # [F, 17, 3] → [1, F, 17, 3]
    x = torch.from_numpy(keypoints).float().unsqueeze(0).to(DEVICE)
    
    # 추론 — gradient 계산 끄기 (CPU 메모리/속도 절약)
    with torch.no_grad():
        rep = model(x, return_rep=True)
    
    # 배치 차원 제거 + numpy로 변환
    # [1, F, 17, 512] → [F, 17, 512]
    embedding = rep.squeeze(0).cpu().numpy()
    
    return embedding