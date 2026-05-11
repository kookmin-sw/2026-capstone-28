import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from core.config import DEVICE


class PoseTagFusionModel(nn.Module):
    """
    ST-GCN pose embedding + tag vector를 결합해서 최종 similarity score 계산.

    입력:
        pose_embedding_a: [640]
        pose_embedding_b: [640]
        tag_vector: [tag_dim]

    출력:
        similarity_score: scalar
    """

    def __init__(self, pose_dim=640, tag_dim=64, tag_hidden=128, fusion_hidden=256):
        super().__init__()

        self.pose_dim = pose_dim
        self.tag_dim = tag_dim

        self.tag_encoder = nn.Sequential(
            nn.Linear(tag_dim, tag_hidden),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(tag_hidden, tag_hidden),
            nn.ReLU(),
        )

        self.fusion_mlp = nn.Sequential(
            nn.Linear(pose_dim * 4 + tag_hidden, fusion_hidden),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(fusion_hidden, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 1),
            nn.Sigmoid(),
        )

    def forward(self, pose_a, pose_b, tag_vector):
        """
        Args:
            pose_a: [B, 640]
            pose_b: [B, 640]
            tag_vector: [B, tag_dim]

        Returns:
            score: [B]
        """

        diff = torch.abs(pose_a - pose_b)
        prod = pose_a * pose_b

        pose_pair = torch.cat(
            [pose_a, pose_b, diff, prod],
            dim=-1,
        )

        tag_emb = self.tag_encoder(tag_vector)

        fused = torch.cat(
            [pose_pair, tag_emb],
            dim=-1,
        )

        score = self.fusion_mlp(fused).squeeze(-1)

        return score


def _to_tensor_2d(x, name):
    if isinstance(x, np.ndarray):
        x = torch.tensor(x, dtype=torch.float32)

    if not torch.is_tensor(x):
        raise TypeError(f"{name} 타입이 잘못되었습니다: {type(x)}")

    if x.dim() == 1:
        x = x.unsqueeze(0)

    if x.dim() != 2:
        raise ValueError(f"{name}은 [D] 또는 [B,D] 형태여야 합니다. 현재 shape={x.shape}")

    return x.float().to(DEVICE)


def load_pose_tag_fusion_model(checkpoint_path=None, pose_dim=640, tag_dim=64):
    model = PoseTagFusionModel(
        pose_dim=pose_dim,
        tag_dim=tag_dim,
    ).to(DEVICE)

    if checkpoint_path is not None:
        ckpt = torch.load(checkpoint_path, map_location=DEVICE, weights_only=False)

        if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
            state_dict = ckpt["model_state_dict"]
        elif isinstance(ckpt, dict) and "state_dict" in ckpt:
            state_dict = ckpt["state_dict"]
        else:
            state_dict = ckpt

        fusion_state = {}

        for k, v in state_dict.items():
            if k.startswith("tag_encoder.") or k.startswith("fusion_mlp."):
                fusion_state[k] = v

        if len(fusion_state) > 0:
            model.load_state_dict(fusion_state, strict=False)

    model.eval()
    return model


def run_pose_tag_similarity(
    pose_embedding_a,
    pose_embedding_b,
    tag_vector,
    checkpoint_path=None,
):
    """
    ST-GCN pose embedding과 tag vector를 결합해 similarity 계산.

    Args:
        pose_embedding_a: np.ndarray [640]
        pose_embedding_b: np.ndarray [640]
        tag_vector: np.ndarray [tag_dim]
        checkpoint_path: 학습된 checkpoint 경로

    Returns:
        dict
    """

    pose_a = _to_tensor_2d(pose_embedding_a, "pose_embedding_a")
    pose_b = _to_tensor_2d(pose_embedding_b, "pose_embedding_b")
    tag = _to_tensor_2d(tag_vector, "tag_vector")

    model = load_pose_tag_fusion_model(
        checkpoint_path=checkpoint_path,
        pose_dim=pose_a.shape[-1],
        tag_dim=tag.shape[-1],
    )

    with torch.no_grad():
        score = model(pose_a, pose_b, tag)

    return {
        "similarity_score": float(score.detach().cpu().numpy()[0]),
        "pose_embedding_a": pose_embedding_a,
        "pose_embedding_b": pose_embedding_b,
        "tag_vector": tag_vector,
    }