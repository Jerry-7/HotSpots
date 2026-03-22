from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EventScore(Base):
    __tablename__ = "event_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), index=True)
    window: Mapped[str] = mapped_column(String(16), index=True)
    hot_score: Mapped[float] = mapped_column(Float)
    importance_score: Mapped[float] = mapped_column(Float)
    level: Mapped[str] = mapped_column(String(2), index=True)
    reasons: Mapped[dict] = mapped_column(JSON, default=dict)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
