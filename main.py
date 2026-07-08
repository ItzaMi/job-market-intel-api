from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uuid import uuid4

app = FastAPI()

class JobCreate(BaseModel):
    title: str
    description: str | None = None
    salary: int
    location: str
    company: str
    company_url: str
    company_logo: str
    company_description: str
    company_location: str

class JobRead(JobCreate):
    id: str

jobs: list[JobRead] = []

@app.get("/health/")
async def health():
    return {"status": "ok"}

@app.get("/jobs/", response_model=list[JobRead])
async def list_jobs() -> list[JobRead]:
    return jobs

@app.get("/jobs/{job_id}/", response_model=JobRead)
async def get_job(job_id: str) -> JobRead:
    for job in jobs:
        if job.id == job_id:
            return job
    raise HTTPException(status_code=404, detail="Job not found")

@app.post("/jobs/", response_model=JobRead)
async def create_job(job: JobCreate) -> JobRead:
    new_job = JobRead(id=str(uuid4()), **job.model_dump())
    jobs.append(new_job)
    return new_job

@app.delete("/jobs/{job_id}/", response_model=JobRead)
async def delete_job(job_id: str) -> JobRead:
    for job in jobs:
        if job.id == job_id:
            jobs.remove(job)
            return job
    raise HTTPException(status_code=404, detail="Job not found")