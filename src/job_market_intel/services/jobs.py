# what are the rules for creating a new Job row?
import uuid
from job_market_intel.utils.posting import get_job_by_fingerprint_async, make_fingerprint
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime

from job_market_intel.repositories import jobs as jobs_repo
from job_market_intel.models import Job, JobCreate, JobFilters, JobUpdate, SortBy

class JobAlreadyExists(Exception):
    pass

class JobNotFound(Exception):
    pass

SORT_ORDERS = {
    SortBy.created_at_asc: Job.created_at.asc(),
    SortBy.created_at_desc: Job.created_at.desc(),
    SortBy.updated_at_asc: Job.updated_at.asc(),
    SortBy.updated_at_desc: Job.updated_at.desc(),
}

async def list(session: AsyncSession, filters: JobFilters) -> list[Job]:
    statement = select(Job)

    if filters.title:
        statement = statement.where(Job.title.ilike(f"%{filters.title}%"))

    if filters.company:
        statement = statement.where(Job.company.ilike(f"%{filters.company}%"))

    if filters.location:
        statement = statement.where(Job.location.ilike(f"%{filters.location}%"))

    if filters.sort:
        statement = statement.order_by(SORT_ORDERS[filters.sort])

    statement = statement.offset(filters.offset).limit(filters.limit)

    return await jobs_repo.list_by_statement(session, statement)

async def get_by_id(session: AsyncSession, job_id: uuid.UUID) -> Job:
    job = await jobs_repo.get_by_id(session, job_id)
    if not job:
        raise JobNotFound()
    return job

async def create(session: AsyncSession, job: JobCreate) -> Job:
    now = datetime.now()
    fingerprint = make_fingerprint(job.source, job.external_id, job.source_url)

    existing = await get_job_by_fingerprint_async(session, fingerprint)
    if existing:
        raise JobAlreadyExists()

    new_job = Job(**job.model_dump(), created_at=now, updated_at=now, fingerprint=fingerprint)
    return await jobs_repo.create(session, new_job)

async def delete(session: AsyncSession, job_id: uuid.UUID) -> Job:
    job = await get_by_id(session, job_id)

    return await jobs_repo.delete(session, job)

async def update(session: AsyncSession, job_id: uuid.UUID, job: JobUpdate) -> Job:
    job = await get_by_id(session, job_id)

    for field, value in job.model_dump(exclude_unset=True).items():
        setattr(job, field, value)

    job.updated_at = datetime.now()

    return await jobs_repo.update(session, job)
