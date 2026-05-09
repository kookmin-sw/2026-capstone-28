"""
Siamese MLP — 두 영상의 GCN 임베딩을 받아 유사도 점수를 출력.

⚠️ 이 파일은 골격입니다.
GCN_MLP_model.ipynb 의 두 번째 셀(학습 코드)에 정의된 SiameseMLP 클래스를
가져와서 forward 부분을 채워주세요.

입력  : (emb_a, emb_b)  각각 [B, 128] (Body Part Pooling + Temporal Pooling 거친 후)
출력  : 유사도 점수      [B, 1]  (0~1)
"""
import torch
import torch.nn as nn
from core.config import GCN_OUT
from .lightweight_gcn import LightweightGCN

BODY_PARTS = {
    'left_arm':  [11, 12, 13],
    'right_arm': [14, 15, 16],
    'left_leg':  [4, 5, 6],
    'right_leg': [1, 2, 3],
    'torso':     [0, 7, 8, 9, 10],
}

class BodyPartMotionPooling(nn.Module):
    def __init__(self, body_parts=BODY_PARTS):
        super().__init__()
        self.part_indices = [body_parts[k] for k in body_parts.keys()]

    def forward(self, x):
        F_len, J, D = x.shape
        part_pooled = []
        for indices in self.part_indices:
            part_feat = x[:, indices, :].mean(dim=1)
            if F_len > 1:
                velocity = torch.norm(part_feat[1:] - part_feat[:-1], dim=1)
                velocity = torch.cat([torch.zeros(1, device=x.device), velocity])
                weights = torch.softmax(velocity, dim=0).unsqueeze(1)
                pooled = (weights * part_feat).sum(dim=0)
            else:
                pooled = part_feat.squeeze(0)
            part_pooled.append(pooled)
        return torch.cat(part_pooled, dim=0)
    

class GlobalSimilarityModel(nn.Module):
    def __init__(self, in_dim=512, gcn_hidden=256, gcn_out=128):
        super().__init__()
        self.gcn = LightweightGCN(in_dim=in_dim, hidden_dim=gcn_hidden, out_dim=gcn_out)
        self.pooling = BodyPartMotionPooling()
        pooled_dim = 5 * gcn_out
        self.mlp = nn.Sequential(
            nn.Linear(pooled_dim * 2, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def encode(self, x):
        x = self.gcn(x)
        x = self.pooling(x)
        return x

    def forward(self, emb_a, emb_b):
        vec_a = self.encode(emb_a.squeeze(0))
        vec_b = self.encode(emb_b.squeeze(0))
        diff = torch.abs(vec_a - vec_b)
        prod = vec_a * vec_b
        combined = torch.cat([diff, prod], dim=0)
        return self.mlp(combined.unsqueeze(0)).squeeze()