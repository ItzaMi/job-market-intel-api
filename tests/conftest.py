import os

# Set before test modules import the app (required at import time).
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from job_market_intel import database
from job_market_intel.database import get_session
from job_market_intel.main import app

ASYNC_TEST_URL = "sqlite+aiosqlite://"


def _make_sync_engine(url: str):
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
    return create_engine(url, echo=False)


def _make_async_engine():
    return create_async_engine(
        ASYNC_TEST_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )


database.engine = _make_sync_engine(os.environ["DATABASE_URL"])
database.async_engine = _make_async_engine()


@pytest.fixture(autouse=True)
async def reset_db():
    async with database.async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    yield


@pytest.fixture
async def session():
    async with AsyncSession(database.async_engine) as session:
        yield session


@pytest.fixture
def client(session):
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
