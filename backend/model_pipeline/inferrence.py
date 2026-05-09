"""
GCN 기반 유사도 추론 파이프라인.
노트북 inference_pipeline.py 의 run_pipeline을 백엔드 함수로 이식.

[입력]  emb_a, emb_b : 각각 [F, 17, 512]  (MotionBERT 임베딩, embed_motion 출력)
[출력]  dict         : 노트북과 동일한 JSON 구조

[구조]
- Motion: GCN 128d + 5초 cross matching
- Pose:   raw 512d + 1초 sequential compare
- 전체 유사도 = Local Pose 전체 평균
"""
import numpy as np
import torch

from core.model_loader import ModelRegistry
from core.config import DEVICE


# ===== 파라미터 (노트북과 동일) =====
MOTION_SEGMENT_SEC = 5
POSE_SEGMENT_SEC = 1
FPS = 10
REMAP_FLOOR_MOTION = 0.5
REMAP_FLOOR_POSE = 0.2
MATCH_THRESHOLD = 0.5


# ===== 정적 구간 / 랭킹 파라미터 =====
STATIC_STD_THRESHOLD = 0.02   # 키포인트 좌표 표준편차가 이 값 이하면 정적
TOP_RATIO = 0.50             # best match 상위 25%만 추출

# ===== Body Part 정의 (노트북과 동일) =====
BODY_PARTS = {
    "left_arm":  [11, 12, 13],
    "right_arm": [14, 15, 16],
    "left_leg":  [4, 5, 6],
    "right_leg": [1, 2, 3],
    "torso":     [0, 7, 8, 9, 10],
}
PART_NAMES = list(BODY_PARTS.keys())


# ============================================================
# 유틸 — 노트북에서 그대로
# ============================================================
def _euclidean_sim(seg_a: torch.Tensor, seg_b: torch.Tensor, floor: float):
    """두 부위 풀링 결과의 유클리드 거리 → remap된 유사도."""
    dists = torch.norm(seg_a - seg_b, dim=1)
    sims = 1.0 / (1.0 + dists)
    sims = (sims - floor) / (1.0 - floor)
    sims = sims.clamp(0.0, 1.0)
    return sims.mean().item(), sims.cpu().numpy()


def _segment_split(tensor: torch.Tensor, seg_frames: int, min_ratio: float = 0.5):
    """tensor를 seg_frames 단위로 자르고, 각 구간의 (start_sec, end_sec) 함께 반환."""
    F_len = tensor.shape[0]
    segs, times = [], []
    for s in range(0, F_len, seg_frames):
        e = min(s + seg_frames, F_len)
        if e - s < seg_frames * min_ratio:
            break
        segs.append(tensor[s:e])
        times.append((s / FPS, e / FPS))
    return segs, times


def _body_part_pool(segment: torch.Tensor) -> torch.Tensor:
    """[F, 17, D] 구간을 5개 신체 부위 임베딩으로 풀링."""
    parts = []
    for idx in BODY_PARTS.values():
        parts.append(segment[:, idx, :].mean(dim=1).mean(dim=0))
    return torch.stack(parts)   # [5, D]

def _compute_motion_energy(segment: torch.Tensor) -> float:
    """
    Segment의 총 움직임 양 (motion energy) 계산.
    각 부위의 시간축 velocity 합 → 5개 부위 평균.
    
    Args:
        segment: [F, 17, D]  GCN 임베딩 segment
    
    Returns:
        scalar — segment의 motion energy (가중치로 사용)
    """
    energies = []
    for indices in BODY_PARTS.values():
        # 부위별 임베딩 [F, D]
        part_feat = segment[:, indices, :].mean(dim=1)
        
        if part_feat.shape[0] > 1:
            # 시간축 velocity의 합
            velocity = torch.norm(part_feat[1:] - part_feat[:-1], dim=1)
            energies.append(velocity.sum().item())
        else:
            energies.append(0.0)
    
    # 5개 부위 평균
    return sum(energies) / len(energies) if energies else 0.0

def _is_static_segment(kps_segment: np.ndarray, threshold: float = STATIC_STD_THRESHOLD) -> bool:
    """
    Segment가 정적 동작(가만히 서 있음)인지 판정.
    
    좌표(x, y)의 시간축 표준편차 평균이 threshold 이하면 정적으로 간주.
    visibility는 무시하고 좌표만 봄.
    
    Args:
        kps_segment: [F, 17, 3]  numpy — 5초 단위로 자른 키포인트
        threshold: 정적 판정 임계값
    
    Returns:
        True면 정적 (매칭에서 제외)
    """
    xy = kps_segment[..., :2]   # [F, 17, 2]  visibility 제외
    
    # 각 (관절, 좌표축)별로 시간축 표준편차 → 17 × 2 값
    # 그 평균이 작으면 = 시간이 흘러도 거의 안 움직임
    motion_std = xy.std(axis=0).mean()   # scalar
    
    return motion_std < threshold


def _split_keypoints(kps: np.ndarray, seg_frames: int, min_ratio: float = 0.5):
    """
    키포인트를 segment로 분할. _segment_split의 numpy 버전.
    GCN 임베딩과 동일한 인덱스로 잘라야 정적 판정 결과가 일치함.
    """
    F_len = kps.shape[0]
    segs = []
    for s in range(0, F_len, seg_frames):
        e = min(s + seg_frames, F_len)
        if e - s < seg_frames * min_ratio:
            break
        segs.append(kps[s:e])
    return segs


# ============================================================
# 메인 진입점
# ============================================================
def infer_similarity(
    emb_a: np.ndarray,
    emb_b: np.ndarray,
    kps_a: np.ndarray,    # ⭐ 추가
    kps_b: np.ndarray,    # ⭐ 추가
) -> dict:
    """
    노트북 run_pipeline을 백엔드 함수로 이식.
    
    Args:
        emb_a, emb_b: [F, 17, 512]  MotionBERT 임베딩
        kps_a, kps_b: [F, 17, 3]    원본 키포인트 (정적 구간 판정용)
    
    Returns:
        dict — global_score, motion_segments, ...
    """
    _validate(emb_a, "emb_a")
    _validate(emb_b, "emb_b")
    
    gcn = ModelRegistry.get().gcn
    if gcn is None:
        raise RuntimeError("GCN이 로드되지 않았습니다.")
    
    emb_a_t = torch.from_numpy(emb_a).float().to(DEVICE)
    emb_b_t = torch.from_numpy(emb_b).float().to(DEVICE)
    
    # ============================================================
    # Step 1: Local Motion (5초, GCN 128d, Cross Matching)
    # ============================================================
    with torch.no_grad():
        gcn_a = gcn(emb_a_t)
        gcn_b = gcn(emb_b_t)
    
    mf = MOTION_SEGMENT_SEC * FPS
    m_segs_a, m_times_a = _segment_split(gcn_a, mf)
    m_segs_b, m_times_b = _segment_split(gcn_b, mf)
    
    if not m_segs_a or not m_segs_b:
        return _empty_result()
    
    m_pool_a = [_body_part_pool(s) for s in m_segs_a]
    m_pool_b = [_body_part_pool(s) for s in m_segs_b]
    
    # ⭐ 정적 구간 판정 — 같은 인덱스로 키포인트 자르기
    kps_segs_a = _split_keypoints(kps_a, mf)
    kps_segs_b = _split_keypoints(kps_b, mf)
    static_a = [_is_static_segment(s) for s in kps_segs_a]
    static_b = [_is_static_segment(s) for s in kps_segs_b]
    
    n_static_a = sum(static_a)
    n_static_b = sum(static_b)
    print(f"  정적 segment 제외: A {n_static_a}/{len(static_a)}, B {n_static_b}/{len(static_b)}")
    
    Na, Nb = len(m_pool_a), len(m_pool_b)
    sim_mat = np.zeros((Na, Nb))
    psim_mat = np.zeros((Na, Nb, 5))
    
    for i in range(Na):
        for j in range(Nb):
            sim, ps = _euclidean_sim(m_pool_a[i], m_pool_b[j], REMAP_FLOOR_MOTION)
            sim_mat[i, j] = sim
            psim_mat[i, j] = ps
    
    # ⭐ 정적 segment는 -inf로 마스킹 (argmax에서 절대 안 뽑힘)
    for i in range(Na):
        if static_a[i]:
            sim_mat[i, :] = -np.inf
    for j in range(Nb):
        if static_b[j]:
            sim_mat[:, j] = -np.inf
    
    # A 기준 best match 추출
    all_matches = []
    weighted_sum = 0.0    # ⭐ 가중평균 분자
    weight_total = 0.0    # ⭐ 가중평균 분모

    for i in range(Na):
        if static_a[i]:
            continue
        
        bj = int(np.argmax(sim_mat[i]))
        bs = sim_mat[i, bj]
        
        if bs == -np.inf or static_b[bj]:
            continue
        
        # ⭐ segment의 motion energy를 가중치로 사용
        energy = _compute_motion_energy(m_segs_a[i])
        weighted_sum += bs * energy
        weight_total += energy
        
        all_matches.append({
            "idx_a": i,
            "idx_b": bj,
            "time_a_str": f"{m_times_a[i][0]:.0f}~{m_times_a[i][1]:.0f}s",
            "time_b_str": f"{m_times_b[bj][0]:.0f}~{m_times_b[bj][1]:.0f}s",
            "time_a_sec": m_times_a[i],
            "time_b_sec": m_times_b[bj],
            "motion_sim": round(float(bs), 4),
            "motion_body_parts": {
                n: round(float(psim_mat[i, bj, k]), 4)
                for k, n in enumerate(PART_NAMES)
            },
        })

    # ⭐ Global score = motion_sim의 가중평균 (motion energy로 가중)
    if weight_total > 0:
        global_score = weighted_sum / weight_total
    else:
        global_score = 0.0

    # Top 25% 추출 (motion_segments 출력용)
    all_matches.sort(key=lambda x: x["motion_sim"], reverse=True)
    top_n = max(1, int(np.ceil(len(all_matches) * TOP_RATIO))) if all_matches else 0
    motion_matches = all_matches[:top_n]
    
    # # ⭐ Top 25% 추출 (최소 1개 보장)
    # all_matches.sort(key=lambda x: x["motion_sim"], reverse=True)
    # top_n = max(1, int(np.ceil(len(all_matches) * TOP_RATIO))) if all_matches else 0
    # motion_matches = all_matches[:top_n]
    # print(f"  Top {TOP_RATIO * 100:.0f}% 매칭: {len(all_matches)}개 → {len(motion_matches)}개 선정")
    
    # ============================================================
    # Step 2: Local Pose (1초, raw 512d, Sequential)
    # ============================================================
    pf = POSE_SEGMENT_SEC * FPS
    all_pose_sims = []
    
    for m in motion_matches:
        as_ = int(m["time_a_sec"][0] * FPS)
        ae  = int(m["time_a_sec"][1] * FPS)
        bs_ = int(m["time_b_sec"][0] * FPS)
        be  = int(m["time_b_sec"][1] * FPS)
        
        chunk_a = emb_a_t[as_:ae]
        chunk_b = emb_b_t[bs_:be]
        
        p_segs_a, p_times_a = _segment_split(chunk_a, pf)
        p_segs_b, p_times_b = _segment_split(chunk_b, pf)
        
        p_times_a = [(t[0] + m["time_a_sec"][0], t[1] + m["time_a_sec"][0]) for t in p_times_a]
        p_times_b = [(t[0] + m["time_b_sec"][0], t[1] + m["time_b_sec"][0]) for t in p_times_b]
        
        n_compare = min(len(p_segs_a), len(p_segs_b))
        m["pose_detail"] = []
        
        for k in range(n_compare):
            pa = _body_part_pool(p_segs_a[k])
            pb = _body_part_pool(p_segs_b[k])
            sim, ps = _euclidean_sim(pa, pb, REMAP_FLOOR_POSE)
            all_pose_sims.append(sim)
            m["pose_detail"].append({
                "time_a": f"{p_times_a[k][0]:.0f}~{p_times_a[k][1]:.0f}s",
                "time_b": f"{p_times_b[k][0]:.0f}~{p_times_b[k][1]:.0f}s",
                "pose_sim": round(sim, 4),
                "body_parts": {
                    n: round(float(ps[i]), 4) for i, n in enumerate(PART_NAMES)
                },
            })
    
    # global_score = float(np.mean(all_pose_sims)) if all_pose_sims else 0.0
    
    # ============================================================
    # Step 3: 결과 dict 조립
    # ============================================================
    return {
        "global_score": round(global_score, 4),
        "top_ratio": TOP_RATIO,
        "static_threshold": STATIC_STD_THRESHOLD,
        "remap_floor_motion": REMAP_FLOOR_MOTION,
        "remap_floor_pose": REMAP_FLOOR_POSE,
        "motion_segments": [
            {
                "id": idx + 1,                    # 1부터 시작하는 번호
                "time_a": m["time_a_str"],
                "time_b": m["time_b_str"],
                "motion_sim": m["motion_sim"],
                "motion_body_parts": m["motion_body_parts"],
                "pose_detail": m.get("pose_detail", []),
            }
            for idx, m in enumerate(motion_matches)
        ],
    }


# ============================================================
# 헬퍼
# ============================================================
def _validate(emb: np.ndarray, name: str) -> None:
    if not isinstance(emb, np.ndarray):
        raise ValueError(f"{name}는 numpy ndarray여야 합니다. 현재: {type(emb)}")
    if emb.ndim != 3 or emb.shape[1] != 17 or emb.shape[2] != 512:
        raise ValueError(
            f"{name} shape은 [F, 17, 512]여야 합니다. 현재: {emb.shape}"
        )
    if emb.shape[0] == 0:
        raise ValueError(f"{name}의 프레임 수가 0입니다.")


def _empty_result() -> dict:
    """영상이 너무 짧아서 5초 단위 분할이 불가능한 경우."""
    return {
        "global_score": 0.0,
        "match_threshold": MATCH_THRESHOLD,
        "remap_floor_motion": REMAP_FLOOR_MOTION,
        "remap_floor_pose": REMAP_FLOOR_POSE,
        "motion_segments": [],
    }