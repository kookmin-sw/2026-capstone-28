from pydantic import BaseModel

class VideoMeta(BaseModel):
    vid: int
    title: str
    size_mb: float
    duration_sec: float
    codec: str

class UploadResponse(BaseModel):
    analysis_id: int
    video_a: VideoMeta
    video_b: VideoMeta
    redirect_url: str
    message: str