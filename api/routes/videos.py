"""Video upload and status routes."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from api.deps import get_db
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
    if not file.filename or not file.filename.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
        raise HTTPException(status_code=400, detail="Only video files (.mp4, .avi, .mov, .mkv) are supported")

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


@router.get("/{video_id}/status", response_model=VideoResponse)
def get_video_status(video_id: str, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video
