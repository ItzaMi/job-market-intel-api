import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from job_market_intel.models import IngestionRun


async def get_by_id(session: AsyncSession, run_id: str | uuid.UUID) -> IngestionRun | None:
    return await session.get(IngestionRun, run_id)


async def create(session: AsyncSession, run: IngestionRun) -> IngestionRun:
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run
