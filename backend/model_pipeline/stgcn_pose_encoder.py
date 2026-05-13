import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from core.config import DEVICE


# ============================================================
# ST-GCN Pose Encoder
# 입력: MotionBERT motion embedding [F, 17, 512]
# 출력: 최종 pose embedding [640]
# ============================================================

H36M_BONES = [
    (0, 1), (1, 2), (2, 3),
    (0, 4), (4, 5), (5, 6),
    (0, 7), (7, 8), (8, 9), (9, 10),
    (8, 11), (11, 12), (12, 13),
    (8, 14), (14, 15), (15, 16),
]

NUM_JOINTS = 17

BODY_PARTS = {
    "left_arm": [11, 12, 13],
    "right_arm": [14, 15, 16],
    "left_leg": [4, 5, 6],
    "right_leg": [1, 2, 3],
    "torso": [0, 7, 8, 9, 10],
}


def build_adjacency_matrix():
    A = np.zeros((NUM_JOINTS, NUM_JOINTS), dtype=np.float32)

    for i, j in H36M_BONES:
        A[i, j] = 1.0
        A[j, i] = 1.0

    A += np.eye(NUM_JOINTS, dtype=np.float32)

    return A


def normalize_adjacency(A):
    D = np.diag(A.sum(axis=1))
    D_inv = np.diag(1.0 / np.sqrt(np.diag(D) + 1e-8))
    return D_inv @ A @ D_inv


class HipCentering(nn.Module):
    """
    Hip joint index 0을 기준으로 나머지 관절 embedding을 상대 표현으로 변환.
    """

    def forward(self, x):
        # x: [..., 17, C]
        hip = x[..., 0:1, :]
        others = x[..., 1:, :] - hip
        return torch.cat([x[..., 0:1, :], others], dim=-2)


class SpatialGCN(nn.Module):
    """
    한 프레임 안에서 17개 관절 간 관계를 학습.
    """

    def __init__(self, in_dim, out_dim, A_norm):
        super().__init__()

        self.A = nn.Parameter(
            torch.tensor(A_norm, dtype=torch.float32),
            requires_grad=False,
        )

        self.W = nn.Linear(in_dim, out_dim)
        self.bn = nn.BatchNorm1d(out_dim)

    def forward(self, x):
        # x: [B*F, J, C]
        x = torch.matmul(self.A.to(x.device), x)
        x = self.W(x)

        BF, J, C = x.shape
        x = self.bn(x.reshape(BF * J, C)).reshape(BF, J, C)

        return F.relu(x)


class TemporalConv(nn.Module):
    """
    시간축 방향 convolution.
    """

    def __init__(self, channels, kernel_size=9):
        super().__init__()

        pad = kernel_size // 2

        self.conv = nn.Conv2d(
            channels,
            channels,
            kernel_size=(kernel_size, 1),
            padding=(pad, 0),
        )

        self.bn = nn.BatchNorm2d(channels)

    def forward(self, x):
        # x: [B, F, J, C]
        x = x.permute(0, 3, 1, 2)  # [B, C, F, J]
        x = F.relu(self.bn(self.conv(x)))
        x = x.permute(0, 2, 3, 1)  # [B, F, J, C]

        return x


class STGCNBlock(nn.Module):
    """
    Spatial GCN → Temporal Conv → Residual
    """

    def __init__(self, in_dim, out_dim, A_norm, t_kernel=9, dropout=0.1):
        super().__init__()

        self.spatial = SpatialGCN(in_dim, out_dim, A_norm)
        self.temporal = TemporalConv(out_dim, kernel_size=t_kernel)
        self.dropout = nn.Dropout(dropout)

        if in_dim != out_dim:
            self.residual = nn.Linear(in_dim, out_dim)
        else:
            self.residual = nn.Identity()

    def forward(self, x):
        # x: [B, F, J, C]
        B, F_, J, C = x.shape

        res = self.residual(x)

        x = x.reshape(B * F_, J, C)
        x = self.spatial(x)
        x = x.reshape(B, F_, J, -1)

        x = self.temporal(x)
        x = self.dropout(x)

        return x + res


class STGCNEncoder(nn.Module):
    """
    MotionBERT embedding을 ST-GCN에 통과시켜 관절-시간 정보를 반영한 표현 생성.

    입력:
        [F, 17, 512] 또는 [B, F, 17, 512]

    출력:
        [F, 17, 128] 또는 [B, F, 17, 128]
    """

    def __init__(
        self,
        in_dim=512,
        hidden_dim=256,
        out_dim=128,
        t_kernel=9,
        use_hip_centering=True,
    ):
        super().__init__()

        A_norm = normalize_adjacency(build_adjacency_matrix())

        self.hip_center = HipCentering() if use_hip_centering else nn.Identity()

        self.b1 = STGCNBlock(in_dim, hidden_dim, A_norm, t_kernel)
        self.b2 = STGCNBlock(hidden_dim, out_dim, A_norm, t_kernel)

    def forward(self, x):
        squeeze = False

        if x.dim() == 3:
            # [F, 17, 512] → [1, F, 17, 512]
            x = x.unsqueeze(0)
            squeeze = True

        x = self.hip_center(x)
        x = self.b1(x)
        x = self.b2(x)

        if squeeze:
            x = x.squeeze(0)

        return x


class AttnTemporalPool(nn.Module):
    """
    ST-GCN 결과 [F, 17, 128]을 부위별로 attention pooling.
    최종 pose embedding: 5개 body part * 128 = 640차원.
    """

    def __init__(self, dim=128, n_parts=5, n_heads=4, dropout=0.1):
        super().__init__()

        self.n_parts = n_parts
        self.cls = nn.Parameter(torch.randn(n_parts, 1, dim) * 0.02)

        self.attn = nn.MultiheadAttention(
            embed_dim=dim,
            num_heads=n_heads,
            dropout=dropout,
            batch_first=True,
        )

        self.norm = nn.LayerNorm(dim)
        self.parts = list(BODY_PARTS.values())

    def forward(self, x):
        # x: [F, 17, D]
        F_, J, D = x.shape

        outputs = []

        for p, idxs in enumerate(self.parts):
            # 부위별 관절 평균: [F, D]
            seq = x[:, idxs, :].mean(dim=1)

            # [1, F, D]
            seq = seq.unsqueeze(0)

            # CLS token: [1, 1, D]
            cls = self.cls[p].unsqueeze(0).to(x.device)

            # [1, F+1, D]
            seq = torch.cat([cls, seq], dim=1)
            seq = self.norm(seq)

            attn_out, _ = self.attn(seq, seq, seq, need_weights=False)

            # CLS 위치 사용: [1, D]
            outputs.append(attn_out[:, 0])

        # [5 * D]
        return torch.cat(outputs, dim=1).squeeze(0)


class STGCNPoseBranch(nn.Module):
    """
    MotionBERT embedding → ST-GCN → 최종 pose embedding
    """

    def __init__(
        self,
        in_dim=512,
        gcn_hidden=256,
        gcn_out=128,
        t_kernel=9,
        use_hip_centering=True,
    ):
        super().__init__()

        self.encoder = STGCNEncoder(
            in_dim=in_dim,
            hidden_dim=gcn_hidden,
            out_dim=gcn_out,
            t_kernel=t_kernel,
            use_hip_centering=use_hip_centering,
        )

        self.pool = AttnTemporalPool(
            dim=gcn_out,
            n_parts=len(BODY_PARTS),
        )

        self.output_dim = len(BODY_PARTS) * gcn_out  # 640


    def forward(self, emb):
        """
        Args:
            emb: [F, 17, 512]

        Returns:
            pose_embedding: [640]
        """
        x = self.encoder(emb)   # [F, 17, 128]
        z = self.pool(x)  # [640]

        return z


def _to_tensor_embedding(emb):
    """
    numpy 또는 torch 형태의 MotionBERT embedding을 tensor로 변환.
    예상 shape: [F, 17, 512]
    """

    if isinstance(emb, np.ndarray):
        emb = torch.tensor(emb, dtype=torch.float32)

    if not torch.is_tensor(emb):
        raise TypeError(f"지원하지 않는 embedding 타입입니다: {type(emb)}")

    if emb.dim() != 3:
        raise ValueError(f"embedding은 [F,17,512] 형태여야 합니다. 현재 shape={emb.shape}")

    if emb.shape[1] != 17:
        raise ValueError(f"관절 수는 17이어야 합니다. 현재 shape={emb.shape}")

    if emb.shape[2] != 512:
        raise ValueError(f"MotionBERT embedding 차원은 512여야 합니다. 현재 shape={emb.shape}")

    return emb.float().to(DEVICE)


def load_pose_branch(checkpoint_path=None):
    """
    ST-GCN Pose Branch 로드.

    checkpoint_path가 없으면 랜덤 초기화 상태.
    checkpoint_path가 있으면 전체 Pose+Tag checkpoint에서
    encoder / pool 부분만 골라서 로드함.
    """

    model = STGCNPoseBranch().to(DEVICE)

    if checkpoint_path is not None:
        ckpt = torch.load(checkpoint_path, map_location=DEVICE, weights_only=False)

        if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
            state_dict = ckpt["model_state_dict"]
        elif isinstance(ckpt, dict) and "state_dict" in ckpt:
            state_dict = ckpt["state_dict"]
        else:
            state_dict = ckpt

        pose_state = {}

        for k, v in state_dict.items():
            # 전체 PoseTag 모델 checkpoint 기준:
            # encoder.xxx, pool.xxx 만 pose branch에 해당
            if k.startswith("encoder."):
                pose_state[k] = v
            elif k.startswith("pool."):
                pose_state[k] = v

        missing, unexpected = model.load_state_dict(pose_state, strict=False)

        if len(pose_state) == 0:
            raise ValueError(
                "checkpoint에서 encoder/pool weight를 찾지 못했습니다. "
                "checkpoint가 PoseTagSTGCNSimilarityModel 형식인지 확인하세요."
            )

    model.eval()
    return model


def extract_pose_embedding(emb, checkpoint_path=None, model=None):
    """
    MotionBERT embedding 하나를 ST-GCN에 통과시켜 최종 pose embedding 생성.

    Args:
        emb: [F, 17, 512]
        checkpoint_path: 학습된 Pose+Tag checkpoint 경로
        model: 이미 로드된 STGCNPoseBranch

    Returns:
        np.ndarray [640]
    """

    if model is None:
        model = load_pose_branch(checkpoint_path)

    emb = _to_tensor_embedding(emb)

    with torch.no_grad():
        pose_embedding = model(emb)

    return pose_embedding.detach().cpu().numpy()


def extract_pair_pose_embeddings(emb_a, emb_b, checkpoint_path=None):
    """
    두 영상의 MotionBERT embedding을 각각 ST-GCN에 넣어 pose embedding 생성.

    Args:
        emb_a: [F, 17, 512]
        emb_b: [F, 17, 512]

    Returns:
        dict
    """

    model = load_pose_branch(checkpoint_path)

    pose_embedding_a = extract_pose_embedding(
        emb_a,
        model=model,
    )

    pose_embedding_b = extract_pose_embedding(
        emb_b,
        model=model,
    )

    return {
        "pose_embedding_a": pose_embedding_a,
        "pose_embedding_b": pose_embedding_b,
    }