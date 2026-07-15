# someone hit POST /jobs/ - what HTTP response do they get?
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from job_market_intel.services import jobs as jobs_service

from ..database import get_session
from ..models import Job, JobCreate, JobRead, JobFilters, JobUpdate

router = APIRouter()

@router.get("/jobs/", response_model=list[JobRead])
async def list_jobs(filters: JobFilters = Depends(), session: AsyncSession = Depends(get_session)) -> list[Job]:
    return await jobs_service.list(session, filters)


@router.get("/jobs/{job_id}/", response_model=JobRead)
async def get_job(job_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> Job:
    try:
        return await jobs_service.get_by_id(session, job_id)
    except jobs_service.JobNotFound:
        raise HTTPException(status_code=404, detail="Job not found")


@router.post("/jobs/", response_model=JobRead)
async def create_job(job: JobCreate, session: AsyncSession = Depends(get_session)) -> Job:
    try:
        return await jobs_service.create(session, job)
    except jobs_service.JobAlreadyExists:
        raise HTTPException(status_code=400, detail="Job already exists")


@router.delete("/jobs/{job_id}/", response_model=JobRead)
async def delete_job(job_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> Job:
    try:
        return await jobs_service.delete(session, job_id)
    except jobs_service.JobNotFound:
        raise HTTPException(status_code=404, detail="Job not found")


@router.patch("/jobs/{job_id}/", response_model=JobRead)
async def update_job(job_id: uuid.UUID, job: JobUpdate, session: AsyncSession = Depends(get_session)) -> Job:
    try:
        return await jobs_service.update(session, job_id, job)
    except jobs_service.JobNotFound:
        raise HTTPException(status_code=404, detail="Job not found")


