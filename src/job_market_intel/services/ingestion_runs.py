from datetime import datetime
from job_market_intel.tasks import ingest_jobs_task
from sqlmodel.ext.asyncio.session import AsyncSession

from job_market_intel.models import IngestionRun, JobSource
from job_market_intel.repositories import ingestion_runs as ingest_runs_repo


class IngestionRunNotFound(Exception):
    pass

async def create(session: AsyncSession, source: JobSource) -> IngestionRun:
    now = datetime.now()
    run = IngestionRun(source=source, created_at=now, updated_at=now)

    run = await ingest_runs_repo.create(session, run)

    ingest_jobs_task.delay(str(run.id))

    return run

async def get_by_id(session: AsyncSession, run_id: str) -> IngestionRun:
    run = await ingest_runs_repo.get_by_id(session, run_id)
    if not run:
        raise IngestionRunNotFound()
    return run