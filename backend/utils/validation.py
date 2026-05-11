import subprocess
import json
from pathlib import Path
from fastapi import UploadFile, HTTPException

MAX_SIZE_MB = 50
MAX_DURATION_SEC = 300  # 5분
ALLOWED_MIME = {"video/mp4", "video/quicktime"}
ALLOWED_EXT = {".mp4", ".mov"}

# 에러 메시지에 공통으로 붙는 형식 안내
_FORMAT_GUIDE = f"형식: ({MAX_SIZE_MB}MB 이하 / {MAX_DURATION_SEC}초 이하 / mp4, mov)"


def _err(filename: str, reason: str) -> HTTPException:
    """
    통일된 에러 메시지 생성.

    출력 예시:
        영상 A.mp4가 형식에 맞지 않습니다. 다시 확인해주세요.
        형식: (500MB 이하 / 300초 이하 / mp4, mov)
        원인: 파일 크기 초과 (612.3MB)
    """
    detail = (
        f"{filename}가 형식에 맞지 않습니다. 다시 확인해주세요.\n"
        f"{_FORMAT_GUIDE}\n"
        f"원인: {reason}"
    )
    return HTTPException(status_code=400, detail=detail)


def validate_format(file: UploadFile) -> None:
    """파일 형식(MIME + 확장자) 검증"""
    ext = Path(file.filename or "").suffix.lower()
    if file.content_type not in ALLOWED_MIME or ext not in ALLOWED_EXT:
        raise _err(
            file.filename,
            f"mp4 또는 mov 형식이 아닙니다 (받은 형식: {ext or '알 수 없음'})",
        )


def validate_size(file: UploadFile, file_bytes: bytes) -> None:
    """파일 크기 검증"""
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise _err(
            file.filename,
            f"파일 크기 초과 ({size_mb:.1f}MB)",
        )


def validate_duration(file_path: Path, filename: str) -> float:
    """ffprobe로 영상 길이 검증. 통과 시 duration(초) 반환"""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                str(file_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise _err(filename, "영상 파일을 읽을 수 없습니다")

        info = json.loads(result.stdout)
        duration = float(info["format"]["duration"])

    except (KeyError, ValueError, json.JSONDecodeError):
        raise _err(filename, "영상 메타데이터 파싱 실패")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="ffprobe가 설치되어 있지 않습니다.")

    if duration > MAX_DURATION_SEC:
        raise _err(
            filename,
            f"영상 길이 초과 ({duration:.0f}초)",
        )

    return duration