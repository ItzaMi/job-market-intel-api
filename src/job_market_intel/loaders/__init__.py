from typing import Callable
from job_market_intel.models import JobCreate, JobSource

from job_market_intel.loaders import sample_json, arbeitnow

LOADERS = {
    "sample_json": sample_json.load,
    "arbeitnow": arbeitnow.load,
}

def get_loader(source: JobSource) -> Callable[[], list[JobCreate]]:
    try:
        return LOADERS[source]
    except KeyError:
        raise ValueError(f"No loader found for source: {source}")