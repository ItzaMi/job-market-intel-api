from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from job_market_intel.database import get_session
from job_market_intel.models import IngestionRun, JobSource
from job_market_intel.services import ingestion_runs as ingestion_runs_service

router = APIRouter(prefix="/ingestion-runs", tags=["ingestion-runs"])

@router.post("/", response_model=IngestionRun)
async def create_ingestion_run(
    source: JobSource = JobSource.sample_json,
    session: AsyncSession = Depends(get_session),
) -> IngestionRun:
    return await ingestion_runs_service.create(session, source)

@router.get("/{run_id}/", response_model=IngestionRun)
async def get_ingestion_run(run_id: str, session: AsyncSession = Depends(get_session)) -> IngestionRun:
    try:
        return await ingestion_runs_service.get_by_id(session, run_id)
    except ingestion_runs_service.IngestionRunNotFound:
        raise HTTPException(status_code=404, detail=f"Ingestion run with ID {run_id} not found")
