"""
services/scoring.py  — NEW PIPELINE VERSION
============================================
Backend calls only one function: compare_routes(source_id, dest_id, hour_of_day, weather_visibility)
"""

import joblib
import json
import numpy as np
import pandas as pd
from pathlib import Path

# --------------------------------------------------------------------------
# Load artifacts once at startup
# --------------------------------------------------------------------------
BASE_DIR     = Path(__file__).parent.parent
model        = joblib.load("mobility_freedom_model.joblib")
preprocessor = joblib.load("preprocessor.joblib")

with open("city_graph.json") as f:
    _graph  = json.load(f)
    NODES   = {n["node_id"]: n for n in _graph["nodes"]}
    ROUTES  = _graph["routes"]

FEATURE_ORDER = [
    'crime_density', 'crime_trend', 'crime_type_violence_ratio',
    'transit_lines_nearby', 'transit_frequency', 'street_connectivity',
    'avg_lighting_quality', 'crowd_density', 'weather_visibility',
    'hour_of_day', 'day_of_week', 'is_holiday',
    'route_length_km', 'num_intersections'
]


# --------------------------------------------------------------------------
# Step 1: Time-based feature adjustment
# --------------------------------------------------------------------------
def _apply_time_adjustments(node: dict, hour: int) -> dict:
    # Crowd density
    if 7 <= hour <= 10 or 17 <= hour <= 20:
        crowd = node["base_crowd"] * 1.2
    elif 0 <= hour <= 5:
        crowd = node["base_crowd"] * 0.1
    else:
        crowd = node["base_crowd"] * 0.8

    # Lighting
    if 6 < hour < 18:
        lighting = 100.0          # sun is out
    else:
        lighting = node["base_lighting"]   # rely on streetlights

    return {
        "crime_density":   node["base_crime_density"],
        "crime_trend":     node["crime_trend"],
        "violence_ratio":  node["violence_ratio"],
        "lighting":        lighting,
        "crowd":           min(100, crowd),
        "transport":       node["transport_availability"]
    }


# --------------------------------------------------------------------------
# Step 2: Aggregate node features into one feature vector
# --------------------------------------------------------------------------
def _aggregate_route_features(path_nodes: list, hour: int,
                               weather_visibility: float,
                               distance_km: float,
                               num_intersections: int) -> dict:
    adjusted = [_apply_time_adjustments(NODES[nid], hour) for nid in path_nodes]

    # Worst-case for crime, average for everything else
    return {
        "crime_density":              max(n["crime_density"]  for n in adjusted),
        "crime_trend":                np.mean([n["crime_trend"]  for n in adjusted]),
        "crime_type_violence_ratio":  max(n["violence_ratio"] for n in adjusted),
        "transit_lines_nearby":       np.mean([n["transport"]    for n in adjusted]),
        "transit_frequency":          np.mean([n["transport"]    for n in adjusted]) * 3,
        "street_connectivity":        min(1.0, num_intersections / 20),
        "avg_lighting_quality":       np.mean([n["lighting"]     for n in adjusted]),
        "crowd_density":              np.mean([n["crowd"]        for n in adjusted]),
        "weather_visibility":         weather_visibility,
        "hour_of_day":                hour,
        "day_of_week":                0,   # backend can pass real value if available
        "is_holiday":                 0,
        "route_length_km":            distance_km,
        "num_intersections":          num_intersections
    }


# --------------------------------------------------------------------------
# Step 3: ML inference → Freedom Score
# --------------------------------------------------------------------------
def _predict_risk(features: dict) -> float:
    row       = pd.DataFrame([{k: features[k] for k in FEATURE_ORDER}])
    scaled    = preprocessor.transform(row)
    risk_prob = float(model.predict_proba(scaled)[0][1])
    return risk_prob


def _freedom_score(risk_prob: float, distance_km: float) -> float:
    distance_penalty = 1 + (distance_km - 2) * 0.03   # small penalty per extra km
    raw = (1 - risk_prob) * 100
    score = raw / max(distance_penalty, 1.0)
    return round(min(100, max(0, score)), 1)


# --------------------------------------------------------------------------
# Step 4: Explanation builder
# --------------------------------------------------------------------------
def _explain(features: dict, score: float, route_type: str) -> str:
    lighting_label = "Excellent" if features["avg_lighting_quality"] > 75 else \
                     "Moderate"  if features["avg_lighting_quality"] > 40 else "Poor"
    crowd_label    = "High"      if features["crowd_density"] > 70 else \
                     "Moderate"  if features["crowd_density"] > 30 else "Low"
    risk_label     = "Low"       if score >= 70 else \
                     "Moderate"  if score >= 45 else "High"
    emoji          = "🟢" if score >= 70 else "🟡" if score >= 45 else "🔴"

    return (f"{emoji} Mobility Freedom Score: {score}/100 — "
            f"Lighting: {lighting_label} | Crowd: {crowd_label} | ML Risk: {risk_label}")


# --------------------------------------------------------------------------
# MAIN FUNCTION — backend calls this from POST /api/v1/routes/compare
# --------------------------------------------------------------------------
def compare_routes(source_id: str, dest_id: str,
                   hour_of_day: int, weather_visibility: float = 10.0) -> dict:
    """
    Input:
        source_id          : e.g. "N1"
        dest_id            : e.g. "N5"
        hour_of_day        : 0-23
        weather_visibility : 10=clear, 5=rain, 2=fog

    Output:
        {
            "routes": [ ...scored route objects ],
            "recommended": { ...the safest route },
            "source": { node info },
            "dest":   { node info }
        }
    """
    if source_id == dest_id:
        return {"error": "Source and destination cannot be the same."}

    found = [r for r in ROUTES
             if r["source_id"] == source_id and r["dest_id"] == dest_id]

    if not found:
        return {"error": "No routes available for this zone yet."}

    scored_routes = []
    for route in found:
        features  = _aggregate_route_features(
            route["path_nodes"], hour_of_day,
            weather_visibility, route["distance_km"], route["num_intersections"]
        )
        risk_prob = _predict_risk(features)
        score     = _freedom_score(risk_prob, route["distance_km"])

        scored_routes.append({
            "route_id":    route["route_id"],
            "name":        route["name"],
            "route_type":  route["route_type"],
            "distance_km": route["distance_km"],
            "polyline":    route["polyline"],
            "score":       score,
            "risk_level":  "low" if score >= 70 else "medium" if score >= 45 else "high",
            "explanation": _explain(features, score, route["route_type"]),
            "components": {
                "lighting":    round(features["avg_lighting_quality"], 1),
                "crowd":       round(features["crowd_density"], 1),
                "crime":       round(features["crime_density"] * 100, 1),
                "transit":     round(features["transit_lines_nearby"], 1)
            }
        })

    recommended = max(scored_routes, key=lambda x: x["score"])

    return {
        "routes":      scored_routes,
        "recommended": recommended,
        "source":      NODES.get(source_id, {}),
        "dest":        NODES.get(dest_id, {})
    }


# --------------------------------------------------------------------------
# Sanity check
# --------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== 2 PM (safe time) ===")
    result = compare_routes("N1", "N5", hour_of_day=14, weather_visibility=10)
    for r in result["routes"]:
        print(f"  {r['name']}: {r['score']} | {r['risk_level']}")
    print(f" Recommended: {result['recommended']['name']}")

    print("\n=== 11 PM (risky time) ===")
    result2 = compare_routes("N1", "N5", hour_of_day=23, weather_visibility=10)
    for r in result2["routes"]:
        print(f"  {r['name']}: {r['score']} | {r['risk_level']}")
    print(f"  Recommended: {result2['recommended']['name']}")

    print("\n=== 11 PM + Fog ===")
    result3 = compare_routes("N1", "N5", hour_of_day=23, weather_visibility=2)
    for r in result3["routes"]:
        print(f"  {r['name']}: {r['score']} | {r['risk_level']}")
    print(f"  Recommended: {result3['recommended']['name']}")
