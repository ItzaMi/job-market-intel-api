from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends,FastAPI, HTTPException
from sqlmodel import Session, select

from database import create_db_and_tables, get_session
from models import Job, JobCreate, JobRead

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/health/")
async def health():
    return {"status": "ok"}

@app.get("/jobs/", response_model=list[JobRead])
async def list_jobs(session: Session = Depends(get_session)) -> list[Job]:
    statement = select(Job)
    jobs = session.exec(statement).all()
    return jobs

@app.get("/jobs/{job_id}/", response_model=JobRead)
async def get_job(job_id: str, session: Session = Depends(get_session)) -> Job:
    job = session.get(Job, job_id)
    
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return job

@app.post("/jobs/", response_model=JobRead)
async def create_job(job: JobCreate, session: Session = Depends(get_session)) -> Job:
    new_job = Job(id=str(uuid4()), **job.model_dump())

    session.add(new_job)
    session.commit()
    session.refresh(new_job)

    return new_job

@app.delete("/jobs/{job_id}/", response_model=JobRead)
async def delete_job(job_id: str, session: Session = Depends(get_session)) -> Job:
    job = session.get(Job, job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    session.delete(job)
    session.commit()

    return job