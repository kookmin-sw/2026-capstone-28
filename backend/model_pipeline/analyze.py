import time
import logging
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_EXCEPTION

from model_pipeline.object_extractor import extract_objects
from model_pipeline.bert_embedder import embed_motion
from model_pipeline.inferrence import infer_similarity
from model_pipeline.report import generate_similarity_report
from model_pipeline.result_formatter import format_result

logger = logging.getLogger(__name__)


def analyze(video_a_id: int, video_b_id: int):
    from core.model_loader import ModelRegistry
    ModelRegistry.get().load_all()

    total_start = time.time()

    # ================================================================
    # Step 1 — 다운로드 + 키포인트 추출 (두 영상 동시)
    # I/O 바운드(다운로드) + MediaPipe(GIL 해제) → Thread 병렬화 효과 큼
    # ================================================================
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(extract_objects, video_a_id)
        future_b = executor.submit(extract_objects, video_b_id)

        # 둘 중 하나라도 에러나면 즉시 감지
        done, _ = wait([future_a, future_b], return_when=FIRST_EXCEPTION)
        for f in done:
            if f.exception():
                raise f.exception()

        feat_a = future_a.result()
        feat_b = future_b.result()

    logger.info(f"[Step1] 다운로드+추출 완료: {time.time() - t0:.2f}s (병렬)")

    # ================================================================
    # Step 2 — MotionBERT 임베딩 (두 영상 동시)
    # PyTorch CPU 연산은 GIL 해제 구간 있어서 Thread로도 효과 있음
    # ================================================================
    t1 = time.time()
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_emb_a = executor.submit(embed_motion, feat_a["keypoints"])
        future_emb_b = executor.submit(embed_motion, feat_b["keypoints"])

        done, _ = wait([future_emb_a, future_emb_b], return_when=FIRST_EXCEPTION)
        for f in done:
            if f.exception():
                raise f.exception()

        emb_a = future_emb_a.result()
        emb_b = future_emb_b.result()

    logger.info(f"[Step2] MotionBERT 임베딩 완료: {time.time() - t1:.2f}s (병렬)")

    # ================================================================
    # Step 3 — GCN 유사도 추론 (순차 — 두 임베딩을 동시에 입력)
    # ================================================================
    t2 = time.time()
    inference_output = infer_similarity(
        emb_a, emb_b,
        feat_a["keypoints"], feat_b["keypoints"]
    )
    logger.info(f"[Step3] GCN 추론 완료: {time.time() - t2:.2f}s")

    # ================================================================
    # Step 4 — LLM 리포트 생성 (순차 — API 호출)
    # ================================================================
    t3 = time.time()
    agent_report = generate_similarity_report(inference_output)
    logger.info(f"[Step4] 리포트 생성 완료: {time.time() - t3:.2f}s")

    fin_time = time.time()
    logger.info(f"[Total] 전체 소요: {fin_time - total_start:.2f}s")

    raw = {
        "elapsed_time": round(fin_time - total_start, 2),
        "video_a_id": video_a_id,
        "video_b_id": video_b_id,
        "model_output": inference_output,
        "agent_report": agent_report,
    }

    return format_result(raw)