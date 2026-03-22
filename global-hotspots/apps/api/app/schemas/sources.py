from pydantic import BaseModel


class SourceItem(BaseModel):
    source_id: int
    name: str
    source_type: str
    region: str
    language: str
    reliability_score: float
    enabled: bool
    weight: float
    crawl_interval_minutes: int
    keyword_allowlist: list[str]
    keyword_blocklist: list[str]


class SourceConnectivityItem(BaseModel):
    source_id: int
    status: str
    latency_ms: int | None = None
    detail: str | None = None


class UpdateSourceConfigIn(BaseModel):
    enabled: bool | None = None
    weight: float | None = None
    crawl_interval_minutes: int | None = None
    keyword_allowlist: list[str] | None = None
    keyword_blocklist: list[str] | None = None
