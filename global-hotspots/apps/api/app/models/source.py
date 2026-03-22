from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    source_type: Mapped[str] = mapped_column(String(40))
    region: Mapped[str] = mapped_column(String(64), default="global")
    language: Mapped[str] = mapped_column(String(16), default="en")
    base_url: Mapped[str] = mapped_column(String(512))
    reliability_score: Mapped[float] = mapped_column(Float, default=0.7)
    enabled_default: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
