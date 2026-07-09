import os

# Set before test modules import the app (DATABASE_URL is required at import time).
os.environ.setdefault("DATABASE_URL", "sqlite://")

from sqlalchemy.pool import StaticPool
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

from job_market_intel import database
from job_market_intel.database import get_session
from job_market_intel.main import app
from job_market_intel.models import Job

IS_SQLITE = os.environ["DATABASE_URL"].startswith("sqlite")


def _make_engine(url: str):
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
    return create_engine(url, echo=False)


database.engine = _make_engine(os.environ["DATABASE_URL"])


@pytest.fixture(autouse=True)
def reset_db():
    SQLModel.metadata.create_all(database.engine)
    yield
    if IS_SQLITE:
        SQLModel.metadata.drop_all(database.engine)
    else:
        with Session(database.engine) as session:
            for job in session.exec(select(Job)).all():
                session.delete(job)
            session.commit()


@pytest.fixture
def session():
    with Session(database.engine) as session:
        yield session


@pytest.fixture
def client(session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
