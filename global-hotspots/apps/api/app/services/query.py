from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.event_score import EventScore
from app.schemas.events import HotspotItem


def list_rankings(
    db: Session,
    window: str,
    region: str,
    topic: str,
    limit: int,
    start: str | None,
    end: str | None,
) -> list[HotspotItem]:
    if window == "custom":
        effective_window = f"custom:{start or ''}:{end or ''}"
    else:
        effective_window = window

    stmt = (
        select(Event, EventScore)
        .join(EventScore, Event.id == EventScore.event_id)
        .where(EventScore.window == effective_window if window == "custom" else EventScore.window == window)
        .order_by(desc(EventScore.importance_score), desc(EventScore.hot_score))
        .limit(limit)
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
