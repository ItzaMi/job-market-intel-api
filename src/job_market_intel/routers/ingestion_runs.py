from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from job_market_intel.database import get_session
from job_market_intel.models import IngestionRun, JobSource
from job_market_intel.repositories.ingestion_runs import create, get_by_id
from job_market_intel.tasks import ingest_jobs_task

router = APIRouter(prefix="/ingestion-runs", tags=["ingestion-runs"])


@router.post("/", response_model=IngestionRun)
async def create_ingestion_run(
    source: JobSource = JobSource.sample_json,
    session: AsyncSession = Depends(get_session),
) -> IngestionRun:
    now = datetime.now()
    run = IngestionRun(source=source, created_at=now, updated_at=now)

    run = await create(session, run)

    ingest_jobs_task.delay(str(run.id))

    return run


@router.get("/{run_id}/", response_model=IngestionRun)
async def get_ingestion_run(run_id: str, session: AsyncSession = Depends(get_session)) -> IngestionRun:
    run = await get_by_id(session, run_id)

    if run is None:
        raise HTTPException(status_code=404, detail=f"Ingestion run with ID {run_id} not found")

    return run
