import numpy as np

WINDOW_SEC = 1.0
MIN_FRAME = 2
DEFAULT_FPS = 30.0

COCO17 = {
    "nose": 0,
    "left_eye": 1,
    "right_eye": 2,
    "left_ear": 3,
    "right_ear": 4,
    "left_shoulder": 5,
    "right_shoulder": 6,
    "left_elbow": 7,
    "right_elbow": 8,
    "left_wrist": 9,
    "right_wrist": 10,
    "left_hip": 11,
    "right_hip": 12,
    "left_knee": 13,
    "right_knee": 14,
    "left_ankle": 15,
    "right_ankle": 16,
}


def _safe_norm(v):
    return np.linalg.norm(v) + 1e-6


def _angle(a, b, c):
    ba = a - b
    bc = c - b
    cos = np.dot(ba, bc) / (_safe_norm(ba) * _safe_norm(bc))
    cos = np.clip(cos, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos)))


def _direction_angle(v):
    return float(np.degrees(np.arctan2(v[1], v[0])))


def _direction_class(angle_deg):
    dirs = ["right", "up_right", "up", "up_left", "left", "down_left", "down", "down_right"]
    a = (angle_deg + 360.0) % 360.0
    idx = int(((a + 22.5) % 360) // 45)
    return dirs[idx]


def _movement_distance(points):
    if len(points) < 2:
        return 0.0
    return float(np.sum(np.linalg.norm(np.diff(points, axis=0), axis=1)))


def _avg_speed(points, times):
    if len(points) < 2:
        return 0.0
    dist = np.linalg.norm(np.diff(points, axis=0), axis=1)
    dt = np.diff(times)
    mask = dt > 1e-6
    if not np.any(mask):
        return 0.0
    return float(np.mean(dist[mask] / dt[mask]))


def _stats(arr):
    arr = np.asarray(arr, dtype=float)
    if len(arr) == 0:
        return 0.0, 0.0, 0.0, 0.0
    return float(np.mean(arr)), float(np.max(arr)), float(np.min(arr)), float(np.max(arr) - np.min(arr))


def _segment_indices(n_frames, fps, window_sec=WINDOW_SEC, min_frame=MIN_FRAME):
    frames_per_window = max(int(fps * window_sec), min_frame)
    segments = []

    for start in range(0, n_frames, frames_per_window):
        end = min(start + frames_per_window, n_frames)
        if end - start >= min_frame:
            segments.append((start, end))

    if not segments and n_frames > 0:
        segments.append((0, n_frames))

    return segments


def _get_xy(keypoints):
    keypoints = np.asarray(keypoints, dtype=np.float32)

    if keypoints.ndim != 3:
        raise ValueError(f"keypoints는 [F,17,3] 형태여야 합니다. 현재 shape={keypoints.shape}")

    if keypoints.shape[1] != 17:
        raise ValueError(f"관절 개수는 17개여야 합니다. 현재 shape={keypoints.shape}")

    return keypoints[:, :, :2]


def _extract_window_features(kp, times, i0, i1):
    seg = kp[i0:i1]
    t = times[i0:i1]

    ls = COCO17["left_shoulder"]
    rs = COCO17["right_shoulder"]
    le = COCO17["left_elbow"]
    re = COCO17["right_elbow"]
    lw = COCO17["left_wrist"]
    rw = COCO17["right_wrist"]
    lh = COCO17["left_hip"]
    rh = COCO17["right_hip"]
    lk = COCO17["left_knee"]
    rk = COCO17["right_knee"]
    la = COCO17["left_ankle"]
    ra = COCO17["right_ankle"]

    left_elbow_angles = np.array([_angle(f[ls], f[le], f[lw]) for f in seg])
    right_elbow_angles = np.array([_angle(f[rs], f[re], f[rw]) for f in seg])
    left_knee_angles = np.array([_angle(f[lh], f[lk], f[la]) for f in seg])
    right_knee_angles = np.array([_angle(f[rh], f[rk], f[ra]) for f in seg])

    lka_mean, _, _, _ = _stats(left_knee_angles)
    rka_mean, _, _, _ = _stats(right_knee_angles)
    lea_mean, _, _, _ = _stats(left_elbow_angles)
    rea_mean, _, _, _ = _stats(right_elbow_angles)

    shoulder_center = (seg[:, ls] + seg[:, rs]) / 2
    hip_center = (seg[:, lh] + seg[:, rh]) / 2
    torso_vec = shoulder_center - hip_center

    body_tilt = np.array([_direction_angle(v) for v in torso_vec])
    body_tilt_mean, _, _, _ = _stats(body_tilt)

    shoulder_vec = seg[:, rs] - seg[:, ls]
    hip_vec = seg[:, rh] - seg[:, lh]

    shoulder_line = np.array([_direction_angle(v) for v in shoulder_vec])
    hip_line = np.array([_direction_angle(v) for v in hip_vec])

    shoulder_line_mean, _, _, _ = _stats(shoulder_line)
    hip_line_mean, _, _, _ = _stats(hip_line)

    torso_twist = np.abs(shoulder_line - hip_line)
    torso_twist = np.minimum(torso_twist, 360 - torso_twist)
    torso_twist_mean, _, _, _ = _stats(torso_twist)

    left_arm_vec = seg[:, lw] - seg[:, ls]
    right_arm_vec = seg[:, rw] - seg[:, rs]
    left_leg_vec = seg[:, la] - seg[:, lh]
    right_leg_vec = seg[:, ra] - seg[:, rh]

    left_arm_dirs = [_direction_class(_direction_angle(v)) for v in left_arm_vec]
    right_arm_dirs = [_direction_class(_direction_angle(v)) for v in right_arm_vec]
    left_leg_dirs = [_direction_class(_direction_angle(v)) for v in left_leg_vec]
    right_leg_dirs = [_direction_class(_direction_angle(v)) for v in right_leg_vec]

    def mode(values):
        if not values:
            return "unknown"
        uniq, cnt = np.unique(values, return_counts=True)
        return str(uniq[np.argmax(cnt)])

    left_wrist = seg[:, lw]
    right_wrist = seg[:, rw]
    left_ankle = seg[:, la]
    right_ankle = seg[:, ra]
    left_knee = seg[:, lk]
    right_knee = seg[:, rk]

    left_leg_extension = np.clip(left_knee_angles / 180.0, 0, 1)
    right_leg_extension = np.clip(right_knee_angles / 180.0, 0, 1)

    step_width = np.abs(left_ankle[:, 0] - right_ankle[:, 0])
    step_width_mean, _, _, step_width_range = _stats(step_width)

    left_foot_height_ground = np.max(np.stack([left_ankle[:, 1], right_ankle[:, 1]], axis=1), axis=1) - left_ankle[:, 1]
    right_foot_height_ground = np.max(np.stack([left_ankle[:, 1], right_ankle[:, 1]], axis=1), axis=1) - right_ankle[:, 1]

    lf_mean, _, _, lf_range = _stats(left_foot_height_ground)
    rf_mean, _, _, rf_range = _stats(right_foot_height_ground)

    left_ankle_height = left_ankle[:, 1] - seg[:, lh, 1]
    right_ankle_height = right_ankle[:, 1] - seg[:, rh, 1]
    left_knee_height = left_knee[:, 1] - seg[:, lh, 1]
    right_knee_height = right_knee[:, 1] - seg[:, rh, 1]

    lah_mean, _, _, lah_range = _stats(left_ankle_height)
    rah_mean, _, _, rah_range = _stats(right_ankle_height)
    lkh_mean, _, _, lkh_range = _stats(left_knee_height)
    rkh_mean, _, _, rkh_range = _stats(right_knee_height)

    left_ankle_path_direction = _direction_angle(left_ankle[-1] - left_ankle[0]) if len(left_ankle) >= 2 else 0.0
    right_ankle_path_direction = _direction_angle(right_ankle[-1] - right_ankle[0]) if len(right_ankle) >= 2 else 0.0

    foot_mid = (left_ankle + right_ankle) / 2
    stride_direction = _direction_angle(foot_mid[-1] - foot_mid[0]) if len(foot_mid) >= 2 else 0.0
    stride_direction_class = _direction_class(stride_direction)

    left_speed = _avg_speed(left_ankle, t)
    right_speed = _avg_speed(right_ankle, t)

    return {
        "start_sec": float(times[i0]),
        "end_sec": float(times[i1 - 1]),

        "left_elbow_angle_mean": lea_mean,
        "right_elbow_angle_mean": rea_mean,
        "left_knee_angle_mean": lka_mean,
        "right_knee_angle_mean": rka_mean,
        "body_tilt_angle_mean": body_tilt_mean,
        "torso_twist_angle_mean": torso_twist_mean,
        "hip_line_angle_mean": hip_line_mean,
        "shoulder_line_angle_mean": shoulder_line_mean,

        "left_arm_direction_class_mode": mode(left_arm_dirs),
        "right_arm_direction_class_mode": mode(right_arm_dirs),
        "left_leg_direction_class_mode": mode(left_leg_dirs),
        "right_leg_direction_class_mode": mode(right_leg_dirs),

        "left_wrist_movement_distance": _movement_distance(left_wrist),
        "right_wrist_movement_distance": _movement_distance(right_wrist),

        "left_foot_avg_speed": left_speed,
        "right_foot_avg_speed": right_speed,
        "left_ankle_avg_speed": left_speed,
        "right_ankle_avg_speed": right_speed,

        "left_leg_extension_ratio_mean": float(np.mean(left_leg_extension)),
        "right_leg_extension_ratio_mean": float(np.mean(right_leg_extension)),
        "left_knee_angle_near_90_ratio": float(np.mean(np.abs(left_knee_angles - 90) <= 15)),
        "right_knee_angle_near_90_ratio": float(np.mean(np.abs(right_knee_angles - 90) <= 15)),
        "left_knee_angle_stability": float(1 / (1 + np.std(left_knee_angles) / 30)),
        "right_knee_angle_stability": float(1 / (1 + np.std(right_knee_angles) / 30)),
        "left_knee_angle_abs_change_sum": float(np.sum(np.abs(np.diff(left_knee_angles)))) if len(left_knee_angles) >= 2 else 0.0,
        "right_knee_angle_abs_change_sum": float(np.sum(np.abs(np.diff(right_knee_angles)))) if len(right_knee_angles) >= 2 else 0.0,
        "left_knee_angle_delta": float(left_knee_angles[-1] - left_knee_angles[0]) if len(left_knee_angles) >= 2 else 0.0,
        "right_knee_angle_delta": float(right_knee_angles[-1] - right_knee_angles[0]) if len(right_knee_angles) >= 2 else 0.0,

        "left_ankle_height_relative_to_hip_mean": lah_mean,
        "right_ankle_height_relative_to_hip_mean": rah_mean,
        "left_ankle_height_relative_to_hip_range": lah_range,
        "right_ankle_height_relative_to_hip_range": rah_range,
        "left_knee_height_relative_to_hip_mean": lkh_mean,
        "right_knee_height_relative_to_hip_mean": rkh_mean,
        "left_knee_height_relative_to_hip_range": lkh_range,
        "right_knee_height_relative_to_hip_range": rkh_range,

        "left_foot_height_relative_to_ground_mean": lf_mean,
        "right_foot_height_relative_to_ground_mean": rf_mean,
        "left_foot_height_relative_to_ground_range": lf_range,
        "right_foot_height_relative_to_ground_range": rf_range,
        "left_foot_contact_ratio": float(np.mean(left_foot_height_ground <= np.percentile(left_foot_height_ground, 25))),
        "right_foot_contact_ratio": float(np.mean(right_foot_height_ground <= np.percentile(right_foot_height_ground, 25))),

        "left_ankle_movement_distance": _movement_distance(left_ankle),
        "right_ankle_movement_distance": _movement_distance(right_ankle),
        "left_ankle_lateral_displacement": float(np.sum(np.abs(np.diff(left_ankle[:, 0])))) if len(left_ankle) >= 2 else 0.0,
        "right_ankle_lateral_displacement": float(np.sum(np.abs(np.diff(right_ankle[:, 0])))) if len(right_ankle) >= 2 else 0.0,
        "left_knee_lateral_displacement": float(np.sum(np.abs(np.diff(left_knee[:, 0])))) if len(left_knee) >= 2 else 0.0,
        "right_knee_lateral_displacement": float(np.sum(np.abs(np.diff(right_knee[:, 0])))) if len(right_knee) >= 2 else 0.0,

        "left_ankle_path_direction": left_ankle_path_direction,
        "right_ankle_path_direction": right_ankle_path_direction,
        "step_width_mean": step_width_mean,
        "step_width_range": step_width_range,
        "stride_movement_distance": _movement_distance(foot_mid),
        "stride_direction": stride_direction,
        "stride_direction_class": stride_direction_class,

        "left_hip_to_knee_vector_start": (seg[0, lk] - seg[0, lh]).tolist(),
        "left_hip_to_knee_vector_end": (seg[-1, lk] - seg[-1, lh]).tolist(),
        "right_hip_to_knee_vector_start": (seg[0, rk] - seg[0, rh]).tolist(),
        "right_hip_to_knee_vector_end": (seg[-1, rk] - seg[-1, rh]).tolist(),

        "whole_body_coordination_score": 0.5,
        "arm_left_right_motion_synchronization": 0.5,
        "arm_left_right_angle_difference_mean": float(np.mean(np.abs(left_elbow_angles - right_elbow_angles))),
        "leg_left_right_angle_difference_mean": float(np.mean(np.abs(left_knee_angles - right_knee_angles))),
        "leg_left_right_motion_synchronization": 0.5,
        "leg_left_right_height_difference_mean": float(np.mean(np.abs(left_ankle_height - right_ankle_height))),
        "leg_left_right_direction_difference_mean": 0.0,
        "leg_bilateral_symmetry_score": 0.5,
    }


def extract_pose_features(keypoints, fps=DEFAULT_FPS, window_sec=WINDOW_SEC, min_frame=MIN_FRAME):
    kp = _get_xy(keypoints)
    n_frames = len(kp)
    times = np.arange(n_frames, dtype=np.float32) / float(fps)

    windows = []
    for i0, i1 in _segment_indices(n_frames, fps, window_sec, min_frame):
        windows.append(_extract_window_features(kp, times, i0, i1))

    return {
        "fps": float(fps),
        "num_frames": int(n_frames),
        "window_sec": float(window_sec),
        "per_window_features": windows,
    }