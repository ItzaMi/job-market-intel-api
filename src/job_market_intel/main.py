from fastapi import FastAPI

from .routers.jobs import router as jobs_router
from .routers.ingestion_runs import router as ingestion_runs_router

app = FastAPI()

@app.get("/health/")
async def health():
    return {"status": "ok"}

app.include_router(jobs_router)
app.include_router(ingestion_runs_router)