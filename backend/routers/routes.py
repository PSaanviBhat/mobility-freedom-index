from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import List

router = APIRouter()

class RouteRequest(BaseModel):
    source_id: str
    dest_id: str
    hour_of_day: int
    weather_visibility: float = 8.0

def apply_time_multipliers(node: dict, hour: int) -> dict:
    # Crowd adjustment
    if 7 <= hour <= 10 or 17 <= hour <= 20:
        crowd = node["base_crowd"] * 1.2
    elif 0 <= hour <= 5:
        crowd = node["base_crowd"] * 0.1
    else:
        crowd = node["base_crowd"] * 0.8

    # Lighting adjustment
    if 6 < hour < 18:
        lighting = 100.0
    else:
        lighting = node["base_lighting"]

    return {
        **node,
        "adjusted_crowd": round(min(crowd, 100), 2),
        "adjusted_lighting": round(lighting, 2),
    }

def aggregate_features(nodes: list, hour: int, weather_visibility: float) -> dict:
    adjusted = [apply_time_multipliers(n, hour) for n in nodes]
    return {
        "crime_density": max(n["base_crime_density"] for n in adjusted),  # worst case
        "crime_trend": sum(n["crime_trend"] for n in adjusted) / len(adjusted),
        "violence_ratio": max(n["violence_ratio"] for n in adjusted),
        "lighting": sum(n["adjusted_lighting"] for n in adjusted) / len(adjusted),
        "crowd_density": sum(n["adjusted_crowd"] for n in adjusted) / len(adjusted),
        "transport_availability": sum(n["transport_availability"] for n in adjusted) / len(adjusted),
        "weather_visibility": weather_visibility,
        "hour_of_day": hour,
    }

def compute_freedom_score(risk_multiplier: float, distance_km: float) -> float:
    distance_penalty = 1 + (distance_km - 4) * 0.05  # penalty grows with distance
    score = (100 - (risk_multiplier * 10)) * (1 / max(distance_penalty, 1))
    return round(min(max(score, 0), 100), 2)

@router.post("/compare")
async def compare_routes_endpoint(request: Request, body: RouteRequest):
    from services.scoring import compare_routes
    result = compare_routes(
        source_id=body.source_id,
        dest_id=body.dest_id,
        hour_of_day=body.hour_of_day,
        weather_visibility=body.weather_visibility
    )
    return result

@router.get("/nodes")
async def get_nodes(request: Request):
    """Frontend calls this to populate the source/destination dropdowns."""
    NODES = request.app.state.nodes
    return [
        {"node_id": n["node_id"], "name": n["name"], "lat": n["lat"], "lng": n["lng"]}
        for n in NODES.values()
    ]