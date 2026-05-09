"""
LightweightGCN — H36M 17 관절 기반 GCN 인코더.
입력 : MotionBERT 임베딩  [B, F, 17, 512]  또는  [F, 17, 512]
출력 : GCN 임베딩          [B, F, 17, 128]  또는  [F, 17, 128]

GCN-SNN 논문 기반: 17 관절 인접 행렬 + 대칭 정규화 + 2-Layer (512→256→128)
원본은 GCN_MLP_model.ipynb 의 첫 번째 셀.
"""
import numpy as np
import torch
import torch.nn as nn
from core.config import NUM_JOINTS, BERT_DIM, GCN_HIDDEN, GCN_OUT


# H36M 17 관절 뼈 연결
H36M_BONES = [
    (0, 1), (1, 2), (2, 3),       # 오른쪽 다리
    (0, 4), (4, 5), (5, 6),       # 왼쪽 다리
    (0, 7), (7, 8), (8, 9), (9, 10),  # 척추 - 머리
    (8, 11), (11, 12), (12, 13),  # 왼쪽 팔
    (8, 14), (14, 15), (15, 16),  # 오른쪽 팔
]


def build_adjacency_matrix() -> np.ndarray:
    """17×17 인접 행렬 (self-loop 포함)"""
    A = np.zeros((NUM_JOINTS, NUM_JOINTS), dtype=np.float32)
    for i, j in H36M_BONES:
        A[i, j] = 1.0
        A[j, i] = 1.0
    A += np.eye(NUM_JOINTS, dtype=np.float32)
    return A


def normalize_adjacency(A: np.ndarray) -> np.ndarray:
    """대칭 정규화: A_norm = D^(-1/2) A D^(-1/2)"""
    D = np.diag(A.sum(axis=1))
    D_inv_sqrt = np.diag(1.0 / np.sqrt(np.diag(D) + 1e-8))
    return D_inv_sqrt @ A @ D_inv_sqrt


class SpatialGraphConv(nn.Module):
    def __init__(self, in_dim: int, out_dim: int, A_norm: np.ndarray):
        super().__init__()
        self.A = nn.Parameter(
            torch.tensor(A_norm, dtype=torch.float32),
            requires_grad=False,
        )
        self.W = nn.Linear(in_dim, out_dim, bias=True)
        self.bn = nn.BatchNorm1d(out_dim)
        self.relu = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, J, C]
        x = torch.matmul(self.A, x)
        x = self.W(x)
        B, J, C = x.shape
        x = x.reshape(B * J, C)
        x = self.bn(x)
        x = x.reshape(B, J, C)
        return self.relu(x)


class LightweightGCN(nn.Module):
    """2-Layer GCN: 512 → 256 → 128"""

    def __init__(
        self,
        in_dim: int = BERT_DIM,
        hidden_dim: int = GCN_HIDDEN,
        out_dim: int = GCN_OUT,
    ):
        super().__init__()
        A = build_adjacency_matrix()
        A_norm = normalize_adjacency(A)

        self.layer1 = SpatialGraphConv(in_dim, hidden_dim, A_norm)
        self.layer2 = SpatialGraphConv(hidden_dim, out_dim, A_norm)
        self.dropout = nn.Dropout(0.1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: [F, 17, 512] 또는 [B, F, 17, 512]
        out: 같은 shape에서 마지막 차원만 128
        """
        # 4D 입력이면 프레임 차원과 배치를 합쳐서 처리
        if x.dim() == 4:
            B, F, J, C = x.shape
            x = x.reshape(B * F, J, C)
            x = self.layer1(x)
            x = self.dropout(x)
            x = self.layer2(x)
            x = x.reshape(B, F, J, -1)
        else:
            x = self.layer1(x)
            x = self.dropout(x)
            x = self.layer2(x)
        return x
