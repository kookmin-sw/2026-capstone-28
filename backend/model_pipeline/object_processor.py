
import numpy as np

# H36M 인덱스
HIP_IDX = 0       # 골반 중점 (원점)
THORAX_IDX = 8    # 흉부 중점 (어깨 중점)


def torso_normalize(kps_seq: np.ndarray) -> np.ndarray:

    out = kps_seq.copy().astype(np.float32)
    xy = out[..., :2]   # [F, 17, 2]

    # 1. 원점 이동 — Hip을 (0, 0)으로
    hip = xy[:, HIP_IDX:HIP_IDX + 1, :]   # [F, 1, 2]
    xy_centered = xy - hip                # [F, 17, 2]

    # 2. 스케일 정규화 — torso 길이로 나누기
    #    torso 벡터 = Hip(0) → Thorax(8)
    #    Hip이 원점이므로 Thorax 좌표 자체가 torso 벡터
    torso_vec = xy_centered[:, THORAX_IDX, :]              # [F, 2]
    torso_len = np.linalg.norm(torso_vec, axis=-1)         # [F]
    torso_len = np.maximum(torso_len, 1e-6)                # 0 나누기 방지
    torso_len = torso_len[:, None, None]                   # [F, 1, 1] 브로드캐스트용

    xy_normalized = xy_centered / torso_len                # [F, 17, 2]

    out[..., :2] = xy_normalized
    return out


def center_to_unit_range(kps_seq: np.ndarray, clip: bool = True) -> np.ndarray:

    out = kps_seq.copy()
    if clip:
        out[..., :2] = np.clip(out[..., :2], -1.5, 1.5)
    return out


def preprocess_for_motionbert(kps_seq: np.ndarray) -> np.ndarray:

    kps_seq = torso_normalize(kps_seq)
    kps_seq = center_to_unit_range(kps_seq, clip=True)
    return kps_seq