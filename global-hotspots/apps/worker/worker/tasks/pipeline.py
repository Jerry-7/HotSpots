import httpx

from worker.celery_app import celery_app
from worker.config import API_BASE_URL, API_REFRESH_TOKEN


def _trigger_refresh() -> dict:
    url = API_BASE_URL.rstrip("/") + "/api/v1/refresh"
    with httpx.Client(timeout=20.0) as client:
        resp = client.post(url, headers={"Authorization": f"Bearer {API_REFRESH_TOKEN}"})
        resp.raise_for_status()
        return resp.json()


@celery_app.task(name="worker.tasks.pipeline.cluster_events")
def cluster_events() -> dict:
    data = _trigger_refresh()
    return {"status": "ok", "step": "cluster_events", "ingest": data.get("ingest", {})}


@celery_app.task(name="worker.tasks.pipeline.score_events")
def score_events() -> dict:
    data = _trigger_refresh()
    return {"status": "ok", "step": "score_events", "score": data.get("score", {})}


@celery_app.task(name="worker.tasks.pipeline.build_rankings")
def build_rankings() -> dict:
    data = _trigger_refresh()
    return {"status": "ok", "step": "build_rankings", "score": data.get("score", {})}
