# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> 저장소 전반의 가이드는 상위 `../CLAUDE.md`에 있습니다. 이 파일은 **`backend/` 내부 작업 시에만 필요한 세부 사항**을 보충합니다.

## 디렉터리 역할

- `main.py` — FastAPI 진입점. `lifespan`에서 `ModelRegistry.load_all()`을 호출하며, `/api/videos/*`와 `/api/*` 두 라우터를 마운트합니다.
- `core/` — `config.py`(경로/하이퍼파라미터/Supabase 환경변수)와 `model_loader.py`(모델 싱글톤 레지스트리).
- `api/` — HTTP 라우터. **비즈니스 로직은 최소화**되어 있고 `model_pipeline` / `utils` / `repository`로 위임합니다.
- `model_pipeline/` — 분석 파이프라인 단계별 모듈. 호출 순서: `analyze.py` → `object_extractor.py` → `bert_embedder.py` → `inferrence.py` → `report.py` → `result_formatter.py`.
- `models/` — 모델별 로더/아키텍처 + `weights/` 하위의 가중치 파일.
- `repository/` — Supabase DB·Storage 접근 (영상 조회/다운로드).
- `schemas/` — Pydantic 응답 스키마 (HTTP 바디용).
- `utils/` — ffmpeg·검증·Supabase 클라이언트 래퍼.
- `temp/` — 분석 중 다운로드된 영상의 임시 저장소 (런타임에 자동 생성).
- `test_data/` — 개발 중 수동 테스트용 샘플 (자동 테스트 스위트 아님).

## `core/` 규칙

- **모든 경로·디바이스·하이퍼파라미터는 `core/config.py`를 통해서만 접근**합니다. 파이프라인이나 모델 파일에서 경로 리터럴을 직접 쓰지 마세요.
- `DEVICE = "cpu"`는 고정입니다. CUDA를 가정한 코드를 추가하지 않습니다.
- `ModelRegistry`는 프로세스 전체에서 한 번만 로드됩니다. 새 모델을 추가하려면:
  1. `core/config.py`에 가중치 경로 상수 추가
  2. `models/<name>/` 하위에 로더 함수 작성
  3. `ModelRegistry.__init__`에 슬롯 추가, `load_all()` / `_load_<name>()` 메서드 추가
  테스트 스크립트에서도 반드시 `ModelRegistry.get().load_all()`을 먼저 호출해야 합니다 (`analyze.py` 상단이 이미 안전장치로 호출).

## 파이프라인 데이터 형상 (틀리면 `_validate`에서 예외)

| 단계 | 입력 | 출력 |
|---|---|---|
| `extract_objects` | `video_id: int` | `{fps, num_frames, width, height, keypoints: [F, 17, 3]}` |
| `embed_motion` | `[F, 17, 3]` (F ≤ 243, 실제 cap은 240) | `[F, 17, 512]` |
| `infer_similarity` | `emb_a, emb_b: [F, 17, 512]` + `kps_a, kps_b: [F, 17, 3]` | dict (`global_score`, `motion_segments`, ...) |
| `generate_similarity_report` | 위 dict | `ReportResult` dict |
| `format_result` | `{model_output, agent_report, video_a_id, video_b_id, elapsed_time}` | 프론트엔드용 최종 dict |

- **키포인트 3번째 채널은 visibility**입니다 (confidence 아님). `inferrence._is_static_segment`는 visibility를 무시하고 `[..., :2]`만 사용합니다.
- **관절 순서는 H36M 17관절**이며 `object_extractor._convert_to_h36m`에서 MediaPipe 33관절을 매핑합니다. `BODY_PARTS` dict(`inferrence.py`)의 인덱스는 이 순서에 종속됩니다.
- **프레임 서브샘플링**은 `extract_object_from_path(sample_rate=2)` 기본값으로 30fps 영상이 ~15fps가 됩니다. 파이프라인 상수 `FPS = 10`은 시간 환산용 상수이므로 실제 샘플링 레이트와 어긋나면 `time_a` / `time_b` 초 계산이 틀어집니다. 변경 시 두 값을 함께 맞춰야 합니다.
- **240프레임 상한** (`object_extractor.py::MAX_FRAMES`)이 있어 긴 영상은 앞부분만 분석됩니다.

## `api/video_upload.py` 주의점

- `TEMP_DIR = Path("/tmp/tenein_videos")`가 하드코딩되어 있어 **Windows에서 동작하지 않을 수 있습니다**. 로컬에서 테스트하다가 업로드가 실패하면 이 경로를 먼저 확인하세요.
- ffmpeg 재인코딩·ffprobe·Supabase 업로드는 모두 **블로킹**이라 `run_in_threadpool`로 감쌌습니다. 새 무거운 작업을 추가할 때도 동일 패턴을 지켜야 이벤트 루프가 막히지 않습니다.
- 업로드 시 `analyses` 테이블에 `status="pending"`으로 INSERT하고, 이후 `/api/analyze`가 같은 `aid`를 **UPDATE**합니다. 둘 중 하나만 호출되는 상태가 정상 플로우가 아님에 유의하세요.
- `video_upload.py`의 `get_supabase()`는 `utils/supabase_client.py`를, `repository/video_repository.py`의 `get_supabase()`는 자체 클라이언트를 만드는 **두 개의 분리된 싱글톤**이 존재합니다. 둘 다 `SERVICE_ROLE_KEY`를 쓰므로 동작은 같지만, 통합할 때 두 곳 모두 수정해야 합니다.

## Supabase 스키마 (코드에서 관찰된 것만)

DDL은 Supabase 콘솔에만 있고 저장소에는 없습니다. 코드에서 확인되는 컬럼:

- `videos(vid: int pk, user_id: uuid, title: text, video_url: text)`
- `analyses(aid: int pk, user_id: uuid, video_id: int fk→videos.vid, result_data: jsonb)`
  - `result_data`는 업로드 시점에는 `{vid_a, vid_b, video_url_a, video_url_b, storage_path_a, storage_path_b, duration_a, duration_b, status}`, 분석 완료 후에는 `format_result()` 출력으로 덮어씌워집니다. 즉 **같은 jsonb 필드의 스키마가 두 번 바뀝니다** — 프론트엔드에서 `status` 필드 유무로 구분해야 합니다.
- Storage 버킷: `videos` (기본값). 경로 컨벤션은 `{user_id}/{session_id}_{a|b}.mp4`.

## LLM 리포트 (`report.py`)

- `langchain-openai`의 `ChatOpenAI`를 사용하며 `OPENAI_API_KEY` 환경변수가 필요합니다.
- 출력은 `ReportResult` Pydantic 모델로 강제됩니다 (`JsonOutputParser`). 모델이 반환한 `similar_segments[*].id`는 `inferrence.py`가 생성한 `motion_segments[*].id`와 **1:1 매칭**되어 `result_formatter`에서 병합됩니다. id 체계를 바꾸면 포맷터가 깨집니다.

## 실행·디버깅 팁

- 서버 기동 시 모델 4개 로드에 수십 초가 걸립니다. `--reload`로 파일을 수정할 때마다 재로드되므로, 파이프라인만 고치는 경우 서버를 띄워두고 별도 스크립트로 호출하는 편이 빠릅니다.
- `/health` 엔드포인트가 `ModelRegistry._loaded`를 반환하므로 모델 로드 완료 여부를 여기서 확인할 수 있습니다.
- `analyze()` 내부 각 단계가 `logger.info`로 소요 시간을 찍습니다. 느린 단계를 찾을 때 로그 레벨 조정 없이 바로 확인하세요.
- 기존 코드 스타일을 유지한채로 코드를 작성하거나 수정합니다.
- IT 업계에서 15년 근무하는 연봉 $20000 시니어 개발자로서 활동합니다. 
