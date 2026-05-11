import uuid
import shutil
import yt_dlp
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, Depends, Header, HTTPException
from fastapi.concurrency import run_in_threadpool

from core.config import TEMP_DIR
from utils.supabase_client import get_supabase
from utils.validation import validate_format, validate_size, validate_duration
from utils.ffmpeg_utils import convert_to_h264, get_video_codec
from schemas.video import UploadResponse, VideoMeta

router = APIRouter()

# 임시 파일 저장은 core.config.TEMP_DIR (backend/temp)를 공유한다.
# 업로드가 끝난 뒤 최종 출력물을 {vid}.mp4로 rename해 두면,
# 이어지는 /api/analyze 단계에서 repository.fetch_video가 바로 재사용한다.
TEMP_DIR.mkdir(parents=True, exist_ok=True)

def download_youtube_video(url: str, output_path: Path) -> None:
    if not url or ("youtube.com" not in url and "youtu.be" not in url):
        raise HTTPException(status_code=400, detail="유튜브 URL만 입력할 수 있습니다.")
    # playlist 전체 다운로드 방지
    url = url.split("&list=")[0]

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "outtmpl": str(output_path),
        "quiet": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"URL 영상 다운로드 실패: {e}")


# ─────────────────────────────────────────────────────────────
#  토큰에서 user_id 추출 (Supabase JWT 검증)
# ─────────────────────────────────────────────────────────────
async def get_current_user_id(authorization: str = Header(...)) -> str:
    """
    프론트에서 Authorization: Bearer <supabase_access_token> 헤더를 보내면
    Supabase에 검증 요청 후 user_id(uuid) 반환.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 토큰이 없습니다.")

    token = authorization.removeprefix("Bearer ").strip()
    sb = get_supabase()

    try:
        res = sb.auth.get_user(token)
        return str(res.user.id)
    except Exception:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")


# ─────────────────────────────────────────────────────────────
#  POST /api/videos/upload
# ─────────────────────────────────────────────────────────────
@router.post("/upload", response_model=UploadResponse)
async def upload_videos(
    video_a: UploadFile | None = File(None, description="비교 영상 A"),
    video_b: UploadFile | None = File(None, description="비교 영상 B"),
    video_a_url: str | None = Form(None),
    video_b_url: str | None = Form(None),

    user_id: str = Depends(get_current_user_id),
    #user_id: str = "test-user-id",
):
    """
    영상 2개를 받아 검증 → 코덱 변환 → DB 저장 → 분석 레코드 생성

    Flow:
      1. 형식 검증 (MIME + 확장자)
      2. 파일 크기 검증 (< 500MB)
      3. 임시 저장
      4. 영상 길이 검증 (< 5분, ffprobe)
      5. 코덱 변환 (H.264 + AAC, ffmpeg)
      6. Supabase Storage 업로드
      7. videos 테이블 INSERT (A, B 각각)
      8. analyses 테이블 INSERT
      9. 임시 파일 정리
    """

    # ── Step 1: 형식 검증 ────────────────────────────────────


    if not video_a and not video_a_url:
        raise HTTPException(status_code=400, detail="영상 A 파일 또는 URL이 필요합니다.")
    if not video_b and not video_b_url:
        raise HTTPException(status_code=400, detail="영상 B 파일 또는 URL이 필요합니다.")


    session_id = uuid.uuid4().hex

    tmp_raw_a = TEMP_DIR / f"{session_id}_a_raw.mp4"
    tmp_raw_b = TEMP_DIR / f"{session_id}_b_raw.mp4"
    tmp_out_a = TEMP_DIR / f"{session_id}_a_out.mp4"
    tmp_out_b = TEMP_DIR / f"{session_id}_b_out.mp4"

    title_a = ""
    title_b = ""
    bytes_a = b""
    bytes_b = b""

    if video_a:
        validate_format(video_a)
        bytes_a = await video_a.read()
        validate_size(video_a, bytes_a)

        ext_a = Path(video_a.filename).suffix.lower()
        tmp_raw_a = TEMP_DIR / f"{session_id}_a_raw{ext_a}"
        tmp_raw_a.write_bytes(bytes_a)
        title_a = video_a.filename
    else:
        await run_in_threadpool(download_youtube_video, video_a_url, tmp_raw_a)
        bytes_a = tmp_raw_a.read_bytes()
        title_a = video_a_url

        dummy_file_a = type(
            "DummyFile",
            (),
            {
                "filename": title_a,
                "content_type": "video/mp4",
            },
        )()
        validate_size(dummy_file_a, bytes_a)

    if video_b:
        validate_format(video_b)
        bytes_b = await video_b.read()
        validate_size(video_b, bytes_b)

        ext_b = Path(video_b.filename).suffix.lower()
        tmp_raw_b = TEMP_DIR / f"{session_id}_b_raw{ext_b}"
        tmp_raw_b.write_bytes(bytes_b)
        title_b = video_b.filename
    else:
        await run_in_threadpool(download_youtube_video, video_b_url, tmp_raw_b)
        bytes_b = tmp_raw_b.read_bytes()
        title_b = video_b_url
        dummy_file_b = type(
            "DummyFile",
            (),
            {
                "filename": title_b,
                "content_type": "video/mp4",
            },
        )()
        validate_size(dummy_file_b, bytes_b)

    try:
        # ── Step 4: 영상 길이 검증 (ffprobe, blocking → threadpool) ──
        duration_a = await run_in_threadpool(validate_duration, tmp_raw_a, title_a)
        duration_b = await run_in_threadpool(validate_duration, tmp_raw_b, title_b)

        # ── Step 5: 코덱 변환 (ffmpeg, blocking → threadpool) ────────
        await run_in_threadpool(convert_to_h264, tmp_raw_a, tmp_out_a, title_a)
        await run_in_threadpool(convert_to_h264, tmp_raw_b, tmp_out_b, title_b)

        codec_a = await run_in_threadpool(get_video_codec, tmp_out_a)
        codec_b = await run_in_threadpool(get_video_codec, tmp_out_b)

        # ── Step 6: Supabase Storage 업로드 ──────────────────────────
        sb = get_supabase()

        storage_path_a = f"{user_id}/{session_id}_a.mp4"
        storage_path_b = f"{user_id}/{session_id}_b.mp4"

        with open(tmp_out_a, "rb") as f:
            sb.storage.from_("videos").upload(
                storage_path_a,
                f.read(),
                file_options={"content-type": "video/mp4"},
            )
        with open(tmp_out_b, "rb") as f:
            sb.storage.from_("videos").upload(
                storage_path_b,
                f.read(),
                file_options={"content-type": "video/mp4"},
            )

        # Storage URL 생성
        video_url_a = sb.storage.from_("videos").get_public_url(storage_path_a)
        video_url_b = sb.storage.from_("videos").get_public_url(storage_path_b)

        # ── Step 7: videos 테이블 INSERT ─────────────────────────────
        res_va = (
            sb.table("videos")
            .insert({"user_id": user_id, 
                    "title": title_a,
                    "video_url": video_url_a, #url추가
                    }) 
            .execute()
        )
        vid_a_id: int = res_va.data[0]["vid"]

        res_vb = (
            sb.table("videos")
            .insert({"user_id": user_id,
                    "title": title_b,
                    "video_url": video_url_b, #url추가
                    })
            .execute()
        )
        vid_b_id: int = res_vb.data[0]["vid"]

        # ── Step 7.5: 로컬 캐시로 rename ────────────────────────────
        #   vid 기준 고정 경로({vid}.mp4)로 바꿔두면 /api/analyze 단계의
        #   fetch_video(video_id)가 Supabase 재다운로드 없이 바로 재사용한다.
        cache_path_a = TEMP_DIR / f"{vid_a_id}.mp4"
        cache_path_b = TEMP_DIR / f"{vid_b_id}.mp4"
        try:
            tmp_out_a.replace(cache_path_a)
            tmp_out_b.replace(cache_path_b)
        except OSError:
            # rename 실패해도 업로드 자체는 성공했으니 분석은 Supabase 다운로드로 fallback.
            # 원본/변환 임시 파일은 아래 finally 블록이 정리한다.
            pass

        # ── Step 8: analyses 테이블 INSERT ───────────────────────────
        #   video_id FK는 A 영상으로, 영상 B vid는 result_data jsonb에 보관
        #   (스키마에 video_id 컬럼이 단일 FK이므로)
        res_analysis = (
            sb.table("analyses")
            .insert(
                {
                    "user_id": user_id,
                    "video_id": vid_a_id,
                    "result_data": {
                        "vid_a": vid_a_id,
                        "vid_b": vid_b_id,
                        "video_url_a": video_url_a,  # URL 추가
                        "video_url_b": video_url_b,  # URL 추가
                        "storage_path_a": storage_path_a,
                        "storage_path_b": storage_path_b,
                        "duration_a": round(duration_a, 2),
                        "duration_b": round(duration_b, 2),
                        "status": "pending",  # 모델 분석 전
                    },
                }
            )
            .execute()
        )
        analysis_id: int = res_analysis.data[0]["aid"]

    finally:
        # ── Step 9: 임시 파일 정리 ───────────────────────────────────
        # 원본(raw)은 항상 삭제. 변환 출력(out)은 rename으로 캐시에 옮겨졌다면
        # 이 시점에 이미 존재하지 않으므로 exists() 체크만으로 충분.
        for f in [tmp_raw_a, tmp_raw_b, tmp_out_a, tmp_out_b]:
            if f.exists():
                f.unlink()

    return UploadResponse(
        analysis_id=analysis_id,
        video_a=VideoMeta(
            vid=vid_a_id,
            title=title_a,
            size_mb=round(len(bytes_a) / (1024 * 1024), 2),
            duration_sec=round(duration_a, 2),
            codec=codec_a,
        ),
        video_b=VideoMeta(
            vid=vid_b_id,
            title=title_b,
            size_mb=round(len(bytes_b) / (1024 * 1024), 2),
            duration_sec=round(duration_b, 2),
            codec=codec_b,
        ),
        redirect_url=f"/analysis/{analysis_id}",
        message="업로드 및 검증 완료. 분석을 시작합니다.",
    )