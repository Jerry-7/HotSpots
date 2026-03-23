import time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_session
from app.models.event import Event
from app.models.event_score import EventScore
from app.models.user import User
from app.schemas.events import GlobePointItem, HotspotItem
from app.services.ingest_pipeline import run_full_refresh


router = APIRouter(tags=["events"])
REFRESH_COOLDOWN_SECONDS = 20
_refresh_last_called: dict[int, float] = {}


def _effective_window(window: str, start: str | None, end: str | None) -> str:
    if window != "custom":
        return window
    return f"custom:{start or ''}:{end or ''}"


@router.get("/hotspots", response_model=list[HotspotItem])
def hotspots(
    window: str = Query("24h"),
    region: str = Query("global"),
    topic: str = Query("all"),
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> list[HotspotItem]:
    _ = user
    effective_window = _effective_window(window, start, end)
    stmt = (
        select(Event, EventScore)
        .join(EventScore, Event.id == EventScore.event_id)
        .where(EventScore.window == effective_window if window == "custom" else EventScore.window == window)
        .order_by(desc(EventScore.importance_score), desc(EventScore.hot_score))
    )
    rows = db.execute(stmt).all()
    items: list[HotspotItem] = []
    for evt, score in rows:
        if region != "global" and evt.region != region:
            continue
        if topic != "all" and evt.topic != topic:
            continue
        items.append(
            HotspotItem(
                event_id=evt.id,
                title=evt.title,
                summary=evt.summary,
                topic=evt.topic,
                region=evt.region,
                country=evt.country,
                city=evt.city,
                lat=evt.lat,
                lng=evt.lng,
                hot_score=score.hot_score,
                importance_score=score.importance_score,
                level=score.level,
                reasons=score.reasons,
            )
        )
    return items


@router.get("/globe/points", response_model=list[GlobePointItem])
def globe_points(
    window: str = Query("24h"),
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> list[GlobePointItem]:
    _ = user
    stmt = (
        select(Event, EventScore)
        .join(EventScore, Event.id == EventScore.event_id)
        .where(EventScore.window == window)
        .order_by(desc(EventScore.importance_score))
    )
    rows = db.execute(stmt).all()
    return [
        GlobePointItem(
            event_id=evt.id,
            title=evt.title,
            lat=evt.lat,
            lng=evt.lng,
            hot_score=score.hot_score,
            importance_score=score.importance_score,
            level=score.level,
        )
        for evt, score in rows
    ]


@router.get("/events/{event_id}", response_model=HotspotItem)
def event_detail(
    event_id: int,
    window: str = Query("24h"),
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> HotspotItem:
    _ = user
    stmt = (
        select(Event, EventScore)
        .join(EventScore, Event.id == EventScore.event_id)
        .where(and_(Event.id == event_id, EventScore.window == window))
    )
    row = db.execute(stmt).first()
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
    evt, score = row
    return HotspotItem(
        event_id=evt.id,
        title=evt.title,
        summary=evt.summary,
        topic=evt.topic,
        region=evt.region,
        country=evt.country,
        city=evt.city,
        lat=evt.lat,
        lng=evt.lng,
        hot_score=score.hot_score,
        importance_score=score.importance_score,
        level=score.level,
        reasons=score.reasons,
    )


@router.post("/refresh")
def refresh_events(
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> dict:
    now = time.monotonic()
    last_called = _refresh_last_called.get(user.id)
    if last_called is not None and now - last_called < REFRESH_COOLDOWN_SECONDS:
        wait_seconds = int(REFRESH_COOLDOWN_SECONDS - (now - last_called)) + 1
        raise HTTPException(status_code=429, detail=f"Refresh too frequent, retry in {wait_seconds}s")
    _refresh_last_called[user.id] = now
    return run_full_refresh(db, user_id=user.id)
