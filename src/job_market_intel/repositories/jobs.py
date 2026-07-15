# how do i read/write Job rows in the database?
import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from job_market_intel.models import Job


async def get_by_id(session: AsyncSession, job_id: uuid.UUID) -> Job | None:
    return await session.get(Job, job_id)


async def list_by_statement(session: AsyncSession, statement) -> list[Job]:
    result = await session.exec(statement)
    return list(result.all())


async def create(session: AsyncSession, job: Job) -> Job:
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def update(session: AsyncSession, job: Job) -> Job:
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def delete(session: AsyncSession, job: Job) -> Job:
    await session.delete(job)
    await session.commit()
    return job
