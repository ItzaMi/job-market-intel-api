import os

from celery import Celery

celery_app = Celery(
    "job_market_intel",
    broker=os.environ["CELERY_BROKER_URL"],
    backend=os.environ["CELERY_RESULT_BACKEND"],
)

celery_app.autodiscover_tasks(["job_market_intel"])