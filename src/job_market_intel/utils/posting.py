from sqlmodel import Session, select
from sqlmodel.ext.asyncio.session import AsyncSession

from job_market_intel.models import Job, JobCreate, JobSource

def make_fingerprint(source: JobSource, external_id: str | None, source_url: str | None) -> str:
    # Use .value — f"{source}" formats as "JobSource.sample_json", not "sample_json"
    if external_id:
        return f"{source.value}:{external_id}"
    if source_url:
        return f"{source.value}:{source_url}"
    raise ValueError("Posting must have external_id or source_url")

def get_job_by_fingerprint(session: Session, fingerprint: str) -> Job | None:
    return session.exec(select(Job).where(Job.fingerprint == fingerprint)).first()


async def get_job_by_fingerprint_async(session: AsyncSession, fingerprint: str) -> Job | None:
    result = await session.exec(select(Job).where(Job.fingerprint == fingerprint))
    return result.first()

# Fields that can change when the same posting is re-ingested
MUTABLE_JOB_FIELDS = ("title", "description", "location", "company", "company_location", "source_url")

def apply_job_fields(target: Job, incoming: JobCreate) -> None:
    data = incoming.model_dump()
    for field in MUTABLE_JOB_FIELDS:
        setattr(target, field, data[field])