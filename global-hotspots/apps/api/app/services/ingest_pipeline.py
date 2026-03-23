from __future__ import annotations

import hashlib
import os
import time
from datetime import datetime, timedelta, timezone

import feedparser
import httpx
from sqlalchemy import and_, delete, select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.event_score import EventScore
from app.models.runtime_setting import RuntimeSetting
from app.models.source import Source
from app.models.source_config import SourceConfig
from app.core.config import settings


TOPIC_KEYWORDS = {
    "technology": ["ai", "chip", "cloud", "software", "tech", "startup", "robot"],
    "finance": ["market", "stock", "bank", "inflation", "economy", "oil", "energy"],
    "society": ["flood", "storm", "earthquake", "health", "education", "policy", "transport"],
    "politics": ["election", "minister", "parliament", "government", "diplomatic"],
}

REGION_HINTS = {
    "europe": ["europe", "berlin", "london", "paris", "brussels", "germany", "france", "uk"],
    "north-america": ["united states", "usa", "washington", "new york", "san francisco", "canada"],
    "asia": ["asia", "china", "japan", "tokyo", "india", "singapore", "seoul"],
    "middle-east": ["middle east", "israel", "uae", "saudi", "qatar", "iran"],
    "latin-america": ["latin", "brazil", "mexico", "argentina", "chile"],
    "africa": ["africa", "nigeria", "kenya", "south africa", "egypt"],
}

REGION_COORDS = {
    "global": (20.0, 0.0),
    "europe": (50.0, 10.0),
    "north-america": (39.0, -98.0),
    "asia": (35.0, 105.0),
    "middle-east": (29.0, 47.0),
    "latin-america": (-15.0, -60.0),
    "africa": (2.0, 20.0),
}


def _normalize_text(text: str) -> str:
    return " ".join((text or "").strip().split())


def _fingerprint(text: str) -> str:
    return hashlib.sha1(_normalize_text(text).lower().encode("utf-8")).hexdigest()

# 主题分类
def _infer_topic(text: str) -> str:
    lower = text.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(word in lower for word in keywords):
            return topic
    return "society"

# 地域分类
def _infer_region(text: str) -> str:
    lower = text.lower()
    for region, keywords in REGION_HINTS.items():
        if any(word in lower for word in keywords):
            return region
    return "global"

# 国家分类
def _infer_country(text: str) -> str:
    lower = text.lower()
    if "united states" in lower or "usa" in lower:
        return "United States"
    if "japan" in lower or "tokyo" in lower:
        return "Japan"
    if "germany" in lower or "berlin" in lower:
        return "Germany"
    if "france" in lower or "paris" in lower:
        return "France"
    if "china" in lower:
        return "China"
    if "uk" in lower or "london" in lower:
        return "United Kingdom"
    return "Global"

# 城市分类
def _infer_city(text: str) -> str:
    lower = text.lower()
    for city in ["Berlin", "London", "Paris", "Tokyo", "San Francisco", "New York", "Washington", "Singapore"]:
        if city.lower() in lower:
            return city
    return ""


def _infer_coords(region: str, title: str) -> tuple[float, float]:
    seed = int(_fingerprint(f"{region}:{title}")[:8], 16)
    base_lat, base_lng = REGION_COORDS.get(region, REGION_COORDS["global"])
    lat_offset = ((seed % 1000) / 1000.0 - 0.5) * 8.0
    lng_offset = (((seed // 1000) % 1000) / 1000.0 - 0.5) * 12.0
    return round(base_lat + lat_offset, 4), round(base_lng + lng_offset, 4)


def _clean_title(title: str, fallback: str) -> str:
    cleaned = _normalize_text(title)
    if cleaned:
        return cleaned[:255]
    return fallback[:255]


def _clean_summary(summary: str, fallback: str) -> str:
    cleaned = _normalize_text(summary)
    if cleaned:
        return cleaned[:1000]
    return fallback[:1000]

# 解析新闻源 RSS
def _fetch_rss_items(source: Source, timeout: float = 8.0, proxy_url: str | None = None) -> list[dict]:
    if proxy_url:
        transport = httpx.HTTPTransport(proxy=proxy_url)
        with httpx.Client(timeout=timeout, transport=transport, follow_redirects=True) as client:
            resp = client.get(source.base_url)
            resp.raise_for_status()
            parsed = feedparser.parse(resp.text)
    else:
        parsed = feedparser.parse(source.base_url)
    items: list[dict] = []
    for entry in (parsed.entries or [])[:40]:
        title = _clean_title(getattr(entry, "title", ""), f"{source.name} update")
        summary = _clean_summary(getattr(entry, "summary", "") or getattr(entry, "description", ""), title)
        items.append(
            {
                "source": source.name,
                "title": title,
                "summary": summary,
            }
        )
    return items


def _fetch_newsapi_items(source: Source, timeout: float = 8.0, proxy_url: str | None = None) -> list[dict]:
    key = os.getenv("NEWS_API_KEY", "").strip()
    if not key:
        return []
    params = {
        "apiKey": key,
        "language": source.language or "en",
        "pageSize": 40,
        "sortBy": "publishedAt",
        "q": "world OR global OR economy OR technology",
    }
    url = source.base_url.rstrip("/") + "/v2/everything"
    transport = httpx.HTTPTransport(proxy=proxy_url) if proxy_url else None
    with httpx.Client(timeout=timeout, transport=transport, follow_redirects=True) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        payload = resp.json()
    articles = payload.get("articles", [])
    items: list[dict] = []
    for article in articles:
        title = _clean_title(str(article.get("title", "")), f"{source.name} news")
        summary = _clean_summary(str(article.get("description") or article.get("content") or ""), title)
        items.append({"source": source.name, "title": title, "summary": summary})
    return items


def _runtime_proxy_url(db: Session) -> str | None:
    row = db.scalar(select(RuntimeSetting).where(RuntimeSetting.key == "source_proxy_url"))
    if row and row.value.strip():
        return row.value.strip()
    if settings.source_proxy_url and settings.source_proxy_url.strip():
        return settings.source_proxy_url.strip()
    return None


def _fetch_source_items(source: Source, proxy_url: str | None = None) -> list[dict]:
    timeout = settings.source_connect_timeout_seconds
    try:
        if source.source_type == "rss":
            return _fetch_rss_items(source, timeout=timeout, proxy_url=proxy_url)
        if source.source_type == "news_api":
            return _fetch_newsapi_items(source, timeout=timeout, proxy_url=proxy_url)
    except Exception:
        return []
    return []


def check_source_connectivity(db: Session) -> list[dict]:
    sources = db.scalars(select(Source).order_by(Source.id.asc())).all()
    proxy_url = _runtime_proxy_url(db)
    result: list[dict] = []

    for src in sources:
        start = time.perf_counter()
        try:
            if src.source_type == "rss":
                transport = None
                if proxy_url:
                    transport = httpx.HTTPTransport(proxy=proxy_url)
                with httpx.Client(
                    timeout=settings.source_connect_timeout_seconds,
                    transport=transport,
                    follow_redirects=True,
                ) as client:
                    resp = client.get(src.base_url)
                    resp.raise_for_status()
                status = "ok"
                detail = f"HTTP {resp.status_code}"
            elif src.source_type == "news_api":
                key = os.getenv("NEWS_API_KEY", "").strip()
                if not key:
                    status = "skipped"
                    detail = "NEWS_API_KEY not set"
                else:
                    transport = None
                    if proxy_url:
                        transport = httpx.HTTPTransport(proxy=proxy_url)
                    with httpx.Client(
                        timeout=settings.source_connect_timeout_seconds,
                        transport=transport,
                        follow_redirects=True,
                    ) as client:
                        ping_url = src.base_url.rstrip("/") + "/v2/top-headlines"
                        resp = client.get(ping_url, params={"apiKey": key, "language": src.language or "en", "pageSize": 1})
                        resp.raise_for_status()
                    status = "ok"
                    detail = f"HTTP {resp.status_code}"
            else:
                status = "skipped"
                detail = f"unsupported source_type={src.source_type}"
        except Exception as exc:
            status = "error"
            detail = str(exc)

        latency = int((time.perf_counter() - start) * 1000)
        result.append(
            {
                "source_id": src.id,
                "status": status,
                "latency_ms": latency,
                "detail": detail,
            }
        )

    return result

#
def ingest_sources(db: Session, user_id: int | None = None) -> dict:
    sources = db.scalars(select(Source).order_by(Source.id.asc())).all()
    proxy_url = _runtime_proxy_url(db)
    if not sources:
        return {"sources": 0, "fetched": 0, "inserted": 0}

    by_source_config: dict[int, SourceConfig] = {}
    if user_id is not None:
        configs = db.scalars(select(SourceConfig).where(SourceConfig.user_id == user_id)).all()
        by_source_config = {cfg.source_id: cfg for cfg in configs}

    enabled_sources: list[Source] = []
    for source in sources:
        cfg = by_source_config.get(source.id)
        enabled = cfg.enabled if cfg else source.enabled_default
        if enabled:
            enabled_sources.append(source)

    if not enabled_sources:
        return {"sources": 0, "fetched": 0, "inserted": 0}

    inserted = 0
    fetched = 0
    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=3)

    recent_events = db.scalars(select(Event).where(Event.created_at >= recent_cutoff)).all()
    seen = {_fingerprint(evt.title) for evt in recent_events}

    for source in enabled_sources:
        items = _fetch_source_items(source, proxy_url=proxy_url)
        fetched += len(items)
        for item in items:
            fp = _fingerprint(item["title"])
            if fp in seen:
                continue
            text = f"{item['title']} {item['summary']}"
            region = _infer_region(text)
            lat, lng = _infer_coords(region, item["title"])
            event = Event(
                title=item["title"],
                summary=item["summary"],
                topic=_infer_topic(text),
                region=region,
                country=_infer_country(text),
                city=_infer_city(text),
                lat=lat,
                lng=lng,
            )
            db.add(event)
            seen.add(fp)
            inserted += 1

    if inserted:
        db.commit()

    return {"sources": len(enabled_sources), "fetched": fetched, "inserted": inserted}


def _level(score: float) -> str:
    if score >= 90:
        return "S"
    if score >= 75:
        return "A"
    if score >= 60:
        return "B"
    return "C"


def rebuild_scores(db: Session) -> dict:
    now = datetime.now(timezone.utc)
    windows = {
        "1h": now - timedelta(hours=1),
        "6h": now - timedelta(hours=6),
        "24h": now - timedelta(hours=24),
        "7d": now - timedelta(days=7),
        "30d": now - timedelta(days=30),
    }

    db.execute(delete(EventScore))
    events = db.scalars(select(Event)).all()
    if not events:
        db.commit()
        return {"events": 0, "scores": 0}

    total_scores = 0
    for event in events:
        age_hours = max(1.0, (now - event.created_at).total_seconds() / 3600.0)
        freshness = max(0.1, min(1.0, 24.0 / age_hours))
        text = f"{event.title} {event.summary}".lower()
        keyword_hits = sum(1 for words in TOPIC_KEYWORDS.values() if any(w in text for w in words))
        signal = min(1.0, 0.2 + keyword_hits * 0.18)
        location_boost = 0.12 if event.region != "global" else 0.0
        base_importance = min(99.0, (52 + signal * 30 + location_boost * 20 + freshness * 17))

        for win, cutoff in windows.items():
            decay = 1.0 if event.created_at >= cutoff else max(0.2, freshness * 0.7)
            importance = round(base_importance * decay, 2)
            hot = round(min(99.0, importance * 0.85 + signal * 12), 2)
            db.add(
                EventScore(
                    event_id=event.id,
                    window=win,
                    hot_score=hot,
                    importance_score=importance,
                    level=_level(importance),
                    reasons={"freshness": round(freshness, 3), "signal": round(signal, 3), "window": win},
                )
            )
            total_scores += 1

    db.commit()
    return {"events": len(events), "scores": total_scores}


def run_full_refresh(db: Session, user_id: int | None = None) -> dict:
    ingest: dict
    score: dict

    try:
        ingest = ingest_sources(db, user_id=user_id)
        ingest_status = "ok"
    except Exception as exc:
        ingest = {"error": str(exc)}
        ingest_status = "error"

    try:
        score = rebuild_scores(db)
        score_status = "ok"
    except Exception as exc:
        score = {"error": str(exc)}
        score_status = "error"

    return {
        "ingest": ingest,
        "score": score,
        "status": "ok" if ingest_status == "ok" and score_status == "ok" else "partial",
        "stages": {
            "ingest": ingest_status,
            "score": score_status,
        },
    }


def preview_source_fetch(db: Session, source_id: int, limit: int = 5) -> dict:
    source = db.get(Source, source_id)
    if not source:
        return {
            "source_id": source_id,
            "source_name": "",
            "status": "error",
            "count": 0,
            "detail": "Source not found",
            "items": [],
        }

    try:
        proxy_url = _runtime_proxy_url(db)
        items = _fetch_source_items(source, proxy_url=proxy_url)
        preview = [{"title": row["title"], "summary": row["summary"]} for row in items[: max(1, min(20, limit))]]
        return {
            "source_id": source.id,
            "source_name": source.name,
            "status": "ok",
            "count": len(preview),
            "detail": None,
            "items": preview,
        }
    except Exception as exc:
        return {
            "source_id": source.id,
            "source_name": source.name,
            "status": "error",
            "count": 0,
            "detail": str(exc),
            "items": [],
        }
