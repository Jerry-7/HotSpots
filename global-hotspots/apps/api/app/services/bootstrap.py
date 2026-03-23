from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.source import Source


DEFAULT_SOURCES = [
    {
        "name": "BBC World",
        "source_type": "rss",
        "region": "global",
        "language": "en",
        "base_url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "reliability_score": 0.9,
    },
    {
        "name": "Reuters World",
        "source_type": "rss",
        "region": "global",
        "language": "en",
        "base_url": "https://www.reutersagency.com/feed/?best-topics=world&post_type=best",
        "reliability_score": 0.92,
    },
    {
        "name": "NewsAPI",
        "source_type": "news_api",
        "region": "global",
        "language": "en",
        "base_url": "https://newsapi.org/",
        "reliability_score": 0.75,
    },
]


def seed_sources() -> None:
    with SessionLocal() as db:
        # 查询数据库所有信息源
        existing = db.scalars(select(Source)).all()
        if existing:
            return
        # 没有则把默认的记录数据库
        for item in DEFAULT_SOURCES:
            db.add(Source(**item))
        db.commit()


def seed_demo_data() -> None:
    # Demo data is intentionally disabled by default.
    # Real events should come from configured sources via the refresh pipeline.
    return
