from pydantic import BaseModel, Field, field_validator
from typing import List, Literal


# ---------------------------
# Score endpoint contracts
# ---------------------------
class LocationInput(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    timestamp: str  # ISO string expected

class MobilityScoreResponse(BaseModel):
    lat: float
    lng: float
    mobility_freedom_score: float = Field(..., ge=0, le=100)
    safety_score: float = Field(..., ge=0, le=100)
    accessibility_score: float = Field(..., ge=0, le=100)
    visibility_score: float = Field(..., ge=0, le=100)
    risk_probability: float = Field(..., ge=0, le=1)
    risk_level: Literal["low", "medium", "high"]
    recommendation: str

    # integrity metadata
    model_version: str
    feature_schema_version: str
    scoring_policy_version: str
    engine_mode: Literal["ml_pipeline", "fallback_rule_based"]


# ---------------------------
# Routes endpoint contracts
# ---------------------------
class RouteRequest(BaseModel):
    source_id: str
    dest_id: str
    hour_of_day: int = Field(..., ge=0, le=23)
    weather_visibility: float = Field(8.0, ge=0, le=10)

class RouteOption(BaseModel):
    route_type: Literal["Fastest", "Safest", "Balanced"]
    path_nodes: List[str]
    total_distance_km: float = Field(..., ge=0)
    mobility_freedom_score: float = Field(..., ge=0, le=100)
    risk_probability: float = Field(..., ge=0, le=1)
    is_high_risk: bool
    risk_level: Literal["low", "medium", "high"]
    recommendation: str

class RouteResponse(BaseModel):
    source_id: str
    dest_id: str
    hour_of_day: int
    routes: List[RouteOption]


# ---------------------------
# Heatmap contracts
# ---------------------------
class HeatmapZone(BaseModel):
    lat: float
    lng: float
    score: float
    zone_type: str