from app.core.celery_app import celery_app


@celery_app.task(name="app.tasks.game_tasks.cleanup_expired_sessions", bind=True)
def cleanup_expired_sessions(self):
    # Phase 7 will implement the full cleanup logic here.
    return {"status": "stub", "message": "Game cleanup task registered, implementation in Phase 7"}
