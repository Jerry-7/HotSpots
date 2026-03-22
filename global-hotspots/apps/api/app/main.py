from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.events import router as events_router
from app.api.routes.rankings import router as rankings_router
from app.api.routes.settings import router as settings_router
from app.api.routes.sources import router as sources_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import ai_provider_key, email_otp, event, event_score, runtime_setting, source, source_config, user
from app.services.bootstrap import seed_demo_data, seed_sources


app = FastAPI(title="Global Hotspots API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    seed_sources()
    if settings.source_seed_demo_data:
        seed_demo_data()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


app.include_router(auth_router, prefix="/api/v1")
app.include_router(events_router, prefix="/api/v1")
app.include_router(rankings_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(sources_router, prefix="/api/v1")
