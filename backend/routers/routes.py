import logging
from fastapi import APIRouter, HTTPException
from models.schemas import RouteRequest, RouteResponse, RouteOption
from services.data_layer import CITY_GRAPH, ROUTE_CATALOG
from services.scoring import calculate_route_risk, derive_risk_level, build_recommendation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/routes", tags=["Routing Engine"])

@router.post("/compare", response_model=RouteResponse)
def compare_routes(request: RouteRequest):
    if request.source_id == request.dest_id:
        raise HTTPException(status_code=400, detail="Source and destination cannot be the same.")
    if request.source_id not in CITY_GRAPH or request.dest_id not in CITY_GRAPH:
        raise HTTPException(status_code=404, detail="Source or destination node not found.")

    matching_routes = [
        route for route in ROUTE_CATALOG
        if route.get("source_id") == request.source_id and route.get("dest_id") == request.dest_id
    ]

    if not matching_routes:
        raise HTTPException(status_code=404, detail="No route options generated.")

    evaluated = []
    for route in matching_routes:
        path = route.get("path_nodes", [])
        dist = float(route.get("distance_km", 0.0))

        score, prob, is_risky, _ = calculate_route_risk(
            path_nodes=path,
            travel_time=request.hour_of_day,
            visibility=request.weather_visibility,
            actual_distance=dist,
        )
        risk_level = derive_risk_level(score)
        rec = build_recommendation(risk_level, request.hour_of_day >= 20 or request.hour_of_day <= 5)

        evaluated.append({
            "route_name": route.get("name", "Unnamed Route"),
            "path_nodes": path,
            "total_distance_km": round(dist, 2),
            "mobility_freedom_score": round(score, 1),
            "risk_probability": round(prob, 4),
            "is_high_risk": bool(is_risky),
            "risk_level": risk_level,
            "recommendation": rec,
        })

    evaluated.sort(key=lambda x: x["total_distance_km"])
    evaluated[0]["route_type"] = "Fastest"

    if len(evaluated) > 1:
        safest = max(evaluated[1:], key=lambda x: x["mobility_freedom_score"])
        safest["route_type"] = "Safest"
    if len(evaluated) > 2:
        remaining = [r for r in evaluated[1:] if r.get("route_type") != "Safest"]
        if remaining:
            remaining[0]["route_type"] = "Balanced"

    final_routes = [r for r in evaluated if "route_type" in r]

    return RouteResponse(
        source_id=request.source_id,
        dest_id=request.dest_id,
        hour_of_day=request.hour_of_day,
        routes=[RouteOption(**r) for r in final_routes],
    )
