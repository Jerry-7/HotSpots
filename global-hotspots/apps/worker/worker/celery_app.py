from celery import Celery

from worker.config import REDIS_URL


celery_app = Celery("hotspots_worker", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.task_routes = {
    "worker.tasks.ingest.*": {"queue": "ingest"},
    "worker.tasks.pipeline.*": {"queue": "pipeline"},
}

celery_app.autodiscover_tasks(["worker.tasks"])
