"""Celery app initialization with Redis broker."""

from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "codelens",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=600,   # 10 min soft limit
    task_time_limit=900,        # 15 min hard limit
)

# Auto-discover tasks in app.tasks package
celery_app.autodiscover_tasks(["app.tasks"])

# Explicitly import tasks to ensure they are registered
from app.tasks import repo_tasks, embedding_tasks  # noqa: E402, F401
