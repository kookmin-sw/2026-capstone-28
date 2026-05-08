"""
Supabase 연동 — 영상 메타데이터 조회 및 Storage 다운로드.

- DB에서 video_id로 영상 정보 조회
- Storage(또는 URL)에서 영상 파일을 임시 디렉토리로 다운로드
- 다운로드 실패 시 임시 파일 정리


"""
import os
import logging
import tempfile
from contextlib import contextmanager
from typing import Generator

import requests
from supabase import create_client, Client

from core.config import SUPABASE_URL, SUPABASE_KEY, TEMP_DIR 

logger = logging.getLogger(__name__)


# ============================================================
# Supabase 클라이언트 — lazy initialization
# ============================================================
_client: Client | None = None


def get_supabase() -> Client:

    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL / SUPABASE_KEY가 설정되지 않았습니다.\n"
                "backend/.env 파일을 확인하세요."
            )
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Supabase 클라이언트 초기화 완료")
    return _client


# ============================================================
# DB 조회
# ============================================================
def get_video_url(video_id: int) -> str:

    sb = get_supabase()
    result = (
        sb.table("videos")
        .select("video_url")
        .eq("vid", video_id)
        .single()
        .execute()
    )
    if not result.data:
        raise ValueError(f"video_id={video_id}에 해당하는 영상을 찾을 수 없습니다.")
    return result.data["video_url"]


# ============================================================
# Storage 다운로드
# ============================================================
def download_video_to_temp(video_url: str, suffix: str = ".mp4") -> str:

    # TEMP_DIR 안에 임시 파일 생성 (한 곳에 모아두면 청소가 쉬움)
    fd, temp_path = tempfile.mkstemp(suffix=suffix, dir=str(TEMP_DIR))

    try:
        logger.info(f"📥 영상 다운로드 시작: {video_url[:80]}...")
        with requests.get(video_url, stream=True, timeout=60) as response:
            response.raise_for_status()
            with os.fdopen(fd, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        logger.info(f"✅ 다운로드 완료: {temp_path}")
        return temp_path

    except Exception as e:
        # 실패 시 임시 파일 정리
        try:
            os.close(fd)
        except OSError:
            pass
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logger.error(f"❌ 다운로드 실패: {e}")
        raise


# ============================================================
# 헬퍼 — context manager로 자동 정리
# ============================================================
@contextmanager
def fetch_video(video_id: int) -> Generator[str, None, None]:
    """
    video_id로 영상을 확보하고, 사용 후 임시 파일을 정리한다.

    우선순위:
      1) 업로드 단계에서 TEMP_DIR/{vid}.mp4로 남겨둔 로컬 캐시가 있으면 그대로 사용 (재다운로드 회피).
         캐시 파일은 yield 이후에도 유지해 다음 요청에서 재활용 가능.
      2) 캐시가 없으면 Supabase에서 다운로드 → 임시 파일 생성 → 사용 후 삭제.

    사용 예:
        with fetch_video(123) as path:
            result = extract_object_from_path(path)
    """
    cached_path = TEMP_DIR / f"{video_id}.mp4"
    if cached_path.exists():
        logger.info(f"♻️  로컬 캐시 사용: {cached_path}")
        yield str(cached_path)
        return

    url = get_video_url(video_id)
    temp_path = download_video_to_temp(url)
    try:
        yield temp_path
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            logger.info(f"🗑️  임시 파일 삭제: {temp_path}")