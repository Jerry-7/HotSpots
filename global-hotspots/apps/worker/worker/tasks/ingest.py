import httpx

from worker.celery_app import celery_app
from worker.config import API_BASE_URL, API_REFRESH_TOKEN


def _trigger_refresh() -> dict:
    url = API_BASE_URL.rstrip("/") + "/api/v1/refresh"
    with httpx.Client(timeout=20.0) as client:
        resp = client.post(url, headers={"Authorization": f"Bearer {API_REFRESH_TOKEN}"})
        resp.raise_for_status()
        return resp.json()


@celery_app.task(name="worker.tasks.ingest.fetch_news_api")
def fetch_news_api() -> dict:
    data = _trigger_refresh()
    return {"status": "ok", "source": "news_api", "refresh": data}


@celery_app.task(name="worker.tasks.ingest.fetch_rss")
def fetch_rss() -> dict:
    data = _trigger_refresh()
    return {"status": "ok", "source": "rss", "refresh": data}
