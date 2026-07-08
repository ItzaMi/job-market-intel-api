# Job Market Intel API

A FastAPI service for managing job listings. Data is persisted in PostgreSQL via SQLModel, with schema changes managed by Alembic.

## Stack

- **FastAPI** — HTTP API
- **SQLModel** — ORM and request/response models
- **PostgreSQL 17** — database (via Docker)
- **Alembic** — migrations
- **uv** — dependency and project management

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- [Docker](https://www.docker.com/) and Docker Compose
- Python 3.13+

## Quick start (Docker)

Start the API and Postgres together:

```bash
docker compose up --build
```

Run in the background:

```bash
docker compose up -d --build
```

Apply database migrations (first run, or after pulling new migrations):

```bash
docker compose run --rm api uv run alembic upgrade head
```

The API is available at `http://127.0.0.1:8000`.

Interactive docs:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

Postgres is exposed on `localhost:5432` with:

| Setting  | Value              |
|----------|--------------------|
| Database | `job_market_intel` |
| User     | `postgres`         |
| Password | `postgres`         |

## Local development (without Docker for the API)

Install dependencies:

```bash
uv sync
```

Start Postgres only:

```bash
docker compose up -d db
```

Set the database URL and run migrations:

```bash
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/job_market_intel
uv run alembic upgrade head
```

Run the API:

```bash
uv run fastapi dev main.py
```

## Docker commands

Stop containers:

```bash
docker compose down
```

Stop and delete DB data:

```bash
docker compose down -v
```

See running containers:

```bash
docker compose ps
```

Follow logs:

```bash
docker compose logs -f
```

Open a Postgres shell:

```bash
docker compose exec db psql -U postgres -d job_market_intel
```

Inside `psql`:

```sql
\dt
SELECT * FROM job;
```

Exit with `\q`.

## Migrations

Create a new migration after changing models in `models.py`:

```bash
uv run alembic revision --autogenerate -m "describe your change"
```

Apply migrations:

```bash
uv run alembic upgrade head
```

Roll back one revision:

```bash
uv run alembic downgrade -1
```

When using Docker, prefix commands with `docker compose run --rm api`.

## Run tests

Tests use an in-memory SQLite database by default, so they run quickly without Docker:

```bash
uv run pytest
```

Verbose output:

```bash
uv run pytest -v
```

To run tests against the Docker Postgres instance (same DB the API uses):

```bash
docker compose run --rm api uv run pytest
```

## API endpoints

| Method   | Path              | Description                          |
|----------|-------------------|--------------------------------------|
| `GET`    | `/health/`        | Health check                         |
| `GET`    | `/jobs/`          | List jobs (supports filters below)   |
| `POST`   | `/jobs/`          | Create a job                         |
| `GET`    | `/jobs/{job_id}/` | Get a job by ID                      |
| `DELETE` | `/jobs/{job_id}/` | Delete a job by ID                   |

### Job fields

| Field              | Type   | Required | Notes                |
|--------------------|--------|----------|----------------------|
| `title`            | string | yes      |                      |
| `description`      | string | no       |                      |
| `salary`           | int    | yes      | Annual salary in USD |
| `location`         | string | yes      |                      |
| `company`          | string | yes      |                      |
| `company_location` | string | yes      |                      |
| `id`               | string | —        | UUID, set by the API |

### List filters (`GET /jobs/`)

All filters are optional and can be combined.

| Query param    | Type   | Description                                      |
|----------------|--------|--------------------------------------------------|
| `title`        | string | Case-insensitive partial match on job title      |
| `company`      | string | Case-insensitive partial match on company name   |
| `location`     | string | Case-insensitive partial match on job location   |
| `salary_range` | enum   | One of: `under_40k`, `40k_60k`, `60k_80k`, `80k_plus` |
| `limit`        | int    | Max results to return (default: `10`)            |
| `offset`       | int    | Number of results to skip (default: `0`)         |

Salary range values:

| Value       | Range              |
|-------------|--------------------|
| `under_40k` | below $40,000      |
| `40k_60k`   | $40,000 – $60,000  |
| `60k_80k`   | $60,000 – $80,000  |
| `80k_plus`  | $80,000 and above  |

## curl examples

### Health check

```bash
curl http://127.0.0.1:8000/health/
```

### List jobs

```bash
curl http://127.0.0.1:8000/jobs/
```

### List jobs with filters

```bash
curl "http://127.0.0.1:8000/jobs/?title=engineer&location=remote&salary_range=80k_plus&limit=5"
```

### Create a job

```bash
curl -X POST http://127.0.0.1:8000/jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Backend Engineer",
    "description": "Build and scale our API platform",
    "salary": 120000,
    "location": "Remote",
    "company": "Acme Corp",
    "company_location": "San Francisco, CA"
  }'
```

`description` is optional. Save the `id` from the response for the next request.

### Get a job by ID

Replace `{job_id}` with the UUID returned from the create response:

```bash
curl http://127.0.0.1:8000/jobs/{job_id}/
```

Example:

```bash
curl http://127.0.0.1:8000/jobs/550e8400-e29b-41d4-a716-446655440000/
```

### Delete a job by ID

```bash
curl -X DELETE http://127.0.0.1:8000/jobs/{job_id}/
```

## Example workflow

```bash
# 1. Start services and migrate
docker compose up -d --build
docker compose run --rm api uv run alembic upgrade head

# 2. Create a job
curl -s -X POST http://127.0.0.1:8000/jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Frontend Developer",
    "salary": 95000,
    "location": "Lisbon",
    "company": "StartupXYZ",
    "company_location": "Lisbon, Portugal"
  }'

# 3. List all jobs
curl http://127.0.0.1:8000/jobs/

# 4. Filter by company and salary band
curl "http://127.0.0.1:8000/jobs/?company=startup&salary_range=80k_plus"

# 5. Get one job (use the id from step 2)
curl http://127.0.0.1:8000/jobs/YOUR_JOB_ID_HERE/
```

## Project layout

```
├── main.py              # FastAPI routes
├── models.py            # SQLModel schemas and filter models
├── database.py          # Engine and session dependency
├── docker-compose.yml   # API + Postgres services
├── DOCKERFILE
├── alembic.ini
├── migrations/          # Alembic migration scripts
└── tests/
    ├── conftest.py      # Test DB setup and fixtures
    └── test_main.py     # API tests
```

## Environment variables

| Variable       | Description                                      | Default (Docker)                                                       |
|----------------|--------------------------------------------------|------------------------------------------------------------------------|
| `DATABASE_URL` | SQLAlchemy connection string                     | `postgresql+psycopg://postgres:postgres@db:5432/job_market_intel`    |
