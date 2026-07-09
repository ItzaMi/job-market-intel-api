from sqlmodel import Field, SQLModel

from pydantic import BaseModel, Field as PydanticField
from enum import Enum

class JobBase(SQLModel):
    title: str
    description: str | None = None
    salary: int
    location: str
    company: str
    company_location: str

class Job(JobBase, table=True):
    id: str = Field(primary_key=True)

class JobCreate(JobBase):
    pass

class JobRead(JobBase):
    id: str

class JobUpdate(SQLModel):
    title: str | None = None
    description: str | None = None
    salary: int | None = None
    location: str | None = None
    company: str | None = None
    company_location: str | None = None

class SalaryRange(str, Enum):
    under_40k = "under_40k"
    range_40k_60k = "40k_60k"
    range_60k_80k = "60k_80k"
    range_80k_plus = "80k_plus"


class JobFilters(BaseModel):
    title: str | None = None
    location: str | None = None
    company: str | None = None
    salary_range: SalaryRange | None = PydanticField(default=None, description="Filter jobs by salary range")
    limit: int = 10
    offset: int = 0