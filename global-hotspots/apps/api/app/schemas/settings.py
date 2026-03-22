from pydantic import BaseModel


class UpsertAIKeyIn(BaseModel):
    provider: str
    api_key: str
    model: str
    base_url: str | None = None
    is_default: bool = False


class ProviderItem(BaseModel):
    provider: str
    model: str
    base_url: str | None
    is_default: bool
    key_preview: str


class RuntimeProxyIn(BaseModel):
    source_proxy_url: str | None = None


class RuntimeProxyOut(BaseModel):
    source_proxy_url: str | None
