"""
models/hrnet/hrnet_loader.py
HRNet-W48 모델 로딩 + 포즈 추출 유틸리티

사전 준비:
  1. backend/ 안에 HRNet 레포 클론
     git clone https://github.com/HRNet/HRNet-Human-Pose-Estimation.git
  2. 가중치 파일 배치
     models/hrnet/weights/pose_hrnet_w48_384x288.pth
  3. pip install EasyDict yacs
"""

import os
import sys
import cv2
import numpy as np
import torch

# ============================================================
# HRNet 레포 경로 설정
# ============================================================
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_HRNET_LIB = os.path.join(_BACKEND_DIR, "HRNet-Human-Pose-Estimation", "lib")
if _HRNET_LIB not in sys.path:
    sys.path.insert(0, _HRNET_LIB)

# ============================================================
# 상수
# ============================================================
INPUT_SIZE = (384, 288)       # H, W
HEATMAP_SIZE = (96, 72)       # H, W

FLIP_PAIRS = [[1, 2], [3, 4], [5, 6], [7, 8],
              [9, 10], [11, 12], [13, 14], [15, 16]]

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

# COCO 17관절 인덱스
COCO = {
    "nose": 0, "l_eye": 1, "r_eye": 2, "l_ear": 3, "r_ear": 4,
    "l_shoulder": 5, "r_shoulder": 6, "l_elbow": 7, "r_elbow": 8,
    "l_wrist": 9, "r_wrist": 10, "l_hip": 11, "r_hip": 12,
    "l_knee": 13, "r_knee": 14, "l_ankle": 15, "r_ankle": 16,
}

# 가중치 기본 경로
_WEIGHT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weights")
_DEFAULT_WEIGHT = os.path.join(_WEIGHT_DIR, "pose_hrnet_w48_384x288.pth")

# 모델 캐시
_cache = {"model": None, "device": None}


# ============================================================
# 1. 모델 로딩
# ============================================================
def load_hrnet(weight_path=None):
    """
    HRNet-W48 모델 로드 + 캐싱.
    두 번째 호출부터 캐시된 모델 즉시 반환.

    Args:
        weight_path: 가중치 파일 경로 (None이면 기본 경로)

    Returns:
        (model, device) 튜플
    """
    if _cache["model"] is not None:
        return _cache["model"], _cache["device"]


    import importlib.util

    # config 모듈 로드
    _cfg_path = os.path.join(_HRNET_LIB, "config", "default.py")
    _cfg_spec = importlib.util.spec_from_file_location("hrnet_config", _cfg_path)
    _cfg_module = importlib.util.module_from_spec(_cfg_spec)
    _cfg_spec.loader.exec_module(_cfg_module)
    cfg = _cfg_module._C

    # pose_hrnet 모듈 로드
    _model_path = os.path.join(_HRNET_LIB, "models", "pose_hrnet.py")
    _model_spec = importlib.util.spec_from_file_location("pose_hrnet", _model_path)
    _model_module = importlib.util.module_from_spec(_model_spec)
    _model_spec.loader.exec_module(_model_module)
    get_pose_net = _model_module.get_pose_net

    device = "cuda" if torch.cuda.is_available() else "cpu"

    # config YAML
    cfg_file = os.path.join(
        _BACKEND_DIR,
        "HRNet-Human-Pose-Estimation",
        "experiments", "coco", "hrnet",
        "w48_384x288_adam_lr1e-3.yaml",
    )
    if not os.path.exists(cfg_file):
        raise FileNotFoundError(
            f"HRNet config 파일을 찾을 수 없습니다: {cfg_file}\n"
            "backend/ 안에 HRNet 레포를 클론했는지 확인하세요:\n"
            "  git clone https://github.com/HRNet/HRNet-Human-Pose-Estimation.git"
        )

    cfg.defrost()
    cfg.merge_from_file(cfg_file)
    cfg.freeze()

    # 가중치
    wp = weight_path or _DEFAULT_WEIGHT
    if not os.path.exists(wp):
        raise FileNotFoundError(
            f"HRNet 가중치 파일을 찾을 수 없습니다: {wp}\n"
            "models/hrnet/weights/ 에 pose_hrnet_w48_384x288.pth 를 배치하세요."
        )

    model = get_pose_net(cfg, is_train=False)
    state_dict = torch.load(wp, map_location=device)
    model.load_state_dict(state_dict, strict=True)
    model.to(device)
    model.eval()

    param_count = sum(p.numel() for p in model.parameters()) / 1e6
    print(f"[INFO] HRNet-W48 loaded ({param_count:.1f}M params) on {device}")

    _cache["model"] = model
    _cache["device"] = device
    return model, device


# ============================================================
# 2. 포즈 추출 (1 프레임)
# ============================================================
def extract_keypoints_hrnet(model, frame, bbox, device, use_flip_test=True):
    """
    YOLO bbox 기반으로 HRNet 포즈 추출 → H36M 17관절 반환.

    Args:
        model: HRNet 모델
        frame: BGR 원본 프레임
        bbox: (x1, y1, x2, y2)
        device: 'cuda' or 'cpu'
        use_flip_test: flip 앙상블 적용 여부

    Returns:
        np.ndarray [17, 3] (x, y, confidence) H36M 형식
    """
    center, scale = _bbox_to_center_scale(bbox)

    # Affine crop
    trans = _get_affine_transform(center, scale, (INPUT_SIZE[1], INPUT_SIZE[0]))
    cropped = cv2.warpAffine(
        frame, trans, (INPUT_SIZE[1], INPUT_SIZE[0]),
        flags=cv2.INTER_LINEAR,
    )

    # ImageNet 정규화
    inp = (cropped.astype(np.float32) / 255.0 - IMAGENET_MEAN) / IMAGENET_STD
    inp = torch.from_numpy(inp.transpose(2, 0, 1)).unsqueeze(0).to(device)

    # HRNet forward
    with torch.no_grad():
        output = model(inp)

        if use_flip_test:
            inp_flip = torch.flip(inp, [3])
            out_flip = model(inp_flip)
            out_flip = _flip_back(out_flip.cpu().numpy())
            out_flip = torch.from_numpy(out_flip).to(device)
            out_flip[:, :, :, 1:] = out_flip.clone()[:, :, :, 0:-1]
            output = (output + out_flip) * 0.5

    heatmaps = output.cpu().numpy()

    # 히트맵 → COCO 좌표
    coco_kpts, coco_scores = _decode_heatmap(heatmaps, center, scale)

    # COCO → H36M
    h36m_kpts, h36m_scores = _coco_to_h36m(coco_kpts, coco_scores)

    return np.concatenate([h36m_kpts, h36m_scores[:, None]], axis=-1)


# ============================================================
# 3. COCO → H36M 변환
# ============================================================
def _coco_to_h36m(coco_kpts, coco_scores):
    """COCO 17관절 → H36M 17관절."""
    h36m_kpts = np.zeros((17, 2), dtype=np.float32)
    h36m_scores = np.zeros(17, dtype=np.float32)

    direct_map = {
        1: COCO["r_hip"],       2: COCO["r_knee"],     3: COCO["r_ankle"],
        4: COCO["l_hip"],       5: COCO["l_knee"],     6: COCO["l_ankle"],
        9: COCO["nose"],
        11: COCO["l_shoulder"], 12: COCO["l_elbow"],   13: COCO["l_wrist"],
        14: COCO["r_shoulder"], 15: COCO["r_elbow"],   16: COCO["r_wrist"],
    }
    for h_idx, c_idx in direct_map.items():
        h36m_kpts[h_idx] = coco_kpts[c_idx]
        h36m_scores[h_idx] = coco_scores[c_idx]

    # Pelvis
    h36m_kpts[0] = (coco_kpts[COCO["l_hip"]] + coco_kpts[COCO["r_hip"]]) / 2
    h36m_scores[0] = min(coco_scores[COCO["l_hip"]], coco_scores[COCO["r_hip"]])
    # Neck
    h36m_kpts[8] = (coco_kpts[COCO["l_shoulder"]] + coco_kpts[COCO["r_shoulder"]]) / 2
    h36m_scores[8] = min(coco_scores[COCO["l_shoulder"]], coco_scores[COCO["r_shoulder"]])
    # Spine
    h36m_kpts[7] = (h36m_kpts[0] + h36m_kpts[8]) / 2
    h36m_scores[7] = min(h36m_scores[0], h36m_scores[8])
    # Head
    h36m_kpts[10] = (coco_kpts[COCO["l_ear"]] + coco_kpts[COCO["r_ear"]]) / 2
    h36m_scores[10] = min(coco_scores[COCO["l_ear"]], coco_scores[COCO["r_ear"]])

    return h36m_kpts, h36m_scores


# ============================================================
# 4. Affine Transform 유틸
# ============================================================
def _get_dir(src_point, rot_rad):
    sn, cs = np.sin(rot_rad), np.cos(rot_rad)
    return np.array(
        [src_point[0] * cs - src_point[1] * sn,
         src_point[0] * sn + src_point[1] * cs],
        dtype=np.float32,
    )


def _get_3rd_point(a, b):
    d = a - b
    return b + np.array([-d[1], d[0]], dtype=np.float32)


def _get_affine_transform(center, scale, output_size, rot=0, inv=False):
    src_w = scale[0]
    dst_w, dst_h = output_size
    rot_rad = np.pi * rot / 180
    src_dir = _get_dir([0, src_w * -0.5], rot_rad)
    dst_dir = np.array([0, dst_w * -0.5], dtype=np.float32)

    src = np.zeros((3, 2), dtype=np.float32)
    dst = np.zeros((3, 2), dtype=np.float32)
    src[0, :] = center
    src[1, :] = center + src_dir
    dst[0, :] = [dst_w * 0.5, dst_h * 0.5]
    dst[1, :] = np.array([dst_w * 0.5, dst_h * 0.5]) + dst_dir
    src[2, :] = _get_3rd_point(src[0, :], src[1, :])
    dst[2, :] = _get_3rd_point(dst[0, :], dst[1, :])

    if inv:
        return cv2.getAffineTransform(dst, src)
    return cv2.getAffineTransform(src, dst)


def _bbox_to_center_scale(bbox, aspect_ratio=288 / 384, padding=1.25):
    x1, y1, x2, y2 = bbox
    w, h = x2 - x1, y2 - y1
    center = np.array([(x1 + x2) / 2, (y1 + y2) / 2], dtype=np.float32)
    if w > aspect_ratio * h:
        h = w / aspect_ratio
    elif w < aspect_ratio * h:
        w = h * aspect_ratio
    return center, np.array([w * padding, h * padding], dtype=np.float32)


# ============================================================
# 5. 히트맵 디코딩
# ============================================================
def _flip_back(output_flipped):
    flipped = output_flipped[:, :, :, ::-1].copy()
    for l, r in FLIP_PAIRS:
        flipped[:, l], flipped[:, r] = flipped[:, r].copy(), flipped[:, l].copy()
    return flipped


def _get_max_preds(heatmaps):
    B, J, H, W = heatmaps.shape
    flat = heatmaps.reshape(B, J, -1)
    idx = np.argmax(flat, axis=2)
    maxvals = np.amax(flat, axis=2).reshape(B, J, 1)
    preds = np.zeros((B, J, 2), dtype=np.float32)
    preds[:, :, 0] = idx % W
    preds[:, :, 1] = idx // W
    preds *= (maxvals > 0.0).reshape(B, J, 1)
    return preds, maxvals


def _decode_heatmap(heatmaps, center, scale):
    coords, maxvals = _get_max_preds(heatmaps)
    H, W = heatmaps.shape[2], heatmaps.shape[3]

    for n in range(coords.shape[0]):
        for j in range(coords.shape[1]):
            hm = heatmaps[n][j]
            px, py = int(coords[n][j][0]), int(coords[n][j][1])
            if 1 < px < W - 1 and 1 < py < H - 1:
                coords[n][j][0] += np.sign(hm[py][px + 1] - hm[py][px - 1]) * 0.25
                coords[n][j][1] += np.sign(hm[py + 1][px] - hm[py - 1][px]) * 0.25

    trans = _get_affine_transform(center, scale, (W, H), inv=True)
    for j in range(coords.shape[1]):
        pt = np.array([coords[0][j][0], coords[0][j][1], 1.0])
        coords[0][j] = (trans @ pt)[:2]

    return coords[0], maxvals[0].flatten()