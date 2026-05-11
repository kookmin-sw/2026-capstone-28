import numpy as np

from model_pipeline.feature_extractor import extract_pose_features


FEATURE_TEXT = {
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

    "left_leg_extension_ratio_mean": "왼다리 펴짐 정도",
    "right_leg_extension_ratio_mean": "오른다리 펴짐 정도",
    "left_knee_angle_near_90_ratio": "왼무릎 90도 접힘 비율",
    "right_knee_angle_near_90_ratio": "오른무릎 90도 접힘 비율",
    "left_knee_angle_stability": "왼무릎 자세 안정성",
    "right_knee_angle_stability": "오른무릎 자세 안정성",
    "left_knee_angle_abs_change_sum": "왼무릎 각도 변화량",
    "right_knee_angle_abs_change_sum": "오른무릎 각도 변화량",
    "left_knee_angle_delta": "왼무릎 각도 시작-끝 변화",
    "right_knee_angle_delta": "오른무릎 각도 시작-끝 변화",

    "left_ankle_height_relative_to_hip_mean": "왼발목 골반 대비 높이",
    "right_ankle_height_relative_to_hip_mean": "오른발목 골반 대비 높이",
    "left_ankle_height_relative_to_hip_range": "왼발목 높이 변화폭",
    "right_ankle_height_relative_to_hip_range": "오른발목 높이 변화폭",
    "left_knee_height_relative_to_hip_mean": "왼무릎 골반 대비 높이",
    "right_knee_height_relative_to_hip_mean": "오른무릎 골반 대비 높이",
    "left_knee_height_relative_to_hip_range": "왼무릎 높이 변화폭",
    "right_knee_height_relative_to_hip_range": "오른무릎 높이 변화폭",
    "left_foot_height_relative_to_ground_mean": "왼발 바닥 대비 높이",
    "right_foot_height_relative_to_ground_mean": "오른발 바닥 대비 높이",
    "left_foot_height_relative_to_ground_range": "왼발 높이 변화폭",
    "right_foot_height_relative_to_ground_range": "오른발 높이 변화폭",
    "left_foot_contact_ratio": "왼발 바닥 접촉 비율",
    "right_foot_contact_ratio": "오른발 바닥 접촉 비율",

    "left_ankle_movement_distance": "왼발목 이동 거리",
    "right_ankle_movement_distance": "오른발목 이동 거리",
    "left_ankle_avg_speed": "왼발목 평균 속도",
    "right_ankle_avg_speed": "오른발목 평균 속도",
    "left_ankle_lateral_displacement": "왼발목 좌우 이동량",
    "right_ankle_lateral_displacement": "오른발목 좌우 이동량",
    "left_knee_lateral_displacement": "왼무릎 좌우 이동량",
    "right_knee_lateral_displacement": "오른무릎 좌우 이동량",
    "left_ankle_path_direction": "왼발목 이동 방향",
    "right_ankle_path_direction": "오른발목 이동 방향",
    "left_leg_direction_class_mode": "왼다리 방향",
    "right_leg_direction_class_mode": "오른다리 방향",
    "step_width_mean": "양발 간 거리",
    "step_width_range": "양발 간 거리 변화폭",
    "stride_movement_distance": "스텝 이동 거리",
    "stride_direction_class": "스텝 진행 방향",

    "leg_left_right_angle_difference_mean": "좌우 다리 각도 차이",
    "leg_left_right_motion_synchronization": "좌우 다리 움직임 동기화",
    "leg_left_right_height_difference_mean": "좌우 다리 높이 차이",
    "leg_left_right_direction_difference_mean": "좌우 다리 방향 차이",
    "leg_bilateral_symmetry_score": "좌우 다리 대칭 정도",
}

ANGLE = {
    "left_elbow_angle_mean", "right_elbow_angle_mean",
    "left_knee_angle_mean", "right_knee_angle_mean",
    "body_tilt_angle_mean", "torso_twist_angle_mean",
    "arm_left_right_angle_difference_mean",
    "hip_line_angle_mean", "shoulder_line_angle_mean",
    "left_knee_angle_delta", "right_knee_angle_delta",
    "left_ankle_path_direction", "right_ankle_path_direction",
    "leg_left_right_angle_difference_mean",
    "leg_left_right_direction_difference_mean",
}

CLASS = {
    "left_arm_direction_class_mode",
    "right_arm_direction_class_mode",
    "left_leg_direction_class_mode",
    "right_leg_direction_class_mode",
    "stride_direction_class",
}

FEATURE_WEIGHT = {
    "body_tilt_angle_mean": 1.5,
    "torso_twist_angle_mean": 1.5,
    "left_knee_angle_mean": 1.3,
    "right_knee_angle_mean": 1.3,
    "left_ankle_movement_distance": 1.2,
    "right_ankle_movement_distance": 1.2,
    "step_width_mean": 1.3,
    "leg_bilateral_symmetry_score": 1.2,
    "left_knee_angle_direction_context": 1.4,
    "right_knee_angle_direction_context": 1.4,
}


def safe_float(x, default=0.0):
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def compare_angle_feature(a, b, strong=15.0, weak=30.0):
    diff = abs(safe_float(a) - safe_float(b))
    if diff <= strong:
        return "매우 유사", diff
    elif diff <= weak:
        return "유사", diff
    return "차이 있음", diff


def compare_ratio_feature(a, b, strong=0.20, weak=0.40, abs_tol=0.05):
    a, b = safe_float(a), safe_float(b)
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


DIRS = ["right", "up_right", "up", "up_left", "left", "down_left", "down", "down_right"]


def compare_class_feature(a, b):
    a, b = str(a), str(b)

    if a == b:
        return "매우 유사", 0.0

    if a in DIRS and b in DIRS:
        ia, ib = DIRS.index(a), DIRS.index(b)
        dist = min((ia - ib) % 8, (ib - ia) % 8)
        if dist == 1:
            return "유사", 1.0

    return "차이 있음", 2.0


def angle_2d_deg(vec):
    v = np.array(vec, dtype=float)
    if len(v) < 2:
        return 0.0
    return float(np.degrees(np.arctan2(v[1], v[0])))


def direction_class_from_angle(angle):
    a = (float(angle) + 360.0) % 360.0
    idx = int(((a + 22.5) % 360) // 45)
    return DIRS[idx]


def direction_from_vector(vec):
    return direction_class_from_angle(angle_2d_deg(vec))


def direction_distance(a, b):
    if a not in DIRS or b not in DIRS:
        return 8
    ia, ib = DIRS.index(a), DIRS.index(b)
    return min((ia - ib) % 8, (ib - ia) % 8)


def compare_direction_change(start_a, end_a, start_b, end_b):
    a0 = direction_from_vector(start_a)
    a1 = direction_from_vector(end_a)
    b0 = direction_from_vector(start_b)
    b1 = direction_from_vector(end_b)

    diff = direction_distance(a0, b0) + direction_distance(a1, b1)

    if diff == 0:
        judge = "매우 유사"
    elif diff <= 2:
        judge = "유사"
    else:
        judge = "차이 있음"

    return judge, float(diff), f"{a0}->{a1}", f"{b0}->{b1}"


def knee_angle_state(angle):
    angle = safe_float(angle)
    if angle < 100:
        return "깊게 접힘"
    elif angle < 140:
        return "접힘"
    elif angle < 165:
        return "약간 접힘"
    return "펴짐"


def compare_window(a, b):
    tags = []
    details = []

    for feat, text in FEATURE_TEXT.items():
        if feat not in a or feat not in b:
            continue

        va, vb = a[feat], b[feat]

        if feat in ANGLE:
            judge, diff = compare_angle_feature(va, vb)
        elif feat in CLASS:
            judge, diff = compare_class_feature(va, vb)
        else:
            judge, diff = compare_ratio_feature(va, vb)

        if judge in ["매우 유사", "유사"]:
            tags.append(text + " 유사")

        details.append({
            "feature": feat,
            "text": text,
            "a": va,
            "b": vb,
            "diff": diff,
            "judge": judge,
        })

    for side, kor in [("left", "왼"), ("right", "오른")]:
        angle_key = f"{side}_knee_angle_mean"
        start_key = f"{side}_hip_to_knee_vector_start"
        end_key = f"{side}_hip_to_knee_vector_end"

        if angle_key not in a or angle_key not in b:
            continue
        if start_key not in a or start_key not in b or end_key not in a or end_key not in b:
            continue

        angle_a = safe_float(a[angle_key])
        angle_b = safe_float(b[angle_key])

        angle_judge, angle_diff = compare_angle_feature(angle_a, angle_b, strong=18.0, weak=35.0)

        dir_judge, dir_diff, change_a, change_b = compare_direction_change(
            a[start_key], a[end_key],
            b[start_key], b[end_key],
        )

        state_a = knee_angle_state(angle_a)
        state_b = knee_angle_state(angle_b)
        state_same = state_a == state_b

        if state_same and dir_judge in ["매우 유사", "유사"]:
            judge = "매우 유사" if angle_judge == "매우 유사" and dir_judge == "매우 유사" else "유사"
            tag_name = f"{kor}무릎 굽힘 상태와 방향 변화 유사"
            tags.append(tag_name)
            diff = angle_diff + dir_diff
        else:
            judge = "차이 있음"
            diff = angle_diff + dir_diff + (0 if state_same else 3)

        details.append({
            "feature": f"{side}_knee_angle_direction_context",
            "text": f"{kor}무릎 굽힘 상태와 방향 변화",
            "a": f"{angle_a:.1f}°/{state_a}/{change_a}",
            "b": f"{angle_b:.1f}°/{state_b}/{change_b}",
            "diff": diff,
            "judge": judge,
        })

    return list(dict.fromkeys(tags)), details


def support_score(details):
    if not details:
        return 0.0

    total_weight = 0.0
    score = 0.0

    for d in details:
        feat = d["feature"]
        w = FEATURE_WEIGHT.get(feat, 1.0)
        total_weight += w

        if d["judge"] == "매우 유사":
            score += 1.0 * w
        elif d["judge"] == "유사":
            score += 0.7 * w
        else:
            score += 0.2 * w

    return score / total_weight if total_weight > 0 else 0.0


def make_numeric_lines(details, top_k=3):
    sim = [d for d in details if d["judge"] in ["매우 유사", "유사"]]
    sim = sorted(sim, key=lambda x: safe_float(x.get("diff", 999.0), 999.0))

    lines = []
    for d in sim[:top_k]:
        if isinstance(d["a"], str):
            lines.append(f"{d['text']} 유사 → ({d['a']} vs {d['b']})")
        else:
            unit = "°" if ("angle" in d["feature"] or "direction" in d["feature"]) else ""
            lines.append(
                f"{d['text']} 유사 → "
                f"({safe_float(d['a']):.2f}{unit} vs {safe_float(d['b']):.2f}{unit}, "
                f"차이: {safe_float(d['diff']):.2f}{unit})"
            )

    return lines


def generate_pair_tags(keypoints_a, keypoints_b, fps_a=30.0, fps_b=30.0, search_radius=1):
    features_a = extract_pose_features(keypoints_a, fps=fps_a)
    features_b = extract_pose_features(keypoints_b, fps=fps_b)

    wa = features_a["per_window_features"]
    wb = features_b["per_window_features"]

    window_results = []

    for i, window_a in enumerate(wa):
        best = None

        start_j = max(0, i - search_radius)
        end_j = min(len(wb), i + search_radius + 1)

        for j in range(start_j, end_j):
            tags, details = compare_window(window_a, wb[j])
            score = support_score(details)

            candidate = {
                "matched_b_index": j,
                "support_score": score,
                "tags": tags,
                "details": details,
            }

            if best is None or candidate["support_score"] > best["support_score"]:
                best = candidate

        if best is None:
            best = {
                "matched_b_index": i,
                "support_score": 0.0,
                "tags": [],
                "details": [],
            }

        window_results.append({
            "window": i,
            "matched_window_in_b": best["matched_b_index"],
            "start": window_a["start_sec"],
            "end": window_a["end_sec"],
            "support_score": best["support_score"],
            "tags": best["tags"][:8],
            "numeric_evidence": make_numeric_lines(best["details"], top_k=3),
            "details": best["details"],
        })

    if window_results:
        avg_support = float(np.mean([r["support_score"] for r in window_results]))
    else:
        avg_support = 0.0

    all_tags = []
    for r in window_results:
        all_tags.extend(r["tags"])

    tag_names = list(dict.fromkeys(all_tags))
    tag_vector = np.array([1.0 for _ in tag_names], dtype=np.float32)

    return {
        "support_score": avg_support,
        "tag_names": tag_names,
        "tag_vector": tag_vector,
        "window_results": window_results,
    }