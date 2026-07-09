from uuid import uuid4

from fastapi import Depends,FastAPI, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import Job, JobCreate, JobRead, JobFilters, SalaryRange, JobUpdate


app = FastAPI()

SALARY_RANGES = {
    SalaryRange.under_40k: (None, 39999),
    SalaryRange.range_40k_60k: (40000, 60000),
    SalaryRange.range_60k_80k: (60000, 80000),
    SalaryRange.range_80k_plus: (80000, None),
}

@app.get("/health/")
async def health():
    return {"status": "ok"}

@app.get("/jobs/", response_model=list[JobRead])
async def list_jobs(filters: JobFilters = Depends(), session: Session = Depends(get_session)) -> list[Job]:
    statement = select(Job)

    if filters.title:
        statement = statement.where(Job.title.ilike(f"%{filters.title}%"))

    if filters.company:
        statement = statement.where(Job.company.ilike(f"%{filters.company}%"))

    if filters.location:
        statement = statement.where(Job.location.ilike(f"%{filters.location}%"))

    if filters.salary_range:
        min_salary, max_salary = SALARY_RANGES[filters.salary_range]

        if min_salary is not None:
            statement = statement.where(Job.salary >= min_salary)
        if max_salary is not None:
            statement = statement.where(Job.salary <= max_salary)

    statement = statement.offset(filters.offset).limit(filters.limit)

    return list(session.exec(statement).all())

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

@app.patch("/jobs/{job_id}/", response_model=JobRead)
async def update_job(job_id: str, job: JobUpdate, session: Session = Depends(get_session)) -> Job:
    db_job = session.get(Job, job_id)

    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    for field, value in job.model_dump(exclude_unset=True).items():
        setattr(db_job, field, value)

    session.add(db_job)
    session.commit()
    session.refresh(db_job)

    return db_job