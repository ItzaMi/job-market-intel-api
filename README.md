# Job Market Intel API

FastAPI API for ingesting and querying job listings. Postgres + SQLModel, background ingestion via Celery + Redis, migrations via Alembic.

**Stack:** FastAPI (async) · SQLModel · PostgreSQL 17 · asyncpg / psycopg · Celery · Redis · uv

## Run

```bash
docker compose up -d --build
docker compose run --rm api uv run alembic upgrade head
```

- API: http://127.0.0.1:8000  
- Docs: http://127.0.0.1:8000/docs  
- Postgres: `localhost:5432` / `job_market_intel` / `postgres` / `postgres`

```bash
uv run pytest                  # tests (async SQLite)
docker compose logs -f         # follow logs
docker compose down -v         # wipe DB volume and stop
```

## Architecture

```
routers/  →  services/  →  repositories/  →  Postgres (asyncpg)
                              ↑
Celery worker → services/ingestion.py (sync psycopg)
```

- **Routers** — HTTP and status codes  
- **Services** — business rules (fingerprints, filters, domain errors)  
- **Repositories** — DB access  

Jobs are deduped by a **fingerprint** (`source.value` + `external_id` or `source_url`). API DB access is async; the Celery worker stays sync.

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health/` | Health check |
| `GET` | `/jobs/` | List / filter / sort / paginate |
| `POST` | `/jobs/` | Create |
| `GET` | `/jobs/{id}/` | Get one |
| `PATCH` | `/jobs/{id}/` | Update |
| `DELETE` | `/jobs/{id}/` | Delete |
| `POST` | `/ingestion-runs/` | Start background ingest (`?source=sample_json`) |
| `GET` | `/ingestion-runs/{id}/` | Ingest run status |

Details and schemas: **[/docs](http://127.0.0.1:8000/docs)**.

```bash
# Ingest sample jobs
curl -X POST "http://127.0.0.1:8000/ingestion-runs/?source=sample_json"

# List
curl "http://127.0.0.1:8000/jobs/?title=engineer&limit=5"
```

## Migrations

```bash
# Apply
docker compose run --rm api uv run alembic upgrade head

# After model changes — review the generated file before applying
docker compose run --rm api uv run alembic revision --autogenerate -m "your message"
docker compose run --rm api uv run alembic upgrade head
```

Autogenerate often includes extra diffs — keep only what you intend.

## Layout

```
src/job_market_intel/
  routers/          # HTTP
  services/         # jobs, ingestion_runs, ingestion (Celery)
  repositories/     # DB
  loaders/          # sample_json, arbeitnow (stub)
  database.py       # sync + async engines
  models.py
  tasks.py / worker.py
data/sample_jobs.json
migrations/
tests/
```

## Env (Compose sets these for containers)

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | `postgresql+psycopg://…` (API converts to asyncpg) |
| `CELERY_BROKER_URL` | Redis broker |
| `CELERY_RESULT_BACKEND` | Redis results |

On the host (API/Alembic against Docker Postgres): use `@localhost:5432` instead of `@db:5432`.

## To-do

- Arbeitnow loader
- better search (`pg_trgm` / full-text).  

## To study

- Ops:
  - production Docker
  - Flower
  - Testcontainers
  - load balancing
