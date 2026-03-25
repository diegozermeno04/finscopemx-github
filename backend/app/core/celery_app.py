import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "finscopemx",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.tasks.etl_tasks",
        "app.tasks.game_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Mexico_City",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.tasks.etl_tasks.*": {"queue": "etl"},
        "app.tasks.game_tasks.*": {"queue": "game"},
    },
    beat_schedule={
        "nightly-incremental-etl": {
            "task": "app.tasks.etl_tasks.run_incremental_etl",
            "schedule": crontab(hour=2, minute=0),
            "options": {"queue": "etl"},
        },
        "cleanup-expired-game-sessions": {
            "task": "app.tasks.game_tasks.cleanup_expired_sessions",
            "schedule": crontab(minute="*/15"),
            "options": {"queue": "game"},
        },
    },
)
