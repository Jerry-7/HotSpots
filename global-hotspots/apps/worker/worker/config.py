import os


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/hotspots")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_REFRESH_TOKEN = os.getenv("API_REFRESH_TOKEN", "demo-token")
