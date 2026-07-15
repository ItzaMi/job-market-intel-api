# Job Market Intel API

A FastAPI service for collecting, ingesting, and querying job listings. Data is persisted in PostgreSQL via SQLModel, background ingestion runs through Celery + Redis, and schema changes are managed by Alembic.

## Stack

- **FastAPI** — HTTP API
- **SQLModel** — ORM and request/response models
- **PostgreSQL 17** — database (via Docker)
- **Alembic** — migrations
- **Celery** — background job ingestion
- **Redis** — Celery broker and result backend
- **uv** — dependency and project management

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- [Docker](https://www.docker.com/) and Docker Compose
- Python 3.13+

## Quick start (Docker)

Start the API, worker, Redis, and Postgres together:

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

## Architecture

The codebase is split into layers so HTTP, business logic, and data sources stay separate:

```
HTTP request
    ↓
routers/          ← validate input, call services, return responses
    ↓
services/         ← business rules (e.g. deduplication, bulk ingest)
    ↓
loaders/          ← fetch + normalize data from external sources
    ↓
PostgreSQL
```

Background ingestion follows a similar path:

```
POST /ingestion-runs/
    ↓
Celery task (tasks.py)   ← queued in Redis, picked up by worker
    ↓
loader for that source
    ↓
services/ingestion.py    ← upsert jobs by fingerprint
    ↓
PostgreSQL
```

### Job identity & deduplication

Each job comes from a **source** (`sample_json`, `arbeitnow`, …) and is identified by `external_id` or `source_url`. The API builds a **fingerprint** from those fields and stores it as a unique column. Re-ingesting the same posting updates the existing row instead of creating a duplicate.

## Roadmap

Things to tackle later, roughly in priority order. Each item came from code review / production-readiness feedback.

| # | Topic | What it means | Why it matters |
|---|-------|---------------|----------------|
| 1 | **Fix async/sync mismatch** | Routes are `async def` but DB calls are sync — either switch routes to `def` or adopt `AsyncSession` + `asyncpg` | Sync DB inside async routes blocks the event loop under load |
| 2 | **Database indexes** | Add indexes on columns we filter/sort (`salary`, `created_at`, `title`, …) | `ILIKE '%engineer%'` on 100k rows becomes a full table scan without indexes |
| 3 | **Full-text search** | PostgreSQL `tsvector` / `pg_trgm`, or semantic search with embeddings | Better search than partial `ILIKE` matches |
| 4 | **Production Docker** | Multi-stage builds, smaller images, Gunicorn + Uvicorn workers | `fastapi dev` is for development only |
| 5 | **Celery depth** | Multiple queues, retries, Flower dashboard | Visibility and control over background jobs |
| 6 | **Integration tests** | Testcontainers for real Postgres + Redis in CI | SQLite tests miss Postgres-specific behaviour |
| 7 | **Clean Architecture** | Repository + service layers for jobs CRUD (like ingestion already has) | Thinner routers, easier testing, SOLID |
| 8 | **Load balancing** | Multiple API replicas behind a reverse proxy | Horizontal scaling once async + indexes are in place |

### Database indexes — quick primer

Think of a table like a spreadsheet. Without an index, Postgres reads **every row** to find matches (a *sequential scan*). With 20 rows that is instant; with 100,000 rows it is slow.

An **index** is a separate sorted lookup structure — like the index at the back of a book. It lets Postgres jump straight to matching rows.

| Query pattern | Index type | Example |
|---------------|------------|---------|
| Exact match / sort | B-tree (default) | `WHERE salary >= 80000 ORDER BY created_at DESC` |
| Partial text (`%engineer%`) | `pg_trgm` GIN | `WHERE title ILIKE '%engineer%'` |
| Full-text search | `tsvector` GIN | `WHERE search_vector @@ plainto_tsquery('python remote')` |

We already have a unique index on `fingerprint`. Filters on `title`, `company`, `location`, and sorts on `salary` / timestamps do not have indexes yet — that is item **#2** on the roadmap.

## Docker, Postgres & Alembic

This project splits responsibilities across two concerns:

| Layer | Tool | Role |
|-------|------|------|
| **Data** | PostgreSQL (`db` service) | Stores job records permanently |
| **Schema** | Alembic (`migrations/`) | Version-controls and applies table changes |

The API reads/writes data through SQLModel, but it does **not** create or alter tables on startup. Schema changes are applied separately with Alembic.

### How the services connect

- **`api`** — runs FastAPI. Code is bind-mounted from the project folder (`.:/app`), so Python file edits are picked up by the dev server without rebuilding the image.
- **`worker`** — runs a Celery worker that processes ingestion tasks from Redis.
- **`redis`** — message broker and result store for Celery.
- **`db`** — runs Postgres 17. Data lives in the named volume `postgres_data`, so it survives `docker compose down` and container restarts.
- **Alembic** — runs as a one-off command inside the `api` container (or locally with `uv`). It connects to the same Postgres instance and applies SQL from `migrations/versions/`.

Migration files are committed to git. After pulling new migrations from a teammate, run `upgrade head` — you do not rebuild the image for that.

### Database URLs

Both the API and Alembic read `DATABASE_URL` from the environment (`database.py` and `migrations/env.py`). The **host** in the URL depends on where the command runs:

| Where you run the command | Host in URL | Example |
|---------------------------|-------------|---------|
| Inside the `api` container | `db` (Docker service name) | `postgresql+psycopg://postgres:postgres@db:5432/job_market_intel` |
| On host machine (`uv run …`) | `localhost` | `postgresql+psycopg://postgres:postgres@localhost:5432/job_market_intel` |

`docker-compose.yml` sets the in-container URL for the `api` service automatically. Only `export DATABASE_URL=…` is needed when running Alembic or the API locally against the Docker Postgres.

Format breakdown:

```
postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE
                       │        │     │        └── job_market_intel
                       │        │     └── 5432
                       │        └── db (in compose) or localhost (from host)
                       └── postgres:postgres
```

### First-time setup

```bash
# 1. Build and start both services
docker compose up -d --build

# 2. Apply all migrations (creates the job table)
docker compose run --rm api uv run alembic upgrade head

# 3. Verify
curl http://127.0.0.1:8000/health/
docker compose exec db psql -U postgres -d job_market_intel -c "\dt"
```

Step 2 is required on a fresh database. Without it, the API will start but requests that hit the DB will fail because the tables do not exist yet.

### Day-to-day flow (changing the schema)

When editing `models.py`:

```bash
# 1. Generate a migration (review the file before committing)
docker compose run --rm api uv run alembic revision --autogenerate -m "add company size"

# 2. Apply it to your local database
docker compose run --rm api uv run alembic upgrade head

# 3. Restart is usually not needed — the API picks up model changes via the bind mount
#    Test at http://127.0.0.1:8000/docs
```

For generating migrations on the host:

```bash
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/job_market_intel
uv run alembic revision --autogenerate -m "add company size"
uv run alembic upgrade head
```

Commit both `models.py` and the new file under `migrations/versions/`.

### When to rebuild the API image

Because the project directory is bind-mounted into the container, most changes do **not** require a rebuild:

| Change | Rebuild? | What to do |
|--------|----------|------------|
| Python files (`main.py`, `models.py`, …) | No | Save the file; FastAPI dev server reloads |
| New migration in `migrations/versions/` | No | Run `alembic upgrade head` |
| `pyproject.toml` / `uv.lock` (new dependency) | **Yes** | `docker compose up -d --build` |
| `DOCKERFILE` changes | **Yes** | `docker compose up -d --build` |
| `docker-compose.yml` env / ports | No* | `docker compose up -d` (recreates containers) |

\*Rebuild only if you also changed build-related settings; otherwise recreating the container is enough.

### Resetting the database

```bash
# Stop containers and delete all persisted data (fresh empty Postgres)
docker compose down -v

# Start again and re-apply migrations from scratch
docker compose up -d --build
docker compose run --rm api uv run alembic upgrade head
```

### Useful Alembic commands

Run inside Docker (recommended — uses the correct `DATABASE_URL` automatically):

```bash
# Apply all pending migrations
docker compose run --rm api uv run alembic upgrade head

# Roll back the last migration
docker compose run --rm api uv run alembic downgrade -1

# Show current revision
docker compose run --rm api uv run alembic current

# Show migration history
docker compose run --rm api uv run alembic history

# Generate a new migration after editing models.py
docker compose run --rm api uv run alembic revision --autogenerate -m "your message"
```

Same commands work locally if `DATABASE_URL` points at `localhost:5432` (see [Database URLs](#database-urls) above).

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

| Method   | Path                        | Description                              |
|----------|-----------------------------|------------------------------------------|
| `GET`    | `/health/`                  | Health check                             |
| `GET`    | `/jobs/`                    | List jobs (supports filters below)       |
| `POST`   | `/jobs/`                    | Create a job                             |
| `GET`    | `/jobs/{job_id}/`           | Get a job by ID                          |
| `PATCH`  | `/jobs/{job_id}/`           | Update a job (partial)                   |
| `DELETE` | `/jobs/{job_id}/`           | Delete a job by ID                       |
| `POST`   | `/ingestion-runs/`          | Start a background ingestion run         |
| `GET`    | `/ingestion-runs/{run_id}/` | Get ingestion run status and counters    |

### Job fields

| Field              | Type   | Required | Notes                                      |
|--------------------|--------|----------|--------------------------------------------|
| `source`           | enum   | yes      | `sample_json` or `arbeitnow`               |
| `external_id`      | string | no*      | ID from the upstream job board             |
| `source_url`       | string | no*      | Canonical URL of the posting               |
| `title`            | string | yes      |                                            |
| `description`      | string | no       |                                            |
| `salary`           | int    | yes      | Annual salary in USD                       |
| `location`         | string | yes      |                                            |
| `company`          | string | yes      |                                            |
| `company_location` | string | yes      |                                            |
| `id`               | UUID   | —        | Set by the API                             |
| `fingerprint`      | string | —        | Set by the API (`source:external_id`)      |
| `created_at`       | datetime | —      | Set by the API                             |
| `updated_at`       | datetime | —      | Set by the API                             |

\* At least one of `external_id` or `source_url` is required so the API can deduplicate postings.

### List filters (`GET /jobs/`)

All filters are optional and can be combined.

| Query param    | Type   | Description                                      |
|----------------|--------|--------------------------------------------------|
| `title`        | string | Case-insensitive partial match on job title      |
| `company`      | string | Case-insensitive partial match on company name   |
| `location`     | string | Case-insensitive partial match on job location   |
| `salary_range` | enum   | One of: `under_40k`, `40k_60k`, `60k_80k`, `80k_plus` |
| `sort`         | enum   | One of: `created_at_asc`, `created_at_desc`, `updated_at_asc`, `updated_at_desc`, `salary_asc`, `salary_desc` (default: `created_at_desc`) |
| `limit`        | int    | Max results to return (default: `10`, max: `100`)    |
| `offset`       | int    | Number of results to skip (default: `0`)               |

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
    "source": "sample_json",
    "external_id": "acme-senior-backend-001",
    "source_url": "https://jobs.example.com/sample_json/acme-senior-backend-001",
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

### Start an ingestion run

Loads jobs from a data source in the background (requires the `worker` service running):

```bash
# Default source: sample_json (reads data/sample_jobs.json)
curl -X POST http://127.0.0.1:8000/ingestion-runs/

# Pick a source explicitly
curl -X POST "http://127.0.0.1:8000/ingestion-runs/?source=sample_json"
```

Response includes a `run_id`. Poll status with:

```bash
curl http://127.0.0.1:8000/ingestion-runs/{run_id}/
```

An ingestion run tracks: `status` (`pending` → `in_progress` → `completed` / `failed`), `jobs_found`, `jobs_created`, `jobs_updated`, `jobs_failed`, and `error` if something went wrong.

## Example workflow

```bash
# 1. Start services and migrate
docker compose up -d --build
docker compose run --rm api uv run alembic upgrade head

# 2. Create a job
curl -s -X POST http://127.0.0.1:8000/jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "source": "sample_json",
    "external_id": "startup-frontend-001",
    "source_url": "https://jobs.example.com/sample_json/startup-frontend-001",
    "title": "Frontend Developer",
    "salary": 95000,
    "location": "Lisbon",
    "company": "StartupXYZ",
    "company_location": "Lisbon, Portugal"
  }'

# 3. Or ingest many jobs at once from sample_json
curl -s -X POST http://127.0.0.1:8000/ingestion-runs/

# 4. List all jobs
curl http://127.0.0.1:8000/jobs/

# 5. Filter by company and salary band
curl "http://127.0.0.1:8000/jobs/?company=startup&salary_range=80k_plus"

# 6. Get one job (use the id from step 2)
curl http://127.0.0.1:8000/jobs/YOUR_JOB_ID_HERE/
```

## Project layout

```
├── src/job_market_intel/
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # Engine and session dependency
│   ├── models.py            # SQLModel schemas and filter models
│   ├── tasks.py             # Celery tasks (ingestion orchestration)
│   ├── worker.py            # Celery app configuration
│   ├── routers/
│   │   ├── jobs.py          # Jobs CRUD + list filters
│   │   └── ingestion_runs.py
│   ├── services/
│   │   └── ingestion.py     # Bulk upsert logic
│   ├── loaders/
│   │   ├── sample_json.py   # Loads data/sample_jobs.json
│   │   └── arbeitnow.py     # Arbeitnow API loader (stub)
│   └── utils/
│       └── posting.py       # Fingerprint + dedup helpers
├── data/
│   └── sample_jobs.json     # Sample data for ingestion
├── docker-compose.yml       # API + worker + Redis + Postgres
├── Dockerfile
├── alembic.ini
├── migrations/              # Alembic migration scripts
└── tests/
    ├── conftest.py          # Test DB setup and fixtures
    └── test_main.py         # API tests
```

## Environment variables

| Variable                 | Description                         | Set by |
|--------------------------|-------------------------------------|--------|
| `DATABASE_URL`           | SQLAlchemy connection string        | `docker-compose.yml` for `api` and `worker`; export when running `uv` on the host |
| `CELERY_BROKER_URL`      | Redis URL for Celery task queue     | `docker-compose.yml` |
| `CELERY_RESULT_BACKEND`  | Redis URL for Celery task results   | `docker-compose.yml` |

See [Database URLs](#database-urls) for the exact values to use inside Docker vs on your machine.
