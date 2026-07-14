from sqlmodel import Session, select
from job_market_intel.models import Job, JobCreate

def make_fingerprint(source: str, external_id: str | None, source_url: str | None) -> str:
    if external_id:
        return f"{source}:{external_id}"
    if source_url:
        return f"{source}:{source_url}"
    raise ValueError("Posting must have external_id or source_url")

def get_job_by_fingerprint(session: Session, fingerprint: str) -> Job | None:
    return session.exec(select(Job).where(Job.fingerprint == fingerprint)).first()

# Fields that can change when the same posting is re-ingested
MUTABLE_JOB_FIELDS = ("title", "description", "salary", "location", "company", "company_location", "source_url")

def apply_job_fields(target: Job, incoming: JobCreate) -> None:
    data = incoming.model_dump()
    for field in MUTABLE_JOB_FIELDS:
        setattr(target, field, data[field])