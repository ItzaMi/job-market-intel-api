# Job Market Intel API

A small FastAPI service for managing job listings. Data is stored in memory (resets when the server restarts).

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- Python 3.13+

## Setup

```bash
uv sync
```

## Run the server

```bash
uv run fastapi dev main.py
```

The API will be available at `http://127.0.0.1:8000`.

Interactive docs:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Run tests

```bash
uv run pytest
```

Verbose output:

```bash
uv run pytest -v
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health/` | Health check |
| `GET` | `/jobs/` | List all jobs |
| `POST` | `/jobs/` | Create a job |
| `GET` | `/jobs/{job_id}/` | Get a job by ID |
| `DELETE` | `/jobs/{job_id}/` | Delete a job by ID |

## curl examples

### Health check

```bash
curl http://127.0.0.1:8000/health/
```

### List jobs

```bash
curl http://127.0.0.1:8000/jobs/
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
    "company_url": "https://acme.com",
    "company_logo": "https://acme.com/logo.png",
    "company_description": "We build developer tools",
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

Replace `{job_id}` with the UUID returned from the create response:

```bash
curl -X DELETE http://127.0.0.1:8000/jobs/{job_id}/
```

## Example workflow

```bash
# 1. Create a job and capture the response
curl -s -X POST http://127.0.0.1:8000/jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Frontend Developer",
    "salary": 95000,
    "location": "Lisbon",
    "company": "StartupXYZ",
    "company_url": "https://startupxyz.com",
    "company_logo": "https://startupxyz.com/logo.png",
    "company_description": "Early-stage fintech",
    "company_location": "Lisbon, Portugal"
  }'

# 2. List all jobs
curl http://127.0.0.1:8000/jobs/

# 3. Get one job (use the id from step 1)
curl http://127.0.0.1:8000/jobs/YOUR_JOB_ID_HERE/
```
