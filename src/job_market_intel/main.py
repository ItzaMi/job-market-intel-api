from fastapi import FastAPI

from .routers.jobs import router as jobs_router

app = FastAPI()

@app.get("/health/")
async def health():
    return {"status": "ok"}

app.include_router(jobs_router)