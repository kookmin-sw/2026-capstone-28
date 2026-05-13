"""
analyze() 결과를 프론트엔드 친화적인 형식으로 정리.
video_a_id, video_b_id로 Supabase에서 영상 URL을 조회해 함께 반환.

[입력]
  analyze_result: {
    "model_output": infer_similarity() 결과,
    "agent_report": generate_similarity_report() 결과,
    "video_a_id": int,
    "video_b_id": int,
  }

[출력]
  프론트엔드 result_page.jsx가 소비하는 dict:
  {
    video_a_id, video_b_id, video_url_a, video_url_b,
    overall: {score, interpretation},
    summary, key_differences,
    segments: [{id, score, video_a, video_b, description, body_parts}, ...]
  }
"""
import re
import logging
from typing import Optional

from utils.supabase_client import get_supabase

logger = logging.getLogger(__name__)


def _fetch_video_url(video_id: int) -> Optional[str]:
    """videos 테이블에서 video_url 조회."""
    if video_id is None:
        return None
    try:
        sb = get_supabase()
        res = sb.table("videos").select("video_url").eq("vid", video_id).single().execute()
        return res.data.get("video_url") if res.data else None
    except Exception as e:
        logger.warning(f"video_url 조회 실패 (vid={video_id}): {e}")
        return None


def format_result(analyze_result: dict) -> dict:
    model_output = analyze_result.get("model_output") or {}
    agent_report = analyze_result.get("agent_report") or {}

    video_a_id = analyze_result.get("video_a_id")
    video_b_id = analyze_result.get("video_b_id")

    motion_segments = model_output.get("motion_segments", [])

    # ====== 영상 URL 조회 ======
    video_url_a = _fetch_video_url(video_a_id)
    video_url_b = _fetch_video_url(video_b_id)

    # ====== 상단 요약 ======
    overall = {
        "score": round(model_output.get("global_score", 0.0) * 100, 1),
        "interpretation": agent_report.get("overall_score_interpretation", ""),
    }

    # ====== 유사 구간 — agent description + model 수치 병합 ======
    segments = []
    for seg in agent_report.get("similar_segments", []):
        seg_id = seg.get("id")
        ms = next((m for m in motion_segments if m.get("id") == seg_id), None)

        # score: motion_sim 기반 (0~1 → 백분율)
        score = round(ms.get("motion_sim", 0) * 100, 1) if ms else 0

        # body_parts: 1초 단위 평균 (pose 기반, 더 정밀)
        # fallback으로 motion_body_parts 사용
        body_parts = {}
        if ms:
            body_parts = ms.get("body_parts") or ms.get("motion_body_parts", {})

        segments.append({
            "id": seg_id,
            "score": score,
            "video_a": _parse_time_range(seg.get("time_a", "")),
            "video_b": _parse_time_range(seg.get("time_b", "")),
            "description": seg.get("description", ""),
            "body_parts": body_parts,
        })

    return {
        "video_a_id": video_a_id,
        "video_b_id": video_b_id,
        "video_url_a": video_url_a,
        "video_url_b": video_url_b,
        "overall": overall,
        "summary": agent_report.get("summary", ""),
        "key_differences": agent_report.get("key_differences", []),
        "segments": segments,
    }


_TIME_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*~\s*(\d+(?:\.\d+)?)")


def _parse_time_range(time_str: str) -> Optional[dict]:
    if not time_str:
        return None
    match = _TIME_PATTERN.search(time_str)
    if not match:
        return None
    return {
        "start": float(match.group(1)),
        "end": float(match.group(2)),
    }