from pydantic import BaseModel


class HotspotItem(BaseModel):
    event_id: int
    title: str
    summary: str
    topic: str
    region: str
    country: str
    city: str
    lat: float
    lng: float
    hot_score: float
    importance_score: float
    level: str
    reasons: dict


class GlobePointItem(BaseModel):
    event_id: int
    title: str
    lat: float
    lng: float
    hot_score: float
    importance_score: float
    level: str
