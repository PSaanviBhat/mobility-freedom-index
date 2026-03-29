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
async def compare_routes(request: Request, body: RouteRequest):
    NODES = request.app.state.nodes
    ROUTES = request.app.state.routes

    # Find matching routes
    matching = [
        r for r in ROUTES
        if r["source_id"] == body.source_id and r["dest_id"] == body.dest_id
    ]

    if not matching:
        return {"error": "No routes available for this zone yet."}

    results = []
    for route in matching:
        # Get node objects for this route
        path_nodes = [NODES[nid] for nid in route["path_nodes"] if nid in NODES]

        # Aggregate features
        features = aggregate_features(path_nodes, body.hour_of_day, body.weather_visibility)

        # ML inference — plug in your model here
        from services.scoring import compute_mobility_score
        ml_output = compute_mobility_score(features)
        risk_multiplier = (100 - ml_output["mobility_freedom_score"]) / 10

        # Final freedom score
        freedom_score = compute_freedom_score(risk_multiplier, route["distance_km"])
        risk_level = "low" if freedom_score > 65 else "medium" if freedom_score > 40 else "high"

        results.append({
            "route_id": route["route_id"],
            "name": route["name"],
            "distance_km": route["distance_km"],
            "route_type": route["route_type"],
            "path_nodes": [
                {"node_id": n["node_id"], "name": n["name"], "lat": n["lat"], "lng": n["lng"]}
                for n in path_nodes
            ],
            "features": features,
            "mobility_freedom_score": freedom_score,
            "risk_level": risk_level,
            "recommendation": f"{'Recommended' if freedom_score == max(r.get('mobility_freedom_score', 0) for r in results or [{'mobility_freedom_score': 0}]) else 'Alternative'} route with {risk_level} risk."
        })

    # Sort by freedom score descending (safest first)
    results.sort(key=lambda x: x["mobility_freedom_score"], reverse=True)
    results[0]["recommendation"] = "✓ Recommended — highest safety score for this time."

    return {"routes": results, "source_id": body.source_id, "dest_id": body.dest_id}

@router.get("/nodes")
async def get_nodes(request: Request):
    """Frontend calls this to populate the source/destination dropdowns."""
    NODES = request.app.state.nodes
    return [
        {"node_id": n["node_id"], "name": n["name"], "lat": n["lat"], "lng": n["lng"]}
        for n in NODES.values()
    ]