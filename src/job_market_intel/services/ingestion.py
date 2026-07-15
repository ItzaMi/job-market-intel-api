from datetime import datetime
import logging
from sqlmodel import Session

from job_market_intel.utils.posting import apply_job_fields, get_job_by_fingerprint, make_fingerprint
from job_market_intel.models import Job, JobCreate

logger = logging.getLogger(__name__)

def ingest_jobs(session: Session, jobs: list[JobCreate]) -> tuple[int, int, int]:
    created = 0
    updated = 0
    failed = 0
    now = datetime.now()

    for job in jobs:
        try:
            fingerprint = make_fingerprint(job.source, job.external_id, job.source_url)
            existing = get_job_by_fingerprint(session, fingerprint)

            if existing:
                apply_job_fields(existing, job)
                existing.updated_at = now
                session.add(existing)
                updated += 1
            else:
                db_job = Job(**job.model_dump(), created_at=now, updated_at=now, fingerprint=fingerprint)
                session.add(db_job)
                created += 1

        except Exception:
            failed += 1
            logger.error(f"Error ingesting job: {job}")

    session.commit()
    return created, updated, failed