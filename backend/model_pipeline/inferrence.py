import os

from model_pipeline.stgcn_pose_encoder import extract_pair_pose_embeddings
from model_pipeline.tag_extractor import generate_pair_tags
from model_pipeline.pose_tag import run_pose_tag_similarity


POSE_TAG_CKPT_PATH = os.getenv(
    "POSE_TAG_CKPT_PATH",
    "model_pipeline/checkpoint/best_pose_tag_corr.pth",
)


def infer_similarity(
    emb_a,
    emb_b,
    keypoints_a,
    keypoints_b,
    fps_a=30.0,
    fps_b=30.0,
):
    """
    최종 Pose+Tag 유사도 추론.

    Args:
        emb_a: MotionBERT embedding A [F, 17, 512]
        emb_b: MotionBERT embedding B [F, 17, 512]
        keypoints_a: HRNet 2D keypoints A [F, 17, 3]
        keypoints_b: HRNet 2D keypoints B [F, 17, 3]
        fps_a: video A fps
        fps_b: video B fps

    Returns:
        dict
    """

    # 1. MotionBERT embedding → ST-GCN pose embedding
    pose_result = extract_pair_pose_embeddings(
        emb_a,
        emb_b,
        checkpoint_path=POSE_TAG_CKPT_PATH,
    )

    pose_embedding_a = pose_result["pose_embedding_a"]   #  ✅ 여기서 모델 임베딩 결과 나오고, 이걸로 5초 단위 문맥 파악하면 됨. 
    pose_embedding_b = pose_result["pose_embedding_b"]

    # 2. HRNet keypoints → feature → pair-level tag
    tag_result = generate_pair_tags(
        keypoints_a,
        keypoints_b,
        fps_a=fps_a,
        fps_b=fps_b,
    )

    tag_vector = tag_result["tag_vector"]


    # ✅ 2-1. Motion Sim 결과물 안에서 HRnet (keypoints) 파라미터로 1초 단위 시퀀스 비교 진행하면 됨.

    # 3. pose embedding + tag vector → final similarity  ✅ 여기는 최종 점수 Global Sim 만들어내는 것.
    final_result = run_pose_tag_similarity(
        pose_embedding_a,
        pose_embedding_b,
        tag_vector,
        checkpoint_path=POSE_TAG_CKPT_PATH,
    )



    # 여기가 수정되어야함. 
    '''
        similarity_score : final_result['similarity_score']
        video_a : "video_a 제목"
        video_b : "video_b 제목"
        motion_segment : { time : { 시작, 끝} ,
                           motion_sim : 5초 구간에서 motion sim,
                           motion_body_part_sim : 5초 구간에서 신체부위별 sim,
                           pose_sim : { 1초 단위 pose 유사도 내용들 }
                        }
    '''
    return {
        "similarity_score": final_result["similarity_score"],
        "pose_embedding_a": pose_embedding_a.tolist(),
        "pose_embedding_b": pose_embedding_b.tolist(),
        "tag_vector": tag_vector.tolist(),
        "tag_names": tag_result["tag_names"],
        "tag_support_score": tag_result["support_score"],
        "window_results": tag_result["window_results"],
        "model_type": "pose_tag_stgcn",
    }