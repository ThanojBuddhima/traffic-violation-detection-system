"""Job dispatch — BackgroundTasks (V1) or Celery (V2)."""

from fastapi import BackgroundTasks

from api.config import settings
from api.services.video_processor import process_video_job


def dispatch_video_job(
    video_id: str,
    storage_key: str,
    background_tasks: BackgroundTasks | None = None,
) -> None:
    if settings.USE_CELERY:
        from api.tasks.celery_app import process_video_task

        process_video_task.delay(video_id, storage_key)
    else:
        if background_tasks is None:
            raise ValueError("background_tasks required when USE_CELERY=false")
        background_tasks.add_task(process_video_job, video_id, storage_key)
