from datetime import datetime
from typing import Annotated
from sqlmodel import Field, SQLModel

from pydantic import BaseModel, Field as PydanticField
from enum import Enum

TextField = Annotated[str, Field(min_length=1, max_length=120)]

class JobBase(SQLModel):
    title: TextField
    description: str | None = Field(default=None, max_length=5000)
    salary: int = Field(gt=0)
    location: TextField
    company: TextField
    company_location: TextField

class Job(JobBase, table=True):
    id: str = Field(primary_key=True)
    created_at: datetime
    updated_at: datetime

class JobCreate(JobBase):
    pass

class JobRead(JobBase):
    id: str
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


class JobFilters(BaseModel):
    title: TextField | None = None
    location: TextField | None = None
    company: TextField | None = None
    salary_range: SalaryRange | None = PydanticField(default=None, description="Filter jobs by salary range")
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)