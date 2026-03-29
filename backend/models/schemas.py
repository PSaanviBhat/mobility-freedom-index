from pydantic import BaseModel

class LocationInput(BaseModel):
    lat: float
    lng: float
    timestamp: str

class MobilityScoreResponse(BaseModel):
    lat: float
    lng: float
    mobility_freedom_score: float
    safety_score: float
    accessibility_score: float
    visibility_score: float
    risk_level: str
    recommendation: str

class RouteRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    timestamp: str

class HeatmapZone(BaseModel):
    lat: float
    lng: float
    score: float
    zone_type: str
class RouteOption(BaseModel):
    route_type: str
    path_nodes: list
    total_distance_km: float
    mobility_freedom_score: float
    risk_probability: float
    is_high_risk: bool

class RouteResponse(BaseModel):
    source_id: str
    dest_id: str
    hour_of_day: int
    routes: list[RouteOption]