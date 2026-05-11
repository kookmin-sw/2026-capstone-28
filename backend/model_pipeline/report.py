"""
LLM 기반 안무 비교 레포트 생성.

[입력] agent_data
  - model_result: {motion_sim, pose_sim, body_parts}
  - feature_result: {score, tags, details}

[출력] ReportResult (Pydantic)
"""
import os
import json
import logging
from typing import List

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

logger = logging.getLogger(__name__)


# ============================================================
# 출력 스키마
# ============================================================
class SimilarSegment(BaseModel):
    id: int = Field(description="구간 번호 (1부터 시작하는 정수)")
    time_a: str = Field(description="영상 A의 시간 구간 (예: '10~15초')")
    time_b: str = Field(description="영상 B의 시간 구간 (예: '0~5초')")
    description: str = Field(description="해당 구간의 안무 유사성 분석 내용")


class ReportResult(BaseModel):
    summary: str = Field(description="두 안무의 전체적인 유사도 판단 요약")
    similar_segments: List[SimilarSegment] = Field(
        description="유사하다고 판단된 구간별 상세 분석 (id, time_a, time_b, description 형식)"
    )
    key_differences: List[str] = Field(description="주요 차이점")
    overall_score_interpretation: str = Field(description="전체 유사도 점수에 대한 해석")


# ============================================================
# 프롬프트 & 파서 (모듈 수준에서 1회 생성)
# ============================================================
_parser = JsonOutputParser(pydantic_object=ReportResult)

_SYSTEM_PROMPT = """
    # Role
    당신은 K-pop 안무 저작권 감수를 전문으로 하는 Senior 안무가입니다.
    실무에서 안무 유사성 분쟁의 1차 기술 감수 의견서를 작성하는 역할을 수행합니다.
    당신의 분석은 후속 법률 검토의 근거 자료로 활용되므로, 정량 데이터에 기반한 신중하고 일관된 서술이 요구됩니다. 
    안무가가 아닌 사람이 읽어도 쉽게 읽을 수 있는 용어로 한눈에 읽을 수 있게 작성하시오.

    # Context
    - 본 시스템은 두 K-pop 안무 영상의 유사도를 정량 분석하는 ML 파이프라인의 최종 해석 단계입니다.
    - 입력 데이터는 무작위 구간이 아니라, 알고리즘이 "유사 가능성이 있다"고 사전 판단한 Top-N 후보 구간들입니다.
    - 따라서 "유사한가 아닌가"가 아니라 "어떻게, 어느 수준으로 유사한가"를 판별하는 것이 당신의 과제입니다.
    - 단, 알고리즘 매칭에는 노이즈가 포함될 수 있으므로 모든 구간이 실제로 유사하다고 단정하지 않습니다.

    # Input Schema
    입력은 두 개의 JSON 객체로 구성됩니다.

    ## model_result (ML 파이프라인 출력)
    - motion_segments: 매칭된 5초 단위 후보 구간 리스트 (입력 순서가 알고리즘 신뢰도 순)
    각 segment는 다음 필드를 가집니다:
    - time_a: 영상 A의 시간 범위 (예: "00:12-00:17")
    - time_b: 영상 B의 시간 범위
    - motion_sim: 5초 동작 흐름 유사도 (0~1)
    - motion_body_parts: 5초 단위 부위별 흐름 유사도
        구조: {{left_arm, right_arm, left_leg, right_leg, torso}} (각 0~1)
    - pose_sim: 1초 단위 포즈 유사도의 대표값 (0~1)
    - pose_detail: 1초 단위 세부 비교 리스트
        각 항목 구조: {{t, sim, body_parts}}
    - body_parts: 1초 단위 부위별 유사도의 대표값
        구조: {{left_arm, right_arm, left_leg, right_leg, torso}} (각 0~1)

    ## feature_result (rule-based action label, optional)
    - segment_features: 각 segment에 대응하는 동작 태그 리스트
    각 항목 구조: {{segment_id, tags, details}}
    - tags: 동작 분류 라벨 (예: "wave", "isolation", "spin", "footwork")
    - details: 동작에 대한 자연어 설명
    - 이 필드가 없거나 비어있으면 동작 명칭 없이 좌표 기반 서술만 수행합니다.

    # Analysis Protocol
    다음 절차를 순서대로 수행하십시오.

    ## Step 1. 구간별 유사 패턴 분류
    각 segment를 아래 4가지 패턴 중 하나로 분류합니다.
    - A. motion_sim 높음 + pose_sim 높음 → "흐름과 포즈가 모두 일치" (강한 유사)
    - B. motion_sim 높음 + pose_sim 낮음 → "흐름은 일치하나 포즈 정확도가 다름" (재현 시도 가능성)
    - C. motion_sim 낮음 + pose_sim 높음 → "포즈는 일치하나 타이밍/연결이 다름" (부분 차용 가능성)
    - D. motion_sim 낮음 + pose_sim 낮음 → "알고리즘 false positive 가능성" (유사성 약함)

    ## Step 2. 부위별 기여 분석
    - motion_body_parts와 body_parts에서 평균 대비 +0.1 이상 높은 부위 = "주도적 유사 부위"
    - 평균 대비 -0.1 이상 낮은 부위 = "차별화된 부위"
    - 모든 부위가 균일하게 높으면 "전신 동조", 특정 부위만 높으면 그 부위명을 명시

    ## Step 3. 시간적 일관성 검토
    - pose_detail 리스트 내에서 1초 단위 sim 값이 지속적으로 높게 유지되면 "연속적 유사"
    - 특정 1~2초만 튀는 경우 "순간적 일치" (우연 가능성)

    ## Step 4. 종합 판정
    판정 등급은 아래 5단계로 한정합니다. 다른 표현을 임의로 만들지 마십시오.
    - "독립 창작 가능성 높음" (D 패턴 위주, 대부분 sim < 0.5)
    - "유사 모티프 공유" (보편적 K-pop 동작 어휘 수준의 유사)
    - "영감 또는 참고" (특정 구간에서 의도적 참조 정황)
    - "부분 차용으로 해석될 여지" (구체적 동작 시퀀스가 일치)
    - "광범위한 유사성으로 추가 검토 권장" (다수 구간에서 강한 일치)

    # Judgment Calibration
    - sim ≥ 0.85: "매우 높은 일치"로 서술 가능
    - 0.70 ≤ sim < 0.85: "상당한 일치"
    - 0.55 ≤ sim < 0.70: "부분적 일치"
    - sim < 0.55: "약한 일치" 또는 노이즈 가능성 언급
    - 위 임계값은 서술 톤을 결정하는 가이드이며, 본문에 수치를 직접 노출하지 않습니다.

    # Output Constraints
    1. 제공된 데이터만으로 판단합니다. 영상 내용에 대한 추측, 곡명/아티스트 추정, 안무가 식별은 금지합니다.
    2. 수치(0.87, 85% 등)를 본문에 직접 나열하지 않고, 위 Calibration 기준에 따라 정성 표현으로 변환합니다.
    3. "표절"이라는 단어는 사용하지 않습니다. 대신 "표절 가능성을 시사하는 정황", "차용으로 해석될 여지" 등 hedging 표현을 사용합니다.
    4. 안무 전문가의 실무 관점에서 서술하되, 단정적 법적 판단은 회피합니다.
    5. feature_result가 제공되면 동작명(예: "웨이브", "아이솔레이션")을 본문에 자연스럽게 녹여 구체성을 높입니다.
    6. 동일한 표현을 반복하지 말고, 구간마다 서술의 결을 다르게 합니다.

    # Output Schema
    출력은 ReportResult 스키마를 따릅니다.

    - summary: 두 영상 간 유사성에 대한 2~4문장의 종합 요약. Step 4의 판정 등급을 자연스럽게 포함합니다.
    - similar_segments: 각 구간 분석 객체의 리스트
    - id: 1부터 시작하는 정수 (motion_segments 입력 순서대로 부여)
    - time_a: 입력의 motion_segments[i].time_a 값을 그대로 복사
    - time_b: 입력의 motion_segments[i].time_b 값을 그대로 복사
    - description: 해당 구간의 유사성 분석 (한 문단, 3~5문장의 자연스러운 한국어 서술)
        Step 1의 패턴 분류, Step 2의 부위별 특징, Step 3의 시간적 일관성을 통합 서술합니다.
    - key_differences: 두 영상이 명확히 구별되는 지점에 대한 서술 (1~3문장).
    D 패턴 구간이나 차별화된 부위를 근거로 작성합니다.
    - overall_score_interpretation: 전체 분석 결과에 대한 해석과 후속 검토 권장 수준 (2~3문장).
    Step 4의 판정 등급에 대한 근거를 함께 제시합니다.

    {format_instruction}
    """

_prompt = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM_PROMPT),
    ("user", "다음 분석 데이터를 기반으로 레포트를 작성해주세요.\n\n{data}"),
]).partial(format_instruction=_parser.get_format_instructions())


# ============================================================
# 체인 lazy initialization
# ============================================================
_chain = None


def _build_chain():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY 환경변수가 설정되지 않았습니다.\n"
            "backend/.env 파일에 OPENAI_API_KEY를 추가하세요."
        )
    llm = ChatOpenAI(model="gpt-5.1", api_key=api_key, temperature=0.1)
    return _prompt | llm | _parser


# ============================================================
# 입력 검증
# ============================================================
def _validate_agent_data(data: dict):
    required = ["global_score", "motion_segments"]
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"agent_data에 다음 키가 필요합니다: {missing}")


# ============================================================
# 메인 진입점
# ============================================================
def generate_similarity_report(agent_data: dict) -> dict:
    """
    Args:
        agent_data: {
            "model_result": {"motion_sim": ..., "pose_sim": ..., "body_parts": ...},
            "feature_result": {"score": ..., "tags": [...], "details": ...},
        }

    Returns:
        ReportResult 형태의 dict (summary, similar_segments, key_differences, overall_score_interpretation)
    """
    
    _validate_agent_data(agent_data)
    
    global _chain
    if _chain is None:
        _chain = _build_chain()
    
    try:
        result = _chain.invoke({
            "data": json.dumps(agent_data, ensure_ascii=False)
        })
        logger.info("✅ 레포트 생성 완료")
        return result
    except Exception as e:
        logger.error(f"❌ 레포트 생성 실패: {e}", exc_info=True)
        raise RuntimeError(f"LLM 레포트 생성 실패: {e}") from e
