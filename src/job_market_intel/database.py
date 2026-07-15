import os

from sqlmodel import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

DATABASE_URL = os.getenv("DATABASE_URL")

def _to_async_url(url: str) -> str:
    if url.startswith("postgresql+psycopg"):
        return url.replace("postgresql+psycopg", "postgresql+asyncpg", 1)
    if url.startswith("sqlite://") and "+aiosqlite" not in url:
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url

engine = create_engine(DATABASE_URL, echo=True)
async_engine = create_async_engine(_to_async_url(DATABASE_URL), echo=True)

async def get_session():
    async with AsyncSession(async_engine) as session:
        yield session