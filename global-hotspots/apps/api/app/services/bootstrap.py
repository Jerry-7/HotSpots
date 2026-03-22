from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.event import Event
from app.models.event_score import EventScore
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
    with SessionLocal() as db:
        existing = db.scalars(select(Event)).all()
        if existing:
            return
        events = [
            Event(
                title="European energy market volatility rises",
                summary="Gas futures surged after new transport restrictions impacted supply routes.",
                topic="finance",
                region="europe",
                country="Germany",
                city="Berlin",
                lat=52.52,
                lng=13.405,
            ),
            Event(
                title="Major AI chip launch accelerates cloud competition",
                summary="Several hyperscalers announced expanded data center investments following a new chip release.",
                topic="technology",
                region="north-america",
                country="United States",
                city="San Francisco",
                lat=37.7749,
                lng=-122.4194,
            ),
            Event(
                title="Severe rainfall disrupts logistics routes",
                summary="Flood alerts expanded across multiple coastal districts, delaying port operations.",
                topic="society",
                region="asia",
                country="Japan",
                city="Tokyo",
                lat=35.6762,
                lng=139.6503,
            ),
        ]
        for event in events:
            db.add(event)
        db.flush()

        scores = [
            EventScore(event_id=events[0].id, window="24h", hot_score=77, importance_score=82, level="A", reasons={"spread": 0.8}),
            EventScore(event_id=events[1].id, window="24h", hot_score=88, importance_score=90, level="S", reasons={"spread": 0.9}),
            EventScore(event_id=events[2].id, window="24h", hot_score=71, importance_score=75, level="A", reasons={"spread": 0.7}),
        ]
        for score in scores:
            db.add(score)
        db.commit()
