from datetime import datetime
from typing import Annotated
import uuid
from sqlmodel import Field, SQLModel

from pydantic import BaseModel, Field as PydanticField
from enum import Enum

TextField = Annotated[str, Field(min_length=1, max_length=120)]
FilterText = Annotated[str, Field(min_length=1, max_length=120)]

class JobBase(SQLModel):
    title: TextField
    description: str | None = Field(default=None, max_length=5000)
    salary: int = Field(gt=0)
    location: TextField
    company: TextField
    company_location: TextField

class Job(JobBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime
    updated_at: datetime

class JobCreate(JobBase):
    pass

class JobRead(JobBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

class JobUpdate(SQLModel):
    title: TextField | None = None
    description: str | None = Field(default=None, max_length=5000)
    salary: int | None = Field(default=None, gt=0)
    location: TextField | None = None
    company: TextField | None = None
    company_location: TextField | None = None

class SalaryRange(str, Enum):
    under_40k = "under_40k"
    range_40k_60k = "40k_60k"
    range_60k_80k = "60k_80k"
    range_80k_plus = "80k_plus"

class SortBy(str, Enum):
    created_at_asc = "created_at_asc"
    created_at_desc = "created_at_desc"
    updated_at_asc = "updated_at_asc"
    updated_at_desc = "updated_at_desc"
    salary_asc = "salary_asc"
    salary_desc = "salary_desc"

class JobFilters(BaseModel):
    title: FilterText | None = None
    location: FilterText | None = None
    company: FilterText | None = None
    salary_range: SalaryRange | None = PydanticField(default=None, description="Filter jobs by salary range")
    limit: int = PydanticField(default=10, ge=1, le=100)
    offset: int = PydanticField(default=0, ge=0)
    sort: SortBy = PydanticField(default=SortBy.created_at_desc)