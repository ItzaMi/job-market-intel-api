from sqlmodel import Field, SQLModel

class JobBase(SQLModel):
    title: str
    description: str | None = None
    salary: int
    location: str
    company: str
    company_url: str
    company_logo: str
    company_description: str
    company_location: str

class Job(JobBase, table=True):
    id: str = Field(primary_key=True)

class JobCreate(JobBase):
    pass

class JobRead(JobBase):
    id: str