from datetime import datetime
from typing import Annotated
import uuid
from enum import Enum

from pydantic import BaseModel, Field as PydanticField
from sqlalchemy import Column, Enum as SAEnum
from sqlmodel import Field, SQLModel

TextField = Annotated[str, Field(min_length=1, max_length=120)]
FilterText = Annotated[str, Field(min_length=1, max_length=120)]

def _str_enum(enum_cls: type[Enum]) -> SAEnum:
    """Store Python enums as plain VARCHAR — matches our Alembic migrations."""
    return SAEnum(
        enum_cls,
        values_callable=lambda members: [member.value for member in members],
        native_enum=False,
    )

class JobSource(str, Enum):
    sample_json = "sample_json"
    arbeitnow = "arbeitnow"

class JobPostingIdentity(SQLModel):
    source: JobSource
    external_id: str | None
    source_url: str | None

class JobBase(SQLModel):
    title: TextField
    description: str | None = Field(default=None, max_length=5000)
    location: TextField
    company: TextField
    company_location: TextField

class Job(JobBase, JobPostingIdentity, table=True):
    # Override: DB column is VARCHAR, not a Postgres ENUM type named "jobsource"
    source: JobSource = Field(sa_column=Column(_str_enum(JobSource), nullable=False))
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime
    updated_at: datetime
    fingerprint: str = Field(unique=True, index=True, max_length=255)

class JobCreate(JobBase, JobPostingIdentity):
    pass

class JobRead(JobBase, JobPostingIdentity):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    fingerprint: str

class JobUpdate(SQLModel):
    title: TextField | None = None
    description: str | None = Field(default=None, max_length=5000)
    location: TextField | None = None
    company: TextField | None = None
    company_location: TextField | None = None

class SortBy(str, Enum):
    created_at_asc = "created_at_asc"
    created_at_desc = "created_at_desc"
    updated_at_asc = "updated_at_asc"
    updated_at_desc = "updated_at_desc"

class JobFilters(BaseModel):
    title: FilterText | None = None
    location: FilterText | None = None
    company: FilterText | None = None
    limit: int = PydanticField(default=10, ge=1, le=100)
    offset: int = PydanticField(default=0, ge=0)
    sort: SortBy = PydanticField(default=SortBy.created_at_desc)

class IngestionStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"

class IngestionRun(SQLModel, table=True):
    __tablename__ = "ingestion_run"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    source: JobSource = Field(sa_column=Column(_str_enum(JobSource), nullable=False))
    status: IngestionStatus = Field(
        default=IngestionStatus.pending,
        sa_column=Column(_str_enum(IngestionStatus), nullable=False),
    )
    jobs_found: int = 0
    jobs_created: int = 0
    jobs_updated: int = 0
    jobs_failed: int = 0
    error: str | None = None
    created_at: datetime
    updated_at: datetime
