import subprocess
from pathlib import Path
from fastapi import HTTPException


def convert_to_h264(input_path: Path, output_path: Path, filename: str) -> Path:
    """
    입력 영상을 H.264 + AAC 코덱으로 변환한다.
    이미 H.264인 경우에도 컨테이너 정규화를 위해 재인코딩한다.

    Returns:
        output_path (변환된 파일 경로)
    """
    cmd = [
        "ffmpeg",
        "-y",                        # 덮어쓰기 허용
        "-i", str(input_path),       # 입력
        "-c:v", "libx264",           # 비디오 코덱: H.264
        "-preset", "fast",           # 인코딩 속도 (ultrafast/superfast/fast/medium)
        "-crf", "23",                # 품질 (18=고품질, 28=저품질, 기본 23)
        "-c:a", "aac",               # 오디오 코덱: AAC
        "-b:a", "128k",              # 오디오 비트레이트
        "-movflags", "+faststart",   # 웹 스트리밍 최적화 (moov atom을 앞으로)
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",  # 짝수 해상도 강제 (libx264 요구사항)
        str(output_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 최대 10분
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail=f"[{filename}] 코덱 변환 시간 초과.")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="ffmpeg가 설치되어 있지 않습니다.")

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"[{filename}] 코덱 변환 실패: {result.stderr[-300:]}",
        )

    return output_path


def get_video_codec(file_path: Path) -> str:
    """현재 파일의 비디오 코덱 이름 반환 (예: 'h264', 'hevc')"""
    import subprocess, json
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            "-select_streams", "v:0",
            str(file_path),
        ],
        capture_output=True, text=True,
    )
    try:
        streams = json.loads(result.stdout).get("streams", [])
        return streams[0].get("codec_name", "unknown") if streams else "unknown"
    except Exception:
        return "unknown"