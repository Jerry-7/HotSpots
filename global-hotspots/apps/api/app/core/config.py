from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_debug: bool = True
    database_url: str = "postgresql+psycopg://postgres:postgres@192.168.0.241:5432/hotspots"
    jwt_secret_key: str = "change-me"
    jwt_expire_minutes: int = 1440
    otp_expire_minutes: int = 10
    otp_length: int = 6
    app_encryption_key: str = "change-me-32-byte-string"
    system_default_ai_provider: str = "openrouter"
    system_default_ai_model: str = "gpt-4o-mini"
    source_proxy_url: str | None = None
    source_connect_timeout_seconds: float = 8.0
    source_seed_demo_data: bool = False
    api_log_dir: str = "/var/log"
    api_log_file: str = "global-hotspots-api.log"
    api_log_level: str = "INFO"


settings = Settings()
