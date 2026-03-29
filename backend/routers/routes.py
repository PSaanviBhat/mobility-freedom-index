import logging
import networkx as nx
from fastapi import APIRouter, HTTPException

# Import schemas from the root backend/schemas.py
from models.schemas import RouteRequest, RouteResponse

# Import logic from the services folder
from services.data_layer import CITY_GRAPH
from services.scoring import calculate_route_risk

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/routes",
    tags=["Routing Engine"]
)

@router.post("/compare", response_model=RouteResponse)
def compare_routes(request: RouteRequest):
    logger.info(f"Received route request from {request.source_id} to {request.dest_id} at hour {request.hour_of_day}")

    if request.source_id == request.dest_id:
        raise HTTPException(status_code=400, detail="Source and destination cannot be the same.")
    
    if request.source_id not in CITY_GRAPH or request.dest_id not in CITY_GRAPH:
        raise HTTPException(status_code=404, detail="Source or destination node not found in city graph.")

    try:
        path_generator = nx.shortest_simple_paths(CITY_GRAPH, request.source_id, request.dest_id, weight="distance")
        raw_paths = []
        for _ in range(3):
            try:
                raw_paths.append(next(path_generator))
            except StopIteration:
                break 
                
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail="No viable route exists between these locations.")

    if not raw_paths:
        raise HTTPException(status_code=404, detail="Failed to generate route paths.")

    evaluated_routes = []
    
    for path in raw_paths:
        actual_distance = 0.0
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i + 1]
            edge_data = CITY_GRAPH.get_edge_data(u, v, default={"distance": 1.0})
            actual_distance += edge_data.get("distance", 1.0)

        freedom_score, risk_prob, is_risky = calculate_route_risk(
            path_nodes=path,
            travel_time=request.hour_of_day,
            visibility=request.weather_visibility,
            actual_distance=actual_distance
        )

        evaluated_routes.append({
            "path_nodes": path,
            "total_distance_km": round(actual_distance, 2),
            "mobility_freedom_score": freedom_score,
            "risk_probability": risk_prob,
            "is_high_risk": is_risky
        })

    fastest_route = evaluated_routes[0]
    fastest_route["route_type"] = "Fastest"
    final_options = [fastest_route]

    if len(evaluated_routes) > 1:
        safest_route = max(evaluated_routes[1:], key=lambda x: x["mobility_freedom_score"])
        safest_route["route_type"] = "Safest"
        final_options.append(safest_route)

    if len(evaluated_routes) > 2:
        balanced_route = [r for r in evaluated_routes[1:] if r != safest_route][0]
        balanced_route["route_type"] = "Balanced"
        final_options.append(balanced_route)

    return RouteResponse(
        source_id=request.source_id,
        dest_id=request.dest_id,
        hour_of_day=request.hour_of_day,
        routes=final_options
    )