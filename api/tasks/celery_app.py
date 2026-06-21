"""Celery app and tasks (V2)."""

from celery import Celery

from api.config import settings

celery_app = Celery("helmet_violations", broker=settings.CELERY_BROKER_URL)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]


@celery_app.task(bind=True, max_retries=3)
def process_video_task(self, video_id: str, storage_key: str):
    from api.services.video_processor import process_video_job

    try:
        process_video_job(video_id, storage_key)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60) from exc
