import uuid
from datetime import datetime

from sqlmodel import Session

from job_market_intel.database import engine
from job_market_intel.models import IngestionRun, IngestionStatus
from job_market_intel.worker import celery_app

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
            run.jobs_found = 0
            run.jobs_created = 0
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