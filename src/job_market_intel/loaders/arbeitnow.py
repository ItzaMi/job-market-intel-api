import httpx

from job_market_intel.models import JobCreate, JobSource

def fetch_jobs() -> list[dict]:
    response = httpx.get("https://www.arbeitnow.com/api/job-board-api")
    return response.json()['data']

def normalize(raw: dict) -> JobCreate:
    if raw.get("remote"):
        location = "Remote"
    else:
        location = raw['location']
    return JobCreate(
        source=JobSource.arbeitnow,
        source_url=raw['url'],
        external_id=raw['slug'],
        title=raw['title'][:120],
        company=raw['company_name'][:120],
        company_location=raw['location'],
        location=location,
        description=raw['description'][:5000],
    )

def load() -> list[JobCreate]:
    jobs = fetch_jobs()
    return [normalize(job) for job in jobs]