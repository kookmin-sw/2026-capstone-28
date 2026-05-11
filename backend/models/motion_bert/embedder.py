"""
MotionBERT 임베딩 모델 로더 및 추론 래퍼.
입력  : 2D 키포인트 시퀀스 [B, F, 17, 3]  (x, y, confidence)
출력  : 임베딩 시퀀스       [B, F, 17, 512]
"""
import torch
from core.config import MOTION_BERT_WEIGHTS, DEVICE
from .architecture import DSTformer


def load_motion_bert():
    """
    MotionBERT 가중치(mega_latest_epoch.bin) 로드.
    추론 전용이므로 eval() 모드 + grad 비활성화.
    """
    if not MOTION_BERT_WEIGHTS.exists():
        raise FileNotFoundError(
            f"MotionBERT 가중치를 찾을 수 없습니다: {MOTION_BERT_WEIGHTS}\n"
            f"models/motion_bert/weights/ 폴더에 mega_latest_epoch.bin 파일을 넣어주세요."
        )

    # 1. 모델 인스턴스 생성 (공식 default config)
    model = DSTformer(
        dim_in=3, dim_out=3,
        dim_feat=512, dim_rep=512,
        depth=5, num_heads=8, mlp_ratio=2,
        num_joints=17, maxlen=243,
    )

    # 2. 가중치 로드 (CPU)
    checkpoint = torch.load(MOTION_BERT_WEIGHTS, map_location=DEVICE, weights_only=False)
    # 공식 checkpoint는 보통 {"model_pos": state_dict} 형태
    state_dict = checkpoint.get("model_pos", checkpoint)
    # 'module.' 접두사 제거 (DataParallel로 저장된 경우)
    state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}
    model.load_state_dict(state_dict, strict=False)

    # 3. 추론 모드
    model.to(DEVICE).eval()
    for p in model.parameters():
        p.requires_grad = False

    return model
