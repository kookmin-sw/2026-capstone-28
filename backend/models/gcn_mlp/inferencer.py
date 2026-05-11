"""
GlobalSimilarityModel 추론 로더.
best_global_model.pth 가중치 한 덩어리로 GCN + Pooling + MLP 전체를 불러옵니다.
"""
import torch
from core.config import GCN_MLP_WEIGHTS, DEVICE
from .siamese_mlp import GlobalSimilarityModel
from .lightweight_gcn import LightweightGCN

def load_gcn_only() -> LightweightGCN:
    """
    best_global_model.pth에서 GCN 부분만 추출해서 LightweightGCN 인스턴스에 로드.
    노트북 inference_pipeline.py 의 GCN 로드 부분과 동일.
    """
    if not GCN_MLP_WEIGHTS.exists():
        raise FileNotFoundError(
            f"가중치를 찾을 수 없습니다: {GCN_MLP_WEIGHTS}"
        )

    gcn = LightweightGCN(in_dim=512, hidden_dim=256, out_dim=128)

    checkpoint = torch.load(GCN_MLP_WEIGHTS, map_location=DEVICE, weights_only=False)
    state_dict = checkpoint.get("model_state_dict", checkpoint)

    # 'gcn.' 접두사 붙은 가중치만 추출
    gcn_state = {
        k.replace("gcn.", ""): v
        for k, v in state_dict.items()
        if k.startswith("gcn.")
    }

    gcn.load_state_dict(gcn_state)
    gcn.to(DEVICE).eval()
    for p in gcn.parameters():
        p.requires_grad = False

    print(f"GCN 로드 완료 (v1, 2-layer, 128d) | Device: {DEVICE}")
    return gcn


def load_global_similarity_model() -> GlobalSimilarityModel:
    if not GCN_MLP_WEIGHTS.exists():
        raise FileNotFoundError(
            f"가중치를 찾을 수 없습니다: {GCN_MLP_WEIGHTS}\n"
            f"models/gcn_mlp/weights/ 폴더에 best_global_model.pth 파일을 넣어주세요."
        )

    model = GlobalSimilarityModel(in_dim=512, gcn_hidden=256, gcn_out=128)

    checkpoint = torch.load(GCN_MLP_WEIGHTS, map_location=DEVICE, weights_only=False)

    # checkpoint 형태 확인 — 보통 {"model_state_dict": ...} 또는 직접 state_dict
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        state_dict = checkpoint["model_state_dict"]
    else:
        state_dict = checkpoint

    # 'module.' 접두사 제거 (DataParallel로 저장된 경우)
    state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}

    missing, unexpected = model.load_state_dict(state_dict, strict=False)
    if missing:
        print(f"⚠️ Missing keys: {missing}")
    if unexpected:
        print(f"⚠️ Unexpected keys: {unexpected}")

    model.to(DEVICE).eval()
    for p in model.parameters():
        p.requires_grad = False

    return model