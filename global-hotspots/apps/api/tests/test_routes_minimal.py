import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.routes import events as events_routes
from app.api.routes.settings import list_ai_providers, upsert_ai_key
from app.api.routes.sources import list_sources, update_source
from app.db.base import Base
from app.models import AIProviderKey, Event, EventScore, Source, SourceConfig, User
from app.schemas.settings import UpsertAIKeyIn
from app.schemas.sources import UpdateSourceConfigIn


class MinimalRoutesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, class_=Session)

    def _db(self) -> Session:
        return self.SessionLocal()

    def test_settings_upsert_and_list(self) -> None:
        with self._db() as db:
            user = User(email="u1@test.local")
            db.add(user)
            db.commit()
            db.refresh(user)

            payload = UpsertAIKeyIn(
                provider="openrouter",
                api_key="sk-test-12345678",
                model="gpt-4o-mini",
                base_url="https://openrouter.ai/api/v1",
                is_default=True,
            )
            item = upsert_ai_key(payload=payload, user=user, db=db)
            self.assertEqual(item.provider, "openrouter")
            self.assertTrue(item.is_default)

            providers = list_ai_providers(user=user, db=db)
            self.assertEqual(len(providers), 1)
            self.assertEqual(providers[0].provider, "openrouter")

    def test_sources_update_and_list(self) -> None:
        with self._db() as db:
            user = User(email="u2@test.local")
            source = Source(
                name="BBC Test",
                source_type="rss",
                region="global",
                language="en",
                base_url="https://example.com/rss.xml",
                reliability_score=0.9,
                enabled_default=True,
            )
            db.add(user)
            db.add(source)
            db.commit()
            db.refresh(user)
            db.refresh(source)

            updated = update_source(
                source_id=source.id,
                payload=UpdateSourceConfigIn(
                    enabled=False,
                    weight=1.4,
                    crawl_interval_minutes=45,
                    keyword_allowlist=["ai", "chip"],
                    keyword_blocklist=["sports"],
                ),
                user=user,
                db=db,
            )
            self.assertFalse(updated.enabled)
            self.assertEqual(updated.weight, 1.4)

            rows = list_sources(user=user, db=db)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].keyword_allowlist, ["ai", "chip"])

    def test_refresh_rate_limit(self) -> None:
        with self._db() as db:
            user = User(email="u3@test.local")
            db.add(user)
            db.commit()
            db.refresh(user)

            events_routes._refresh_last_called.clear()
            first = events_routes.refresh_events(user=user, db=db)
            self.assertIn("status", first)
            self.assertIn("stages", first)

            with self.assertRaises(HTTPException) as ctx:
                events_routes.refresh_events(user=user, db=db)
            self.assertEqual(ctx.exception.status_code, 429)


if __name__ == "__main__":
    unittest.main()
