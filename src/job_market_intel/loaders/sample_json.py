import json
from pathlib import Path
from job_market_intel.models import JobCreate

SAMPLE_JOBS_PATH = Path(__file__).resolve().parents[3] / "data" / "sample_jobs.json"

def load() -> list[JobCreate]:
    with SAMPLE_JOBS_PATH.open() as json_data:
        return [JobCreate.model_validate(job) for job in json.load(json_data)]