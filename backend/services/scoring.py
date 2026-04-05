import logging

import pandas as pd

from .data_layer import CITY_GRAPH, FEATURE_COLUMNS, ML_PIPELINE, SAFETY_THRESHOLD
from .recommendation import build_recommendation

logger = logging.getLogger(__name__)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


def _normalize_ratio(value: float, scale: float) -> float:
    value = float(value)
    if value <= 1.0:
        return _clamp(value, 0.0, 1.0)
    return _clamp(value / scale, 0.0, 1.0)


def _prepare_feature_frame(features_dict: dict) -> pd.DataFrame:
    row = {column: features_dict[column] for column in FEATURE_COLUMNS}
    return pd.DataFrame([row], columns=FEATURE_COLUMNS)


def _fallback_probability(features_dict: dict) -> float:
    crime = _normalize_ratio(features_dict["crime_density"], 1.0)
    lighting_penalty = 1.0 - _normalize_ratio(features_dict["avg_lighting_quality"], 100.0)
    visibility_penalty = 1.0 - _normalize_ratio(features_dict["weather_visibility"], 10.0)
    crowd_penalty = 1.0 - _normalize_ratio(features_dict["crowd_density"], 100.0)
    violence = _normalize_ratio(features_dict["crime_type_violence_ratio"], 1.0)
    night_penalty = 1.0 if int(features_dict["hour_of_day"]) >= 20 or int(features_dict["hour_of_day"]) <= 5 else 0.0
    raw = (
        0.38 * crime
        + 0.18 * lighting_penalty
        + 0.12 * visibility_penalty
        + 0.10 * crowd_penalty
        + 0.12 * violence
        + 0.10 * night_penalty
    )
    return _clamp(raw, 0.0, 1.0)


def aggregate_route_features(path_nodes: list[str], travel_time: int, visibility: float, actual_distance: float) -> pd.DataFrame:
    if not path_nodes:
        raise ValueError("Path nodes list cannot be empty.")

    total_lighting = 0.0
    total_crowd = 0.0
    total_transit = 0.0
    total_crime = 0.0
    total_crime_trend = 0.0
    total_violence = 0.0

    for node_id in path_nodes:
        node = CITY_GRAPH.nodes.get(node_id, {})
        total_lighting += float(node.get("base_lighting", 50.0))
        total_crowd += float(node.get("base_crowd", 50.0))
        total_transit += float(node.get("transport_availability", 0.0))
        total_crime += float(node.get("base_crime_density", 0.0))
        total_crime_trend += float(node.get("crime_trend", 0.0))
        total_violence += float(node.get("violence_ratio", 0.0))

    num_nodes = len(path_nodes)
    is_night = travel_time >= 20 or travel_time <= 5
    avg_lighting = total_lighting / num_nodes
    avg_crowd = total_crowd / num_nodes
    avg_transit = total_transit / num_nodes

    features_dict = {
        "crime_density": round(total_crime / num_nodes, 4),
        "crime_trend": round(total_crime_trend / num_nodes, 4),
        "crime_type_violence_ratio": round(total_violence / num_nodes, 4),
        "transit_lines_nearby": int(round(avg_transit)),
        "transit_frequency": round(avg_transit * 4.0, 2),
        "street_connectivity": round(_clamp((num_nodes - 1) / max(actual_distance, 1.0), 0.1, 1.0), 4),
        "avg_lighting_quality": round(avg_lighting if is_night else min(100.0, avg_lighting + 10.0), 2),
        "crowd_density": round(avg_crowd if not is_night else max(5.0, avg_crowd * 0.65), 2),
        "weather_visibility": round(_clamp(visibility, 0.0, 10.0), 2),
        "hour_of_day": int(travel_time),
        "day_of_week": 5,
        "is_holiday": 0,
        "route_length_km": round(max(actual_distance, 0.1), 3),
        "num_intersections": max(0, num_nodes - 2),
    }
    return _prepare_feature_frame(features_dict)


def predict_risk_probability(feature_frame: pd.DataFrame) -> float:
    if ML_PIPELINE is None:
        return _fallback_probability(feature_frame.iloc[0].to_dict())
    return _clamp(float(ML_PIPELINE.predict_proba(feature_frame)[0, 1]), 0.0, 1.0)


def compute_mobility_score(features: dict) -> dict:
    hour_of_day = int(features.get("hour_of_day", features.get("hour", 12)))
    day_of_week = int(features.get("day_of_week", 5 if features.get("is_weekend") else 2))
    is_holiday = int(bool(features.get("is_holiday", False)))
    crime_density = _clamp(features.get("crime_density", features.get("crime_index", 0.3)), 0.0, 1.0)
    violence_ratio = _clamp(features.get("crime_type_violence_ratio", crime_density * 0.75), 0.0, 1.0)
    lighting_quality = features.get("avg_lighting_quality", features.get("lighting_index", 65.0))
    if float(lighting_quality) <= 1.0:
        lighting_quality = float(lighting_quality) * 100.0
    weather_visibility = features.get("weather_visibility", features.get("lighting_index", 7.0))
    if float(weather_visibility) <= 1.0:
        weather_visibility = float(weather_visibility) * 10.0
    crowd_density = features.get("crowd_density", 45.0)
    if float(crowd_density) <= 1.0:
        crowd_density = float(crowd_density) * 100.0
    transit_access = float(features.get("transit_access", 0.6))

    model_features = {
        "crime_density": round(crime_density, 4),
        "crime_trend": round(float(features.get("crime_trend", 0.05)), 4),
        "crime_type_violence_ratio": round(violence_ratio, 4),
        "transit_lines_nearby": int(round(max(0.0, transit_access * 10.0))),
        "transit_frequency": round(max(0.0, transit_access * 12.0), 2),
        "street_connectivity": round(_clamp(features.get("street_connectivity", 0.7), 0.0, 1.0), 4),
        "avg_lighting_quality": round(_clamp(lighting_quality, 0.0, 100.0), 2),
        "crowd_density": round(_clamp(crowd_density, 0.0, 100.0), 2),
        "weather_visibility": round(_clamp(weather_visibility, 0.0, 10.0), 2),
        "hour_of_day": hour_of_day,
        "day_of_week": day_of_week,
        "is_holiday": is_holiday,
        "route_length_km": round(max(0.2, float(features.get("route_length_km", 1.5))), 3),
        "num_intersections": int(max(0, round(float(features.get("num_intersections", 4))))),
    }

    feature_frame = _prepare_feature_frame(model_features)
    risk_probability = predict_risk_probability(feature_frame)
    safety_score = round(_clamp((1.0 - risk_probability) * 100.0, 0.0, 100.0), 2)
    visibility_score = round(
        _clamp(
            (0.55 * model_features["avg_lighting_quality"]) + (4.5 * model_features["weather_visibility"]),
            0.0,
            100.0,
        ),
        2,
    )
    accessibility_score = round(
        _clamp(
            (model_features["transit_lines_nearby"] * 6.0)
            + (model_features["street_connectivity"] * 25.0)
            + (model_features["crowd_density"] * 0.15),
            0.0,
            100.0,
        ),
        2,
    )
    mobility_freedom_score = round(
        _clamp((0.6 * safety_score) + (0.2 * visibility_score) + (0.2 * accessibility_score), 0.0, 100.0),
        2,
    )

    return {
        "mobility_freedom_score": mobility_freedom_score,
        "safety_score": safety_score,
        "accessibility_score": accessibility_score,
        "visibility_score": visibility_score,
        "risk_probability": round(risk_probability, 6),
        "engine_mode": "ml_pipeline" if ML_PIPELINE is not None else "fallback_rule_based",
        "features": model_features,
    }


def calculate_route_risk(path_nodes: list[str], travel_time: int, visibility: float, actual_distance: float):
    feature_frame = aggregate_route_features(path_nodes, travel_time, visibility, actual_distance)
    probability = predict_risk_probability(feature_frame)
    score = round(_clamp((1.0 - probability) * 100.0, 0.0, 100.0), 2)
    is_risky = bool(probability >= SAFETY_THRESHOLD)
    return score, round(probability, 4), is_risky, feature_frame.iloc[0].to_dict()


def derive_risk_level(mobility_freedom_score: float) -> str:
    score = float(mobility_freedom_score)
    if score >= 70.0:
        return "low"
    if score >= 45.0:
        return "medium"
    return "high"


def get_integrity_meta() -> dict:
    from .data_layer import FEATURE_SCHEMA_VERSION, MODEL_VERSION, SCORING_POLICY_VERSION

    return {
        "model_version": MODEL_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "scoring_policy_version": SCORING_POLICY_VERSION,
    }
