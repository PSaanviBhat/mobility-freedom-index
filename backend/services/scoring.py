"""
services/scoring.py  — FINAL VERSION
======================================
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import joblib
import json
import numpy as np
import pandas as pd
from pathlib import Path

# --------------------------------------------------------------------------
# Load artifacts once at startup
# --------------------------------------------------------------------------
BASE_DIR     = Path(__file__).parent.parent
model        = joblib.load(BASE_DIR / "ml_models" / "mobility_freedom_model.joblib")
preprocessor = joblib.load(BASE_DIR / "ml_models" / "preprocessor.joblib")

with open(BASE_DIR / "data" / "city_graph.json") as f:
    _graph = json.load(f)
    NODES  = {n["node_id"]: n for n in _graph["nodes"]}
    ROUTES = _graph["routes"]

FEATURE_ORDER = [
    'crime_density', 'crime_trend', 'crime_type_violence_ratio',
    'transit_lines_nearby', 'transit_frequency', 'street_connectivity',
    'avg_lighting_quality', 'crowd_density', 'weather_visibility',
    'hour_of_day', 'day_of_week', 'is_holiday',
    'route_length_km', 'num_intersections'
]

_HOUR_RISK = {
    0:1.6, 1:1.6, 2:1.6, 3:1.6, 4:1.5,
    5:0.8, 6:0.75, 7:0.7, 8:0.65, 9:0.6,
    10:0.6, 11:0.6, 12:0.6, 13:0.6, 14:0.6,
    15:0.65, 16:0.7, 17:0.75, 18:0.8, 19:0.9,
    20:1.1, 21:1.2, 22:1.4, 23:1.5
}

# --------------------------------------------------------------------------
# Step 1: Time-based feature adjustment per node
# --------------------------------------------------------------------------
def _apply_time_adjustments(node: dict, hour: int) -> dict:
    if 7 <= hour <= 10 or 17 <= hour <= 20:
        crowd = node["base_crowd"] * 1.2
    elif 0 <= hour <= 5:
        crowd = node["base_crowd"] * 0.1
    else:
        crowd = node["base_crowd"] * 0.8

    lighting = 100.0 if 6 < hour < 18 else node["base_lighting"]

    return {
        "crime_density":  node["base_crime_density"],
        "crime_trend":    node["crime_trend"],
        "violence_ratio": node["violence_ratio"],
        "lighting":       lighting,
        "crowd":          min(100, crowd),
        "transport":      node["transport_availability"]
    }


# --------------------------------------------------------------------------
# Step 2: Aggregate node list into one ML feature vector
# --------------------------------------------------------------------------
def _aggregate_route_features(path_nodes: list, hour: int,
                               weather_visibility: float,
                               distance_km: float,
                               num_intersections: int) -> dict:
    adjusted = [_apply_time_adjustments(NODES[nid], hour) for nid in path_nodes]

    return {
        "crime_density":             max(n["crime_density"]  for n in adjusted),
        "crime_trend":               float(np.mean([n["crime_trend"]  for n in adjusted])),
        "crime_type_violence_ratio": max(n["violence_ratio"] for n in adjusted),
        "transit_lines_nearby":      float(np.mean([n["transport"]    for n in adjusted])) / 10,
        "transit_frequency":         float(np.mean([n["transport"]    for n in adjusted])) * 3 / 10,
        "street_connectivity":       min(1.0, num_intersections / 20),
        "avg_lighting_quality":      float(np.mean([n["lighting"]     for n in adjusted])) / 100,
        "crowd_density":             float(np.mean([n["crowd"]        for n in adjusted])) / 100,
        "weather_visibility":        weather_visibility,
        "hour_of_day":               hour,
        "day_of_week":               0,
        "is_holiday":                0,
        "route_length_km":           distance_km,
        "num_intersections":         num_intersections
    }


# --------------------------------------------------------------------------
# Step 3: ML inference
# --------------------------------------------------------------------------
def _predict_risk(features: dict) -> float:
    row = pd.DataFrame([{k: features[k] for k in FEATURE_ORDER}])
    return float(model.predict_proba(row)[0][1])


def _freedom_score(risk_prob: float, distance_km: float) -> float:
    distance_penalty = 1 + (distance_km - 2) * 0.03
    score = ((1 - risk_prob) * 100) / max(distance_penalty, 1.0)
    return round(min(100, max(0, score)), 1)


# --------------------------------------------------------------------------
# Step 4: Explanation builder
# --------------------------------------------------------------------------
def _explain(features: dict, score: float) -> str:
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
# compare_routes — called from POST /api/routes/compare
# --------------------------------------------------------------------------
def compare_routes(source_id: str, dest_id: str,
                   hour_of_day: int,
                   weather_visibility: float = 10.0) -> dict:
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
        risk_prob  = _predict_risk(features)
        base_score = _freedom_score(risk_prob, route["distance_km"])

        # Apply time-of-day multiplier for clear day/night differentiation
        time_multiplier = _HOUR_RISK[hour_of_day]
        score = round(min(100, max(0, base_score / time_multiplier)), 1)

        scored_routes.append({
            "route_id":    route["route_id"],
            "name":        route["name"],
            "route_type":  route["route_type"],
            "distance_km": route["distance_km"],
            "polyline":    route["polyline"],
            "score":       score,
            "risk_level":  "low" if score >= 85 else "medium" if score >= 60 else "high",
            "explanation": _explain(features, score),
            "components": {
                "lighting": round(features["avg_lighting_quality"], 1),
                "crowd":    round(features["crowd_density"], 1),
                "crime":    round(features["crime_density"] * 100, 1),
                "transit":  round(features["transit_lines_nearby"], 1)
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
# compute_mobility_score — handles both old and new feature formats
# --------------------------------------------------------------------------
def compute_mobility_score(features: dict) -> dict:
    if "lighting" in features and "transport_availability" in features:
        ml_features = {
            "crime_density":             features.get("crime_density", 0.3),
            "crime_trend":               features.get("crime_trend", 0.0),
            "crime_type_violence_ratio": features.get("violence_ratio", 0.2),
            "transit_lines_nearby":      features.get("transport_availability", 5.0),
            "transit_frequency":         features.get("transport_availability", 5.0) * 3,
            "street_connectivity":       0.5,
            "avg_lighting_quality":      features.get("lighting", 70.0),
            "crowd_density":             features.get("crowd_density", 50.0),
            "weather_visibility":        features.get("weather_visibility", 10.0),
            "hour_of_day":               features.get("hour_of_day", 12),
            "day_of_week":               0,
            "is_holiday":                0,
            "route_length_km":           features.get("route_length_km", 4.0),
            "num_intersections":         features.get("num_intersections", 10),
        }
    else:
        ml_features = {
            "crime_density":             features.get("crime_index", 0.3),
            "crime_trend":               0.0,
            "crime_type_violence_ratio": features.get("crime_index", 0.3) * 0.5,
            "transit_lines_nearby":      features.get("transit_access", 0.5) * 10,
            "transit_frequency":         features.get("transit_access", 0.5) * 30,
            "street_connectivity":       0.5,
            "avg_lighting_quality":      features.get("lighting_index", 0.7) * 100,
            "crowd_density":             features.get("crowd_density", 0.4) * 100,
            "weather_visibility":        features.get("weather_visibility", 10.0),
            "hour_of_day":               features.get("hour", 12),
            "day_of_week":               0,
            "is_holiday":                0,
            "route_length_km":           4.0,
            "num_intersections":         10,
        }

    risk_prob = _predict_risk(ml_features)
    hour      = int(ml_features["hour_of_day"])
    time_adj  = (1.0 - _HOUR_RISK[hour]) * 15
    score     = round(min(100, max(0, (1 - risk_prob) * 100 + time_adj)), 1)

    return {
        "mobility_freedom_score": score,
        "safety_score":           round(max(0, 100 - ml_features["crime_density"] * 100), 1),
        "accessibility_score":    round(min(100, ml_features["transit_lines_nearby"] * 10), 1),
        "visibility_score":       round(ml_features["avg_lighting_quality"], 1),
    }


# --------------------------------------------------------------------------
# Sanity check — run: python services/scoring.py
# --------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 55)
    print("TEST 1: compare_routes() — 2 PM (safe)")
    print("=" * 55)
    r = compare_routes("N1", "N4", hour_of_day=14)
    for route in r["routes"]:
        print(f"  {route['name']}: {route['score']} | {route['risk_level']}")
    print(f"  → Recommended: {r['recommended']['name']}")

    print("\n" + "=" * 55)
    print("TEST 2: compare_routes() — 11 PM (risky)")
    print("=" * 55)
    r2 = compare_routes("N1", "N4", hour_of_day=23)
    for route in r2["routes"]:
        print(f"  {route['name']}: {route['score']} | {route['risk_level']}")
    print(f"  → Recommended: {r2['recommended']['name']}")