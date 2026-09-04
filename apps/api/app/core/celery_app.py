from celery import Celery
from apps.api.app.core.config import settings

celery_app = Celery(
    "opspilot",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_always_eager=settings.CELERY_ALWAYS_EAGER,
    task_eager_propagates=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# Optional task autodiscovery
celery_app.autodiscover_tasks(["apps.api.app.workers"])
