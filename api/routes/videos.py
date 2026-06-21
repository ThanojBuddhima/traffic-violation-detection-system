"""Video upload and status routes."""

import mimetypes
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api.deps import get_db
from api.media import is_allowed_upload
from api.schemas import VideoResponse, VideoUploadResponse
from api.services.job_dispatcher import dispatch_video_job
from api.storage import get_storage
from database.models import Video, VideoStatus

router = APIRouter(prefix="/api/videos", tags=["videos"])


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not is_allowed_upload(file.filename, file.content_type):
        raise HTTPException(
            status_code=400,
            detail="Supported files: videos (.mp4, .avi, .mov, .mkv, .m4v) and images (.jpg, .jpeg, .png, .webp, .bmp, .heic)",
        )

    video_id = str(uuid.uuid4())
    storage = get_storage()
    storage_key = storage.save_upload(video_id, file.file, file.filename)

    video = Video(
        id=video_id,
        filename=file.filename,
        storage_key=storage_key,
        status=VideoStatus.QUEUED.value,
    )
    db.add(video)
    db.commit()

    dispatch_video_job(video_id, storage_key, background_tasks=background_tasks)

    return VideoUploadResponse(video_id=video_id, status=VideoStatus.QUEUED.value)


@router.get("", response_model=list[VideoResponse])
def list_videos(db: Session = Depends(get_db)):
    return db.query(Video).order_by(Video.upload_time.desc()).all()


@router.get("/{video_id}/stream")
def stream_video(video_id: str, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    storage = get_storage()
    try:
        local_path = storage.materialize_for_processing(video.storage_key)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Upload file not found") from None

    path = Path(local_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Upload file not found")

    media_type = mimetypes.guess_type(video.filename)[0] or "application/octet-stream"
    return FileResponse(
        path,
        media_type=media_type,
        filename=video.filename,
    )


@router.get("/{video_id}/status", response_model=VideoResponse)
def get_video_status(video_id: str, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video
