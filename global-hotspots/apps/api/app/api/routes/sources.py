from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_session
from app.models.source import Source
from app.models.source_config import SourceConfig
from app.models.user import User
from app.schemas.sources import SourceConnectivityItem, SourceItem, UpdateSourceConfigIn
from app.services.ingest_pipeline import check_source_connectivity


router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceItem])
def list_sources(user: User = Depends(current_user), db: Session = Depends(db_session)) -> list[SourceItem]:
    sources = db.scalars(select(Source).order_by(Source.id.asc())).all()
    configs = db.scalars(select(SourceConfig).where(SourceConfig.user_id == user.id)).all()
    by_source = {cfg.source_id: cfg for cfg in configs}
    items: list[SourceItem] = []
    for src in sources:
        cfg = by_source.get(src.id)
        items.append(
            SourceItem(
                source_id=src.id,
                name=src.name,
                source_type=src.source_type,
                region=src.region,
                language=src.language,
                reliability_score=src.reliability_score,
                enabled=cfg.enabled if cfg else src.enabled_default,
                weight=cfg.weight if cfg else 1.0,
                crawl_interval_minutes=cfg.crawl_interval_minutes if cfg else 30,
                keyword_allowlist=cfg.keyword_allowlist if cfg else [],
                keyword_blocklist=cfg.keyword_blocklist if cfg else [],
            )
        )
    return items


@router.patch("/{source_id}", response_model=SourceItem)
def update_source(
    source_id: int,
    payload: UpdateSourceConfigIn,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> SourceItem:
    src = db.get(Source, source_id)
    if not src:
        raise HTTPException(status_code=404, detail="Source not found")
    cfg = db.scalar(
        select(SourceConfig).where(and_(SourceConfig.user_id == user.id, SourceConfig.source_id == source_id))
    )
    if not cfg:
        cfg = SourceConfig(user_id=user.id, source_id=source_id)
        db.add(cfg)

    for field in ["enabled", "weight", "crawl_interval_minutes", "keyword_allowlist", "keyword_blocklist"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(cfg, field, value)
    db.commit()
    db.refresh(cfg)

    return SourceItem(
        source_id=src.id,
        name=src.name,
        source_type=src.source_type,
        region=src.region,
        language=src.language,
        reliability_score=src.reliability_score,
        enabled=cfg.enabled,
        weight=cfg.weight,
        crawl_interval_minutes=cfg.crawl_interval_minutes,
        keyword_allowlist=cfg.keyword_allowlist,
        keyword_blocklist=cfg.keyword_blocklist,
    )


@router.get("/connectivity", response_model=list[SourceConnectivityItem])
def source_connectivity(
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> list[SourceConnectivityItem]:
    _ = user
    rows = check_source_connectivity(db)
    return [SourceConnectivityItem(**row) for row in rows]
