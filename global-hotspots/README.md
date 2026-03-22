# Global Hotspots MVP

Monorepo for a global-hotspots web app MVP.

## Structure

- `apps/api`: FastAPI backend (auth, source config, AI keys, hotspots, rankings, globe points)
- `apps/worker`: Celery worker (ingest, clustering, scoring pipeline placeholders)
- `apps/web`: Next.js frontend shell (globe, rankings, settings)
- `infra`: deployment notes and local infra defaults

## Quick start

1. Copy `.env.example` to `.env` and fill required values.
2. Start dependencies:
   - `docker compose up -d postgres redis`
3. Run API:
   - `cd apps/api && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000`
4. Run worker:
   - `cd apps/worker && pip install -r requirements.txt && celery -A worker.celery_app worker --loglevel=info`
5. Run frontend:
   - `cd apps/web && npm install && npm run dev`

## Notes

- OTP email sending is stubbed to console log for MVP.
- AI provider key storage is encrypted at rest using `APP_ENCRYPTION_KEY`.
- Demo seed is disabled by default. No fake hotspot data is shown unless you explicitly set `SOURCE_SEED_DEMO_DATA=true`.

## Fast usable mode (new)

- API now provides one-click pipeline endpoint: `POST /api/v1/refresh`.
- The endpoint runs: source ingest (RSS + optional NewsAPI) -> score rebuild (`1h/6h/24h/7d/30d`).
- Web settings page now has a button: `一键刷新热点数据`.
- Worker tasks now call the same refresh endpoint, so celery queue can trigger updates too.

### Optional env for ingest

- `NEWS_API_KEY`: enable NewsAPI fetch (`source_type=news_api`). Empty means skip NewsAPI.
- `SOURCE_PROXY_URL`: optional outbound proxy for source fetch/connectivity checks (e.g. `http://127.0.0.1:7890`).
- `SOURCE_CONNECT_TIMEOUT_SECONDS`: source request timeout seconds.
- `SOURCE_SEED_DEMO_DATA`: set `true` only if you want startup demo events.
- `API_BASE_URL`: worker callback API base URL (default `http://localhost:8000`).
- `API_REFRESH_TOKEN`: worker bearer token for refresh endpoint (default `demo-token`).

### Quick verify

1. Start postgres + redis.
2. Start API and web.
3. Open settings page and click `一键刷新热点数据`.
4. Go back to home/ranking page and verify hotspots changed.

### Source connectivity + proxy

- Settings page now supports runtime proxy configuration and displays per-source connectivity status.
- API endpoints:
  - `GET /api/v1/settings/runtime/proxy`
  - `POST /api/v1/settings/runtime/proxy`
  - `GET /api/v1/sources/connectivity`

## Minimal tests

- Added minimal route-level regression tests in `apps/api/tests/test_routes_minimal.py`.
- Run tests:
  - `cd apps/api && python -m unittest tests.test_routes_minimal -v`
