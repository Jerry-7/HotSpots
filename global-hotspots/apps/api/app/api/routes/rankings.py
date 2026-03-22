from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_session
from app.models.user import User
from app.schemas.events import HotspotItem
from app.services.query import list_rankings


router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get("", response_model=list[HotspotItem])
def rankings(
    window: str = Query("24h"),
    region: str = Query("global"),
    topic: str = Query("all"),
    limit: int = Query(50, ge=1, le=200),
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> list[HotspotItem]:
    _ = user
    return list_rankings(db=db, window=window, region=region, topic=topic, limit=limit, start=start, end=end)
