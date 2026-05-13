"""
Pose+Tag 유사도 추론 파이프라인.

[입력]
  emb_a, emb_b             : [F, 17, 512]  MotionBERT 임베딩
  keypoints_a, keypoints_b : [F, 17, 3]    HRNet 2D 키포인트
  fps_a, fps_b             : 원본 영상 fps

[출력]
  dict — LLM agent(generate_similarity_report) 입력 스키마와 호환

[구조]
  - Global Score : run_pose_tag_similarity (ST-GCN pose embedding + tag vector)
  - Motion (5초) : HRNet keypoints 좌표+속도+가속도 기반 motion-aware similarity
  - Refine       : ±2초 sliding window로 정밀 정렬
  - Pose (1초)   : HRNet keypoints 기반 부위별 pose similarity
  - Tag (1초)    : 관절 각도/방향/속도 등 feature 비교 → support_score, tags, evidence
"""
import os
import numpy as np
import torch

from model_pipeline.stgcn_pose_encoder import load_pose_branch
from model_pipeline.tag_extractor import generate_pair_tags
from model_pipeline.pose_tag import run_pose_tag_similarity

from core.config import DEVICE


# ===== 파라미터 =====
MOTION_SEGMENT_SEC = 5
POSE_SEGMENT_SEC = 1
FPS = 10
REMAP_FLOOR_POSE = 0.2
TOP_PERCENT = 0.25
MIN_SIM_THRESHOLD = 0.60

# Coarse-to-Fine Refine
REFINE_MARGIN_SEC = 2
REFINE_STRIDE_SEC = 1
REFINE_WINDOW_SEC = 5

# Body Part 정의 (H36M-17 기준)
BODY_PARTS = {
    "torso":     [0, 7, 8, 9, 10],
    "left_arm":  [11, 12, 13],
    "right_arm": [14, 15, 16],
    "left_leg":  [4, 5, 6],
    "right_leg": [1, 2, 3],
}
PART_NAMES = list(BODY_PARTS.keys())

# H36M-17 관절 인덱스 (tag feature 추출용)
H36M17 = {
    "pelvis": 0, "right_hip": 1, "right_knee": 2, "right_ankle": 3,
    "left_hip": 4, "left_knee": 5, "left_ankle": 6,
    "spine": 7, "thorax": 8, "neck": 9, "head": 10,
    "left_shoulder": 11, "left_elbow": 12, "left_wrist": 13,
    "right_shoulder": 14, "right_elbow": 15, "right_wrist": 16,
}

POSE_TAG_CKPT_PATH = os.getenv(
    "POSE_TAG_CKPT_PATH",
    "model_pipeline/checkpoint/best_pose_tag_corr.pth",
)


# ============================================================
# Motion-aware similarity 유틸 (노트북 기준)
# ============================================================
def _normalize_pose_segment(seg: np.ndarray) -> np.ndarray:
    """hip center 기준 정렬 + 몸통 길이 기준 scale normalize."""
    seg = np.asarray(seg, dtype=np.float32).copy()
    hip_center = (seg[:, 11:12, :] + seg[:, 12:13, :]) / 2.0
    seg = seg - hip_center
    shoulder_center = (seg[:, 5, :] + seg[:, 6, :]) / 2.0
    hip_center_after = (seg[:, 11, :] + seg[:, 12, :]) / 2.0
    torso_len = np.linalg.norm(shoulder_center - hip_center_after, axis=-1)
    scale = np.nanmean(torso_len)
    if not np.isfinite(scale) or scale < 1e-6:
        scale = np.nanstd(seg) + 1e-6
    seg = seg / (scale + 1e-6)
    return seg


def _get_motion_feature(seg: np.ndarray, part_idxs: list) -> np.ndarray:
    """좌표 + 속도 + 가속도 기반 feature 생성."""
    part = seg[:, part_idxs, :]
    pose_feat = part.reshape(part.shape[0], -1)
    if part.shape[0] >= 2:
        vel = np.diff(part, axis=0)
        vel_feat = vel.reshape(vel.shape[0], -1)
    else:
        vel_feat = np.zeros((1, len(part_idxs) * 3), dtype=np.float32)
    if part.shape[0] >= 3:
        acc = np.diff(vel, axis=0)
        acc_feat = acc.reshape(acc.shape[0], -1)
    else:
        acc_feat = np.zeros((1, len(part_idxs) * 3), dtype=np.float32)
    feat = np.concatenate([
        pose_feat.mean(axis=0), pose_feat.std(axis=0),
        vel_feat.mean(axis=0), vel_feat.std(axis=0),
        acc_feat.mean(axis=0), acc_feat.std(axis=0),
    ], axis=0)
    return feat.astype(np.float32)


def _distance_to_similarity(dist: float, alpha: float = 5.0) -> float:
    sim = np.exp(-alpha * dist)
    return float(np.clip(sim, 0.0, 1.0))


def _pose_motion_similarity(
    seg_a: np.ndarray, seg_b: np.ndarray, alpha: float = 5.0,
) -> tuple:
    """
    HRNet keypoints 기반 motion-aware similarity.
    Returns: (overall_sim, {part_name: sim})
    """
    T = min(seg_a.shape[0], seg_b.shape[0])
    if T < 3:
        return 0.0, {p: 0.0 for p in PART_NAMES}
    a = _normalize_pose_segment(seg_a[:T])
    b = _normalize_pose_segment(seg_b[:T])
    part_sims = {}
    for part_name in PART_NAMES:
        idxs = BODY_PARTS[part_name]
        fa = _get_motion_feature(a, idxs)
        fb = _get_motion_feature(b, idxs)
        denom = np.linalg.norm(fa) + np.linalg.norm(fb) + 1e-6
        dist = np.linalg.norm(fa - fb) / denom
        part_sims[part_name] = _distance_to_similarity(dist, alpha=alpha)
    overall = float(np.mean(list(part_sims.values())))
    return overall, part_sims


# ============================================================
# Segment 분할 유틸
# ============================================================
def _split_segments(arr: np.ndarray, window_frames: int) -> tuple:
    """numpy array를 window_frames 단위로 분할."""
    F_len = arr.shape[0]
    segments, times = [], []
    for start in range(0, F_len, window_frames):
        end = min(start + window_frames, F_len)
        if end - start < max(2, window_frames // 2):
            continue
        segments.append(arr[start:end])
        times.append((start / FPS, end / FPS))
    return segments, times


# ============================================================
# 1초 Tag Feature 추출 (노트북 셀 10 기준)
# ============================================================
def _vec_angle_deg(v1, v2):
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 < 1e-12 or n2 < 1e-12:
        return 0.0
    return float(np.degrees(np.arccos(np.clip(np.dot(v1, v2) / (n1 * n2), -1, 1))))


def _angle_2d_deg(v):
    return float(np.degrees(np.arctan2(v[1], v[0])))


def _joint_angle(A, B, C):
    return _vec_angle_deg(A - B, C - B)


_DIRECTION_CLASSES = [
    "right", "up_right", "up", "up_left",
    "left", "down_left", "down", "down_right",
]


def _direction_class_from_angle(angle_deg):
    a = (angle_deg + 360.0) % 360.0
    idx = int(((a + 22.5) % 360) // 45)
    return _DIRECTION_CLASSES[idx]


def _mode_string(values):
    if not values:
        return "unknown"
    uniq, counts = np.unique(np.array(values, dtype=object), return_counts=True)
    return str(uniq[int(np.argmax(counts))])


def _movement_distance(points):
    if len(points) < 2:
        return 0.0
    return float(np.sum(np.linalg.norm(np.diff(points, axis=0), axis=1)))


def _avg_speed(points, times):
    if len(points) < 2:
        return 0.0
    dt = np.diff(times)
    dp = np.linalg.norm(np.diff(points, axis=0), axis=1)
    mask = dt > 1e-12
    if not np.any(mask):
        return 0.0
    return float(np.mean(dp[mask] / dt[mask]))


def _compute_window_features(coord: np.ndarray, start_frame: int, end_frame: int) -> dict:
    """1초 window의 tag feature dict 생성."""
    seg = coord[start_frame:end_frame]
    times = np.arange(seg.shape[0], dtype=np.float32) / FPS

    LSH, LEL, LWR = H36M17["left_shoulder"], H36M17["left_elbow"], H36M17["left_wrist"]
    RSH, REL, RWR = H36M17["right_shoulder"], H36M17["right_elbow"], H36M17["right_wrist"]
    LHP, LKN, LAN = H36M17["left_hip"], H36M17["left_knee"], H36M17["left_ankle"]
    RHP, RKN, RAN = H36M17["right_hip"], H36M17["right_knee"], H36M17["right_ankle"]
    PEL, THO = H36M17["pelvis"], H36M17["thorax"]

    left_elbow = [_joint_angle(p[LSH], p[LEL], p[LWR]) for p in seg]
    right_elbow = [_joint_angle(p[RSH], p[REL], p[RWR]) for p in seg]
    left_knee = [_joint_angle(p[LHP], p[LKN], p[LAN]) for p in seg]
    right_knee = [_joint_angle(p[RHP], p[RKN], p[RAN]) for p in seg]

    torso_vecs = seg[:, THO, :2] - seg[:, PEL, :2]
    body_tilt = [_vec_angle_deg(np.r_[v, 0.0], np.array([0.0, 1.0, 0.0])) for v in torso_vecs]

    hip_line = [_angle_2d_deg(p[LHP, :2] - p[RHP, :2]) for p in seg]
    shoulder_line = [_angle_2d_deg(p[LSH, :2] - p[RSH, :2]) for p in seg]
    torso_twist = [abs(h - sh) for h, sh in zip(hip_line, shoulder_line)]

    left_arm_dir = [_direction_class_from_angle(_angle_2d_deg(p[LWR, :2] - p[LSH, :2])) for p in seg]
    right_arm_dir = [_direction_class_from_angle(_angle_2d_deg(p[RWR, :2] - p[RSH, :2])) for p in seg]

    left_wrist, right_wrist = seg[:, LWR, :], seg[:, RWR, :]
    left_ankle, right_ankle = seg[:, LAN, :], seg[:, RAN, :]

    lw_speed = _avg_speed(left_wrist, times)
    rw_speed = _avg_speed(right_wrist, times)
    la_speed = _avg_speed(left_ankle, times)
    ra_speed = _avg_speed(right_ankle, times)

    arm_sync = 1.0 / (1.0 + abs(lw_speed - rw_speed))
    whole_coord = 1.0 / (1.0 + np.std([lw_speed, rw_speed, la_speed, ra_speed]))

    return {
        "left_elbow_angle_mean": float(np.mean(left_elbow)),
        "right_elbow_angle_mean": float(np.mean(right_elbow)),
        "left_knee_angle_mean": float(np.mean(left_knee)),
        "right_knee_angle_mean": float(np.mean(right_knee)),
        "body_tilt_angle_mean": float(np.mean(body_tilt)),
        "torso_twist_angle_mean": float(np.mean(torso_twist)),
        "left_arm_direction_class_mode": _mode_string(left_arm_dir),
        "right_arm_direction_class_mode": _mode_string(right_arm_dir),
        "left_wrist_movement_distance": _movement_distance(left_wrist),
        "right_wrist_movement_distance": _movement_distance(right_wrist),
        "whole_body_coordination_score": float(whole_coord),
        "arm_left_right_motion_synchronization": float(arm_sync),
        "arm_left_right_angle_difference_mean": float(
            np.mean(np.abs(np.array(left_elbow) - np.array(right_elbow)))
        ),
        "hip_line_angle_mean": float(np.mean(hip_line)),
        "shoulder_line_angle_mean": float(np.mean(shoulder_line)),
        "left_foot_avg_speed": float(la_speed),
        "right_foot_avg_speed": float(ra_speed),
    }


# ============================================================
# Tag 비교 유틸 (노트북 셀 10 기준)
# ============================================================
_FEATURE_TEXT = {
    "left_elbow_angle_mean": "왼팔 팔꿈치 평균 각도",
    "right_elbow_angle_mean": "오른팔 팔꿈치 평균 각도",
    "left_knee_angle_mean": "왼무릎 평균 각도",
    "right_knee_angle_mean": "오른무릎 평균 각도",
    "body_tilt_angle_mean": "몸통 기울기",
    "torso_twist_angle_mean": "상체 비틀림",
    "left_arm_direction_class_mode": "왼팔 방향",
    "right_arm_direction_class_mode": "오른팔 방향",
    "left_wrist_movement_distance": "왼손목 이동 거리",
    "right_wrist_movement_distance": "오른손목 이동 거리",
    "whole_body_coordination_score": "전신 협응",
    "arm_left_right_motion_synchronization": "양팔 동기화",
    "arm_left_right_angle_difference_mean": "양팔 대칭 패턴",
    "hip_line_angle_mean": "골반선 방향",
    "shoulder_line_angle_mean": "어깨선 방향",
    "left_foot_avg_speed": "왼발 평균 속도",
    "right_foot_avg_speed": "오른발 평균 속도",
}

_ANGLE_FEATURES = {
    "left_elbow_angle_mean", "right_elbow_angle_mean",
    "left_knee_angle_mean", "right_knee_angle_mean",
    "body_tilt_angle_mean", "torso_twist_angle_mean",
    "arm_left_right_angle_difference_mean",
    "hip_line_angle_mean", "shoulder_line_angle_mean",
}

_RATIO_FEATURES = {
    "left_wrist_movement_distance", "right_wrist_movement_distance",
    "whole_body_coordination_score", "arm_left_right_motion_synchronization",
    "left_foot_avg_speed", "right_foot_avg_speed",
}

_CLASS_FEATURES = {
    "left_arm_direction_class_mode", "right_arm_direction_class_mode",
}

_FEATURE_WEIGHT = {
    "body_tilt_angle_mean": 1.5, "torso_twist_angle_mean": 1.5,
    "hip_line_angle_mean": 1.3, "shoulder_line_angle_mean": 1.3,
    "left_elbow_angle_mean": 1.2, "right_elbow_angle_mean": 1.2,
    "left_knee_angle_mean": 1.2, "right_knee_angle_mean": 1.2,
    "whole_body_coordination_score": 1.5,
    "arm_left_right_motion_synchronization": 1.2,
    "arm_left_right_angle_difference_mean": 1.1,
    "left_wrist_movement_distance": 0.8, "right_wrist_movement_distance": 0.8,
    "left_foot_avg_speed": 0.8, "right_foot_avg_speed": 0.8,
    "left_arm_direction_class_mode": 0.6, "right_arm_direction_class_mode": 0.6,
}


def _compare_angle(a, b, strong=15.0, weak=30.0):
    diff = abs(float(a) - float(b))
    if diff <= strong:
        return "매우 유사", diff
    elif diff <= weak:
        return "유사", diff
    return "차이 있음", diff


def _compare_ratio(a, b, strong=0.20, weak=0.40, abs_tol=0.05):
    a, b = float(a), float(b)
    abs_diff = abs(a - b)
    if abs_diff <= abs_tol:
        return "매우 유사", abs_diff
    denom = max(abs(a), abs(b), 1.0)
    diff = abs_diff / denom
    if diff <= strong:
        return "매우 유사", diff
    elif diff <= weak:
        return "유사", diff
    return "차이 있음", diff


def _compare_class(a, b):
    a, b = str(a), str(b)
    if a == b:
        return "매우 유사", 0.0
    if a in _DIRECTION_CLASSES and b in _DIRECTION_CLASSES:
        ia, ib = _DIRECTION_CLASSES.index(a), _DIRECTION_CLASSES.index(b)
        dist = min((ia - ib) % 8, (ib - ia) % 8)
        if dist == 1:
            return "유사", 1.0
    return "차이 있음", 2.0


def _compare_window_features(feat_a: dict, feat_b: dict) -> tuple:
    """두 window feature dict를 비교 → (tags, details)."""
    tags, details = [], []
    for feat in _FEATURE_TEXT:
        if feat not in feat_a or feat not in feat_b:
            continue
        va, vb = feat_a[feat], feat_b[feat]
        try:
            if feat in _ANGLE_FEATURES:
                judge, diff = _compare_angle(va, vb)
            elif feat in _RATIO_FEATURES:
                judge, diff = _compare_ratio(va, vb)
            elif feat in _CLASS_FEATURES:
                judge, diff = _compare_class(va, vb)
            else:
                continue
        except Exception:
            continue
        if judge in ["매우 유사", "유사"]:
            tags.append(_FEATURE_TEXT[feat] + " 유사")
        details.append({
            "feature": feat, "text": _FEATURE_TEXT[feat],
            "a": va, "b": vb, "diff": diff, "judge": judge,
        })
    return tags, details


def _support_score(details: list) -> float:
    """가중치 기반 support score."""
    if not details:
        return 0.0
    total_weight, score = 0.0, 0.0
    for d in details:
        w = _FEATURE_WEIGHT.get(d["feature"], 1.0)
        total_weight += w
        if d["judge"] == "매우 유사":
            score += 1.0 * w
        elif d["judge"] == "유사":
            score += 0.7 * w
        else:
            score += 0.2 * w
    return score / total_weight if total_weight > 0 else 0.0


def _make_numeric_lines(details: list, top_k: int = 3) -> list:
    """수치 근거 문자열 생성."""
    sim_details = sorted(
        [d for d in details if d["judge"] in ["매우 유사", "유사"]],
        key=lambda x: x["diff"],
    )
    lines = []
    for d in sim_details[:top_k]:
        if isinstance(d["a"], str):
            lines.append(f"{d['text']} 유사 → ({d['a']} vs {d['b']})")
        else:
            unit = "°" if "angle" in d["feature"] else ""
            lines.append(
                f"{d['text']} 유사 → ({d['a']:.2f}{unit} vs {d['b']:.2f}{unit}, 차이: {d['diff']:.2f}{unit})"
            )
    return lines


# ============================================================
# 입력 검증
# ============================================================
def _validate(emb: np.ndarray, name: str) -> None:
    if not isinstance(emb, np.ndarray):
        raise ValueError(f"{name}는 numpy ndarray여야 합니다. 현재: {type(emb)}")
    if emb.ndim != 3 or emb.shape[1] != 17 or emb.shape[2] != 512:
        raise ValueError(f"{name} shape은 [F, 17, 512]여야 합니다. 현재: {emb.shape}")
    if emb.shape[0] == 0:
        raise ValueError(f"{name}의 프레임 수가 0입니다.")


def _empty_result() -> dict:
    return {
        "global_score": 0.0,
        "motion_segments": [],
    }


# ============================================================
# 메인 진입점
# ============================================================
def infer_similarity(
    emb_a: np.ndarray,
    emb_b: np.ndarray,
    keypoints_a: np.ndarray,
    keypoints_b: np.ndarray,
    fps_a: float = 30.0,
    fps_b: float = 30.0,
) -> dict:
    """
    최종 Pose+Tag 유사도 추론 + 구간별 상세 분석.

    Args:
        emb_a, emb_b: [F, 17, 512]  MotionBERT 임베딩
        keypoints_a, keypoints_b: [F, 17, 3]  HRNet 2D 키포인트
        fps_a, fps_b: 원본 영상 fps

    Returns:
        dict — generate_similarity_report(agent_data) 입력과 호환
              {
                "global_score": float,
                "motion_segments": [
                  {
                    "id", "time_a", "time_b",
                    "motion_sim", "motion_body_parts",
                    "pose_sim", "pose_detail", "body_parts"
                  }, ...
                ],
                "feature_result": {
                  "segment_features": [
                    {"segment_id", "tags", "details"}, ...
                  ]
                }
              }
    """
    _validate(emb_a, "emb_a")
    _validate(emb_b, "emb_b")

    emb_a_t = torch.from_numpy(emb_a).float().to(DEVICE)
    emb_b_t = torch.from_numpy(emb_b).float().to(DEVICE)
    kps_a_np = np.asarray(keypoints_a, dtype=np.float32)
    kps_b_np = np.asarray(keypoints_b, dtype=np.float32)

    # ============================================================
    # Global Score — ST-GCN pose embedding + tag → run_pose_tag_similarity
    # ============================================================
    model = load_pose_branch(POSE_TAG_CKPT_PATH)

    with torch.no_grad():
        pose_emb_a = model(emb_a_t).detach().cpu().numpy()
        pose_emb_b = model(emb_b_t).detach().cpu().numpy()

    tag_result = generate_pair_tags(
        keypoints_a, keypoints_b,
        fps_a=fps_a, fps_b=fps_b,
    )
    tag_vector = tag_result["tag_vector"]

    final_result = run_pose_tag_similarity(
        pose_emb_a, pose_emb_b, tag_vector,
        checkpoint_path=POSE_TAG_CKPT_PATH,
    )
    global_score = final_result["similarity_score"]

    # ============================================================
    # Step 1: Coarse Matching (5초, HRNet keypoints motion-aware)
    # ============================================================
    window_frames = MOTION_SEGMENT_SEC * FPS

    segs_a, times_a = _split_segments(kps_a_np, window_frames)
    segs_b, times_b = _split_segments(kps_b_np, window_frames)

    Na, Nb = len(segs_a), len(segs_b)
    if Na == 0 or Nb == 0:
        result = _empty_result()
        result["global_score"] = round(global_score, 4)
        return result

    sim_mat = np.zeros((Na, Nb), dtype=np.float32)
    part_mat = [[None for _ in range(Nb)] for _ in range(Na)]

    for i in range(Na):
        for j in range(Nb):
            sim, part_sims = _pose_motion_similarity(segs_a[i], segs_b[j])
            sim_mat[i, j] = sim
            part_mat[i][j] = part_sims

    # Top 25% + 임계값 필터 + greedy 1:1 매칭
    all_cells = [(i, j, float(sim_mat[i, j])) for i in range(Na) for j in range(Nb)]
    all_cells.sort(key=lambda x: x[2], reverse=True)
    n_top = max(1, int(len(all_cells) * TOP_PERCENT))
    top_cells = [(i, j, s) for i, j, s in all_cells[:n_top] if s >= MIN_SIM_THRESHOLD]

    used_a, used_b = set(), set()
    coarse_matches = []
    for i, j, s in top_cells:
        if i not in used_a and j not in used_b:
            coarse_matches.append({
                "idx_a": i,
                "idx_b": j,
                "time_a_sec": times_a[i],
                "time_b_sec": times_b[j],
                "coarse_sim": round(float(s), 4),
                "coarse_body_parts": {
                    n: round(float(part_mat[i][j][n]), 4) for n in PART_NAMES
                },
            })
            used_a.add(i)
            used_b.add(j)

    coarse_matches.sort(key=lambda x: x["coarse_sim"], reverse=True)

    # ============================================================
    # Step 1.5: Coarse-to-Fine Refine (±2초)
    # ============================================================
    refine_window = REFINE_WINDOW_SEC * FPS
    refine_stride = REFINE_STRIDE_SEC * FPS
    refine_margin = REFINE_MARGIN_SEC * FPS

    refined_matches = []
    for m in coarse_matches:
        coarse_a_frame = int(m["time_a_sec"][0] * FPS)
        coarse_b_frame = int(m["time_b_sec"][0] * FPS)

        sa_start = max(0, coarse_a_frame - refine_margin)
        sa_end = min(kps_a_np.shape[0] - refine_window, coarse_a_frame + refine_margin)
        sb_start = max(0, coarse_b_frame - refine_margin)
        sb_end = min(kps_b_np.shape[0] - refine_window, coarse_b_frame + refine_margin)

        best_sim = -1.0
        best_a, best_b = coarse_a_frame, coarse_b_frame
        best_parts = m["coarse_body_parts"]

        if sa_end < sa_start or sb_end < sb_start:
            best_sim = m["coarse_sim"]
        else:
            for sa in range(sa_start, sa_end + 1, refine_stride):
                for sb in range(sb_start, sb_end + 1, refine_stride):
                    seg_a = kps_a_np[sa : sa + refine_window]
                    seg_b = kps_b_np[sb : sb + refine_window]
                    if seg_a.shape[0] < refine_window // 2 or seg_b.shape[0] < refine_window // 2:
                        continue
                    sim, parts = _pose_motion_similarity(seg_a, seg_b)
                    if sim > best_sim:
                        best_sim = sim
                        best_a, best_b = sa, sb
                        best_parts = {n: round(float(parts[n]), 4) for n in PART_NAMES}

        ref_a = (best_a / FPS, (best_a + refine_window) / FPS)
        ref_b = (best_b / FPS, (best_b + refine_window) / FPS)

        refined_matches.append({
            "idx_a": m["idx_a"],
            "idx_b": m["idx_b"],
            "time_a_sec": ref_a,
            "time_b_sec": ref_b,
            "motion_sim": round(float(best_sim), 4),
            "coarse_sim": m["coarse_sim"],
            "motion_body_parts": best_parts,
        })

    # ============================================================
    # Step 2: Pose 정밀 비교 (1초) + Tag Evidence
    # ============================================================
    for m in refined_matches:
        a0, a1 = m["time_a_sec"]
        b0, b1 = m["time_b_sec"]
        duration = min(a1 - a0, b1 - b0)
        n_steps = max(1, int(duration // POSE_SEGMENT_SEC))

        m["pose_detail"] = []
        pose_sims_in_segment = []

        for k in range(n_steps):
            sa0 = a0 + k * POSE_SEGMENT_SEC
            sa1 = min(a0 + (k + 1) * POSE_SEGMENT_SEC, a1)
            sb0 = b0 + k * POSE_SEGMENT_SEC
            sb1 = min(b0 + (k + 1) * POSE_SEGMENT_SEC, b1)

            fa0, fa1 = int(sa0 * FPS), int(sa1 * FPS)
            fb0, fb1 = int(sb0 * FPS), int(sb1 * FPS)

            seg_a_1 = kps_a_np[fa0:fa1]
            seg_b_1 = kps_b_np[fb0:fb1]

            if seg_a_1.shape[0] < 2 or seg_b_1.shape[0] < 2:
                continue

            # 1초 pose similarity
            pose_sim, pose_parts = _pose_motion_similarity(seg_a_1, seg_b_1)

            # 1초 tag evidence
            feat_a = _compute_window_features(kps_a_np, fa0, fa1)
            feat_b = _compute_window_features(kps_b_np, fb0, fb1)
            tags, details = _compare_window_features(feat_a, feat_b)
            tag_score = _support_score(details)
            evidence_lines = _make_numeric_lines(details)

            pose_sims_in_segment.append(pose_sim)

            m["pose_detail"].append({
                "t": f"{sa0:.0f}~{sa1:.0f}s ↔ {sb0:.0f}~{sb1:.0f}s",
                "sim": round(pose_sim, 4),
                "body_parts": {n: round(float(pose_parts[n]), 4) for n in PART_NAMES},
                "tag_support": round(tag_score, 4),
                "tags": tags[:5],
                "numeric_evidence": evidence_lines,
            })

        # 5초 구간의 대표 pose_sim / body_parts
        if pose_sims_in_segment:
            m["pose_sim"] = round(float(np.mean(pose_sims_in_segment)), 4)
            avg_body = {}
            for n in PART_NAMES:
                vals = [pd["body_parts"][n] for pd in m["pose_detail"]]
                avg_body[n] = round(float(np.mean(vals)), 4)
            m["body_parts"] = avg_body
        else:
            m["pose_sim"] = 0.0
            m["body_parts"] = {n: 0.0 for n in PART_NAMES}

    # ============================================================
    # Step 3: 결과 dict 조립 — LLM agent 입력 스키마
    # ============================================================
    motion_segments = []
    segment_features = []

    for idx, m in enumerate(refined_matches):
        seg_id = idx + 1
        time_a = f"{m['time_a_sec'][0]:.0f}~{m['time_a_sec'][1]:.0f}s"
        time_b = f"{m['time_b_sec'][0]:.0f}~{m['time_b_sec'][1]:.0f}s"

        motion_segments.append({
            "id": seg_id,
            "time_a": time_a,
            "time_b": time_b,
            "motion_sim": m["motion_sim"],
            "coarse_sim": m["coarse_sim"],
            "motion_body_parts": m["motion_body_parts"],
            "pose_sim": m["pose_sim"],
            "pose_detail": m["pose_detail"],
            "body_parts": m["body_parts"],
        })

        # segment별 tag 집계 (중복 제거, 상위 8개)
        all_tags = []
        all_evidence = []
        for pd in m.get("pose_detail", []):
            all_tags.extend(pd.get("tags", []))
            all_evidence.extend(pd.get("numeric_evidence", []))

        segment_features.append({
            "segment_id": seg_id,
            "tags": list(dict.fromkeys(all_tags))[:8],
            "details": all_evidence[:5],
        })

    return {
        "global_score": round(global_score, 4),
        "motion_segments": motion_segments,
        "feature_result": {
            "segment_features": segment_features,
        },
    }