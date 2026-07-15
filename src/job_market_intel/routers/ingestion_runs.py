from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from job_market_intel.database import get_session
from job_market_intel.models import IngestionRun, JobSource
from job_market_intel.tasks import ingest_jobs_task

router = APIRouter(prefix="/ingestion-runs", tags=["ingestion-runs"])

@router.post("/", response_model=IngestionRun)
async def create_ingestion_run(source: JobSource = JobSource.sample_json, session: Session = Depends(get_session)) -> IngestionRun:
    now = datetime.now()
    run = IngestionRun(source=source, created_at=now, updated_at=now)

    session.add(run)
    session.commit()
    session.refresh(run)

    ingest_jobs_task.delay(str(run.id))

    return run

@router.get("/{run_id}/", response_model=IngestionRun)
async def get_ingestion_run(run_id: str, session: Session = Depends(get_session)) -> IngestionRun:
    run = session.get(IngestionRun, run_id)

    if run is None:
        raise HTTPException(status_code=404, detail=f"Ingestion run with ID {run_id} not found")

    return run