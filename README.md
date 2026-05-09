<div align="center">

# 🎯 Tenein — K-pop 안무 유사도 분석 시스템

**AI 기반 K-pop 안무 영상 비교 · 분석 · 보고서 자동 생성 웹 서비스**

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF?logo=vite&logoColor=white)](https://vitejs.dev)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org)
[![Supabase](https://img.shields.io/badge/Supabase-Auth%20·%20DB%20·%20Storage-3FCF8E?logo=supabase&logoColor=white)](https://supabase.com)

<br/>

<img src="docs/images/system_overview.png" alt="Tenein System Overview" width="720"/>

<br/>

*두 K-pop 안무 영상을 업로드하면 AI가 유사 구간을 탐지하고,*
*신체 부위별 유사도를 분석하여 PDF 보고서를 자동 생성합니다.*

</div>

---

## 📋 목차

- [프로젝트 소개](#-프로젝트-소개)
- [팀 소개](#-팀-소개)
- [시스템 아키텍처](#-시스템-아키텍처)
- [AI 모델 파이프라인](#-ai-모델-파이프라인)
- [웹 서비스](#-웹-서비스)
- [설치 및 실행](#-설치-및-실행)
- [사용 라이브러리](#-사용-라이브러리)
- [참고 문헌](#-참고-문헌)

---

## 🎬 프로젝트 소개

K-pop 안무 영상 간 유사도를 자동으로 분석하는 풀스택 AI 웹 서비스입니다.
두 영상을 업로드하면 딥러닝 파이프라인이 동작을 추출하고, 구간별 유사도를 계산한 뒤, LLM이 자연어 분석 보고서를 생성합니다.

### 주요 기능

| 기능 | 설명 |
|:---:|------|
| 🎯 **전체 유사도 분석** | 두 안무 영상의 전체 유사도 점수 산출 |
| 🔍 **구간별 탐지** | 시간 구간별 유사 안무 구간 자동 탐지 |
| 🦴 **부위별 분석** | 왼팔, 오른팔, 왼다리, 오른다리, 몸통 부위별 유사도 |
| 📊 **AI 보고서** | GPT-4o-mini 기반 자연어 분석 보고서 자동 생성 |
| 📄 **PDF 내보내기** | 분석 결과를 PDF 보고서로 다운로드 |
| 👤 **분석 히스토리** | 과거 분석 기록 조회 및 상세 보기 |

---

## 👥 팀 소개

### 팀명: Tenein

> *Tenein — 고대어로 "안무"를 뜻합니다.*

| 이름 | 역할 |
|:----:|------|
| 김수만 | AI 모델 설계, 3D Pose Lifting, GCN+Skip 모델 개발 |
| 김정인 | Tag Feature 설계, 멀티모달 모델 개발, 추론 파이프라인 |
| 배문경 | 프론트엔드 개발, UI/UX 디자인, PDF 보고서 시스템 |
| 백경지 | 백엔드 개발, API 설계, DB 설계, 인프라 구축 |

**지도교수:** 윤수연 (국민대학교 소프트웨어융합대학)

---

## 🏗 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Client Layer                                  │
│                                                                      │
│   React + Vite (localhost:5173)                                      │
│   ┌──────────┬──────────┬──────────┬──────────┬──────────┐          │
│   │  Login   │   Home   │  Result  │ Profile  │  About   │          │
│   │  Page    │   Page   │  Page    │  Page    │  Page    │          │
│   └──────────┴──────────┴──────────┴──────────┴──────────┘          │
│         │                     │              │                       │
│         │ Supabase Auth       │ PDF Export   │ History Modal         │
│         ▼                     ▼              ▼                       │
│   ┌──────────┐      ┌──────────────┐  ┌────────────────┐           │
│   │ Supabase │      │ @react-pdf/  │  │  generatePDF   │           │
│   │ JS Client│      │  renderer    │  │  (브라우저 내)   │           │
│   └──────────┘      └──────────────┘  └────────────────┘           │
│                                                                      │
├──────────────────────── HTTP REST ────────────────────────────────────┤
│                    POST /api/analyze                                 │
│                    { video_a_id, video_b_id }                        │
├──────────────────────────────────────────────────────────────────────┤
│                        Server Layer                                  │
│                                                                      │
│   FastAPI + Uvicorn (localhost:8000)                                  │
│   ┌──────────────────────────────────────────────────┐              │
│   │              ML Pipeline (4-Stage)                │              │
│   │                                                    │              │
│   │   ┌──────────┐   ┌──────────┐   ┌──────────┐    │              │
│   │   │  YOLO    │ → │MediaPipe │ → │ Motion   │    │              │
│   │   │ 인물검출  │   │ Pose 추출│   │ BERT 임베딩│    │              │
│   │   └──────────┘   └──────────┘   └──────────┘    │              │
│   │                                       │           │              │
│   │                                       ▼           │              │
│   │   ┌──────────┐   ┌──────────┐   ┌──────────┐    │              │
│   │   │  Result  │ ← │   LLM    │ ← │   GCN    │    │              │
│   │   │ Formatter│   │ Report   │   │ 유사도추론 │    │              │
│   │   └──────────┘   └──────────┘   └──────────┘    │              │
│   │                                                    │              │
│   └──────────────────────────────────────────────────┘              │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                     External Services                                │
│                                                                      │
│   ┌──────────────────────┐        ┌──────────────────┐              │
│   │      Supabase        │        │    OpenAI API     │              │
│   │  ┌──────┬─────┬────┐│        │  GPT-4o-mini      │              │
│   │  │ Auth │ DB  │Stor││        │  (LangChain 경유)  │              │
│   │  └──────┴─────┴────┘│        └──────────────────┘              │
│   └──────────────────────┘                                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 AI 모델 파이프라인

### 전체 구조

```
영상 입력
  → YOLOv8 (인물 검출)
  → Pose Estimation (2D 포즈 추출, 17관절)
  → H36M 관절 변환
  → MotionBERT (임베딩 생성, [F, 17, 512])
  → LightweightGCN + BodyPartMotionPooling (유사도 계산)
  → 정적 구간 필터링 + Top 25% 선별
  → LangChain + GPT-4o-mini (자연어 보고서)
  → JSON 응답
```

### 핵심 기술

<details>
<summary><b>포즈 추출</b></summary>

- YOLOv8으로 프레임별 인물 바운딩 박스 검출
- MediaPipe PoseLandmarker (tasks API, 0.10.33)로 33관절 좌표 추출
- COCO → H36M 17관절 매핑
- 10fps 프레임 샘플링

</details>

<details>
<summary><b>MotionBERT 임베딩</b></summary>

- DSTformer 아키텍처 (dim_feat=512, depth=5)
- Frozen (학습 없음) — 순수 feature extractor로 사용
- `return_rep=True`로 512차원 임베딩 벡터 출력
- 5초 단위 segment 분할

</details>

<details>
<summary><b>유사도 추론 (GCN)</b></summary>

- LightweightGCN: 512 → 256 → 128 (skip connection)
- BodyPartMotionPooling: 17관절 → 5개 부위 (왼팔, 오른팔, 왼다리, 오른다리, 몸통)
- 시간축 velocity 기반 가중 풀링
- Cross Matching: A×B similarity matrix → 각 A segment의 best match 탐색
- 정적 구간 자동 필터링 (std < threshold)
- 상위 25% 구간 선별 (최소 1개 보장)

</details>

<details>
<summary><b>LLM 보고서 생성</b></summary>

- LangChain + ChatOpenAI (GPT-4o-mini)
- Pydantic 스키마로 구조화된 JSON 출력
- 출력: summary, interpretation, key_differences, segments[].description
- SimilarSegment(id, time_a, time_b, description) 구조

</details>

### AI 모델 성능

| 모델 구성 | Val Correlation |
|:---------|:---------------:|
| MediaPipe + BERT + GCN | 0.8653 |
| Pose-only (ST-GCN) | 0.9272 |
| Pose + HRNet Feature | 0.9570 |
| 3D + Velocity + Bone + Skip (GCN) | 0.9711 |
| **Pose + Tag 멀티모달 (최종)** | **0.9766** |

---

## 🌐 웹 서비스

### 프론트엔드

| 항목 | 내용 |
|------|------|
| **프레임워크** | React 18 + Vite 5 (JSX, TypeScript 미사용) |
| **디자인 시스템** | Glassmorphism (backdrop-filter blur + 반투명 그라디언트) |
| **인증** | Supabase Auth (이메일/비밀번호) |
| **PDF 생성** | @react-pdf/renderer (브라우저 내 생성, 서버 부하 없음) |
| **폰트** | Chakra Petch (제목), Rajdhani (본문), NotoSansKR (PDF) |

#### 페이지 구성

| 페이지 | 파일 | 기능 |
|:------:|------|------|
| 🔐 | `Login.jsx` | 로그인 / 회원가입 |
| 🏠 | `home_page.jsx` | 영상 업로드 + 분석 요청 |
| ⏳ | `loading_page.jsx` | 분석 대기 (단계별 메시지 + 경과시간) |
| 📊 | `result_page.jsx` | 분석 결과 + 아코디언 구간 + PDF 다운로드 |
| 👤 | `profile_page.jsx` | 유저 정보 + 히스토리 + 상세 모달 |
| ℹ️ | `about_us_page.jsx` | 서비스 소개 |

### 백엔드

| 항목 | 내용 |
|------|------|
| **프레임워크** | FastAPI + Uvicorn |
| **ML 런타임** | PyTorch (CPU), YOLO, MediaPipe, MotionBERT, GCN |
| **LLM** | LangChain + GPT-4o-mini |
| **DB/Storage** | Supabase (PostgreSQL + Storage) |

#### API 엔드포인트

```http
POST /api/analyze
Content-Type: application/json

{
  "video_a_id": 1,
  "video_b_id": 2
}
```

```json
// Response
{
  "overall": {
    "score": 68.0,
    "interpretation": "전체 유사도는 중간 이상으로..."
  },
  "summary": "두 영상의 전체 유사도는...",
  "key_differences": [
    "팔 동작 디테일에서 의도적 변형이 관찰됨",
    "후반부로 갈수록 포즈 일치도가 감소"
  ],
  "segments": [
    {
      "id": 1,
      "score": 66.7,
      "video_a": { "start": 15.0, "end": 20.0 },
      "video_b": { "start": 10.0, "end": 15.0 },
      "description": "영상 A의 15~20초와 영상 B의 10~15초는..."
    }
  ]
}
```

### 데이터베이스 구조

```sql
-- 사용자 프로필
profiles (
  id          UUID PRIMARY KEY,    -- auth.users.id FK
  user_name   TEXT
)

-- 분석 결과
analyses (
  aid         BIGINT PRIMARY KEY,  -- auto-increment
  user_id     UUID,                -- auth.users.id FK
  created_at  TIMESTAMP,
  result_data JSONB                -- format_result 출력 전체
)

-- Storage: videos 버킷 (public)
```

---

## 🚀 설치 및 실행

### 사전 요구사항

- **Node.js** 18+ / npm 9+
- **Python** 3.13+
- **Git**

### 1. 저장소 클론

```bash
git clone https://github.com/nomad0884/26_Capstone.git
cd 26_Capstone/Web
```

### 2. 백엔드 설정

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

**환경변수 설정** — `backend/.env` 파일 생성:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
OPENAI_API_KEY=sk-proj-...
```

**모델 가중치 배치:**

| 파일 | 경로 | 용도 |
|------|------|------|
| `yolov8n.pt` | `models/yolo/weights/` | 인물 검출 |
| `pose_landmarker_full.task` | `models/mediapipe/` | 포즈 추출 |
| `mega_latest_epoch.bin` | `models/motion_bert/weights/` | MotionBERT 임베딩 |
| `best_global_model.pth` | `models/gcn_mlp/weights/` | GCN 유사도 모델 |

**서버 실행:**

```bash
uvicorn main:app --reload
# http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

### 3. 프론트엔드 설정

```bash
cd ../kpop-studio

# 의존성 설치
npm install
```

**환경변수 설정** — `kpop-studio/.env` 파일 생성:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

> ⚠️ 프론트엔드에는 반드시 `anon` key만 사용하세요. `service_role` key는 백엔드 전용입니다.

**PDF 한글 폰트 설치:**

[Google Fonts - Noto Sans KR](https://fonts.google.com/noto/specimen/Noto+Sans+KR) 에서 다운로드 후:

```bash
mkdir public/fonts
# NotoSansKR-Regular.ttf, NotoSansKR-Bold.ttf → public/fonts/
```

**개발 서버 실행:**

```bash
npm run dev
# http://localhost:5173
```

### 4. 동시 실행

터미널 2개를 열어서 백엔드와 프론트엔드를 각각 실행합니다.

```
터미널 1 (백엔드):    uvicorn main:app --reload        → :8000
터미널 2 (프론트엔드): npm run dev                      → :5173
```

브라우저에서 `http://localhost:5173` 접속 → 로그인 → 영상 업로드 → 분석 시작

---

## 📚 사용 라이브러리

### AI / 백엔드

| 라이브러리 | 용도 | 라이센스 |
|-----------|------|:-------:|
| PyTorch 2.x | 딥러닝 프레임워크 | BSD-3 |
| FastAPI | REST API 서버 | MIT |
| Ultralytics YOLOv8 | 인물 검출 | AGPL-3.0 |
| MediaPipe 0.10.33 | 2D 포즈 추출 | Apache-2.0 |
| MotionBERT | 모션 임베딩 | MIT |
| LangChain | LLM 오케스트레이션 | MIT |
| OpenCV 4.x | 영상 처리 | Apache-2.0 |
| NumPy | 수치 연산 | BSD-3 |

### 프론트엔드

| 라이브러리 | 용도 | 라이센스 |
|-----------|------|:-------:|
| React 18 | UI 프레임워크 | MIT |
| Vite 5 | 빌드 도구 | MIT |
| @supabase/supabase-js | 인증 / DB / Storage | MIT |
| @react-pdf/renderer | PDF 보고서 생성 | MIT |
| buffer | Buffer 폴리필 | MIT |

### 외부 서비스

| 서비스 | 용도 |
|-------|------|
| Supabase | 인증 · PostgreSQL DB · Storage |
| OpenAI API | GPT-4o-mini 보고서 생성 |

---

## 📖 참고 문헌

1. S. Yan et al., "Spatial Temporal Graph Convolutional Networks for Skeleton-Based Action Recognition," *AAAI*, 2018.
2. W. Zhu et al., "MotionBERT: A Unified Perspective on Learning Human Motion Representations," *ICCV*, 2023.
3. K. Sun et al., "Deep High-Resolution Representation Learning for Human Pose Estimation," *CVPR*, 2019.
4. H. Sakoe and S. Chiba, "Dynamic Programming Algorithm Optimization for Spoken Word Recognition," *IEEE TASSP*, 1978.
5. K. He et al., "Deep Residual Learning for Image Recognition," *CVPR*, 2016.

---

<div align="center">

**Tenein** — K-pop Visual Studio

국민대학교 소프트웨어융합대학 캡스톤디자인 2025

© 2025 Tenein Team

</div>
