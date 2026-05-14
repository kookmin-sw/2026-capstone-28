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

## ☁️ AWS 배포 아키텍처
 
```
┌──────────────────────────────────────────────────────────────────────┐
│                           AWS Cloud                                  │
│                                                                      │
│  ┌─────────────────────┐         ┌─────────────────────┐            │
│  │  EC2 — Frontend     │         │  EC2 — Backend       │            │
│  │  ┌───────┐ ┌──────┐ │         │  ┌────────┐ ┌──────┐ │            │
│  │  │ React │ │ Vite │ │  POST   │  │FastAPI │ │Docker│ │            │
│  │  └───────┘ └──────┘ │ ──────→ │  │Python  │ └──────┘ │            │
│  │       Docker         │/analyze │  └────────┘          │            │
│  └──────────┬──────────┘         └──────────┬───────────┘            │
│             │                               │                        │
└─────────────┼───────────────────────────────┼────────────────────────┘
              │ HTTPS                         │
              │                               ├──→ Supabase DB
              │                               ├──→ Supabase Storage
              │                               └──→ OpenAI API (Report)
              │
    ┌─────────┼──────────────────────────────────────┐
    │         ▼                                      │
    │  ┌─────────────┐                               │
    │  │Supabase Auth│  Login / Create Account       │
    │  └─────────────┘                               │
    │                      Supabase                  │
    └────────────────────────────────────────────────┘
 
┌──────────────────────────────────────────────────────────────────────┐
│                         CI/CD Pipeline                               │
│                                                                      │
│  Developer → GitHub → GitHub Actions → Docker Build → ECR Push      │
│                                            │                         │
│                                            └──→ EC2 자동 배포        │
└──────────────────────────────────────────────────────────────────────┘
```
 
### 인프라 구성
 
| 구성 요소 | 서비스 | 역할 |
|:---:|------|------|
| 🖥 | **EC2 (Frontend)** | React + Vite 정적 파일 서빙, Docker 컨테이너 |
| 🧠 | **EC2 (Backend)** | FastAPI + PyTorch ML 파이프라인, Docker 컨테이너 |
| 📦 | **ECR** | Frontend Image, Backend Image 저장소 |
| 🔐 | **Supabase Auth** | 사용자 인증 (이메일/비밀번호, Google OAuth) |
| 🗄 | **Supabase DB** | PostgreSQL — 분석 결과, 사용자 프로필 저장 |
| 📁 | **Supabase Storage** | 업로드 영상 파일 관리 (videos 버킷) |
| 🤖 | **OpenAI API** | GPT-4o-mini 기반 분석 보고서 생성 |
 
### 배포 흐름
 
```
1. 개발자가 main 브랜치에 push
2. GitHub Actions 트리거
3. Docker 이미지 빌드 (Frontend / Backend)
4. ECR에 이미지 Push
5. EC2에서 최신 이미지 Pull + 컨테이너 재시작
```
 
### 통신 구조
 
| 구간 | 프로토콜 | 포트 |
|------|:------:|:----:|
| User ↔ Frontend | HTTPS | 443 |
| Frontend ↔ Backend | HTTP | 8000 |
| Frontend ↔ Supabase Auth | HTTPS | 443 |
| Backend ↔ Supabase DB/Storage | HTTPS | 443 |
| Backend ↔ OpenAI API | HTTPS | 443 |

---
## 📚 사용 라이브러리

### AI / 백엔드

| 라이브러리 | 용도 | 라이센스 |
|-----------|------|:-------:|
| PyTorch 2.x | 딥러닝 프레임워크 | BSD-3 |
| FastAPI | REST API 서버 | MIT |
| Ultralytics YOLOv8 | 인물 검출 | AGPL-3.0 |
| HRNet-W48  | 2D 포즈 추출 | MIT |
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
