import asyncio
from app.core.celery_app import celery_app


@celery_app.task(
    name="app.tasks.etl_tasks.run_incremental_etl",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def run_incremental_etl(self):
    try:
        from app.etl.etl_core import run_incremental_etl as _run
        result = asyncio.run(_run())
        return result
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.tasks.etl_tasks.run_full_etl",
    bind=True,
    max_retries=1,
    time_limit=10800,
)
def run_full_etl(self, years: int = 20):
    try:
        from app.etl.etl_core import run_full_etl as _run
        result = asyncio.run(_run(years=years))
        return result
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.tasks.etl_tasks.process_ondemand_job",
    bind=True,
    max_retries=1,
    default_retry_delay=300,
)
def process_ondemand_job(self, job_id: int):
    try:
        from app.etl.etl_ondemand import process_download_queue_job
        result = asyncio.run(process_download_queue_job(job_id))
        return result
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.tasks.etl_tasks.run_reconcile",
    bind=True,
    max_retries=1,
    time_limit=7200,
)
def run_reconcile(self, years: int = 20):
    try:
        from app.etl.etl_reconcile import run_full_reconcile
        result = asyncio.run(run_full_reconcile(years=years))
        return result
    except Exception as exc:
        raise self.retry(exc=exc)
