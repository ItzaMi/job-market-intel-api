import json
from pathlib import Path
import uuid
from datetime import datetime

from sqlmodel import Session

from job_market_intel.database import engine
from job_market_intel.models import IngestionRun, IngestionStatus, Job, JobCreate
from job_market_intel.worker import celery_app

SAMPLE_JOBS_PATH = Path(__file__).resolve().parents[2] / "data" / "sample_jobs.json"

def load_sample_jobs() -> list[JobCreate]:
    with SAMPLE_JOBS_PATH.open() as json_data:
        return [JobCreate.model_validate(job) for job in json.load(json_data)]

def ingest_jobs(session: Session, jobs: list[JobCreate]) -> int:
    now = datetime.now()
    for job in jobs:
        db_job = Job(**job.model_dump(), created_at=now, updated_at=now)
        session.add(db_job)
    session.commit()
    return len(jobs)

@celery_app.task(name="ingest_jobs")
def ingest_jobs_task(ingestion_run_id: str | uuid.UUID) -> None:
    run_id = ingestion_run_id if isinstance(ingestion_run_id, uuid.UUID) else uuid.UUID(ingestion_run_id)

    with Session(engine) as session:
        run = session.get(IngestionRun, run_id)
        if run is None:
            raise ValueError(f"Ingestion run with ID {run_id} not found")
        
        run.status = IngestionStatus.in_progress
        run.updated_at = datetime.now()
        session.add(run)
        session.commit()

        try:
            jobs = load_sample_jobs()
            created_count = ingest_jobs(session, jobs)
            run.jobs_found = len(jobs)
            run.jobs_created = created_count
            run.status = IngestionStatus.completed
            run.updated_at = datetime.now()
            session.add(run)
            session.commit()

        except Exception as e:
            run.status = IngestionStatus.failed
            run.error = str(e)
            run.updated_at = datetime.now()
            session.add(run)
            session.commit()
            raise