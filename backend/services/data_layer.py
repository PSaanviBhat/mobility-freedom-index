import json
import logging
from datetime import datetime
from pathlib import Path

import joblib
import networkx as nx

from config import (
    BACKEND_MODELS_DIR,
    DATA_DIR,
    DEFAULT_FEATURE_SCHEMA_VERSION,
    DEFAULT_MODEL_VERSION,
    DEFAULT_SCORING_POLICY_VERSION,
    ML_ARTIFACTS_DIR,
)

logger = logging.getLogger(__name__)

MODEL_PATHS = [
    ML_ARTIFACTS_DIR / "best_risk_model_pipeline.joblib",
    BACKEND_MODELS_DIR / "best_risk_model_pipeline.joblib",
]
THRESHOLD_PATHS = [
    ML_ARTIFACTS_DIR / "threshold_config.joblib",
    BACKEND_MODELS_DIR / "threshold_config.joblib",
]
GRAPH_PATH = DATA_DIR / "city_graph.json"

ML_PIPELINE = None
CITY_GRAPH = nx.DiGraph()
ROUTE_CATALOG = []
MODEL_PATH_IN_USE = None

# integrity metadata
MODEL_VERSION = DEFAULT_MODEL_VERSION
FEATURE_SCHEMA_VERSION = DEFAULT_FEATURE_SCHEMA_VERSION
SCORING_POLICY_VERSION = DEFAULT_SCORING_POLICY_VERSION

# threshold for high risk
SAFETY_THRESHOLD = 0.50
FEATURE_COLUMNS = [
    "crime_density",
    "crime_trend",
    "crime_type_violence_ratio",
    "transit_lines_nearby",
    "transit_frequency",
    "street_connectivity",
    "avg_lighting_quality",
    "crowd_density",
    "weather_visibility",
    "hour_of_day",
    "day_of_week",
    "is_holiday",
    "route_length_km",
    "num_intersections",
]


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def load_ml_pipeline():
    global ML_PIPELINE, MODEL_PATH_IN_USE, MODEL_VERSION, FEATURE_COLUMNS
    try:
        model_path = _first_existing(MODEL_PATHS)
        if model_path:
            ML_PIPELINE = joblib.load(model_path)
            MODEL_PATH_IN_USE = model_path
            MODEL_VERSION = model_path.name
            logger.info("Loaded ML pipeline from %s", model_path)
            preprocessor = getattr(ML_PIPELINE, "named_steps", {}).get("preprocessor")
            feature_names = getattr(preprocessor, "feature_names_in_", None)
            if feature_names is not None:
                FEATURE_COLUMNS = list(feature_names)
        else:
            logger.warning("ML model missing. Checked: %s", MODEL_PATHS)
    except Exception as e:
        logger.exception("Failed loading ML pipeline: %s", e)
        ML_PIPELINE = None


def load_city_graph():
    try:
        with GRAPH_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)

        for node in data.get("nodes", []):
            CITY_GRAPH.add_node(
                node["node_id"],
                name=node.get("name"),
                lat=node.get("lat"),
                lng=node.get("lng"),
                base_crime_density=node.get("base_crime_density", 0.0),
                base_lighting=node.get("base_lighting", 50.0),
                base_crowd=node.get("base_crowd", 50.0),
                crime_trend=node.get("crime_trend", 0.0),
                violence_ratio=node.get("violence_ratio", 0.0),
                transport_availability=node.get("transport_availability", 0.0),
            )

        for route in data.get("routes", []):
            ROUTE_CATALOG.append(route)
            CITY_GRAPH.add_edge(
                route["source_id"],
                route["dest_id"],
                distance=route.get("distance_km", 1.0),
                name=route.get("name", "Unnamed"),
                path_nodes=route.get("path_nodes", [route["source_id"], route["dest_id"]]),
                route_id=route.get("route_id"),
            )

        logger.info("Graph loaded: nodes=%s, edges=%s", CITY_GRAPH.number_of_nodes(), CITY_GRAPH.number_of_edges())
    except Exception as e:
        logger.exception("Failed loading city graph: %s", e)


def load_threshold_config():
    global SAFETY_THRESHOLD
    try:
        threshold_path = _first_existing(THRESHOLD_PATHS)
        if not threshold_path:
            return
        threshold_config = joblib.load(threshold_path)
        safety_threshold = threshold_config.get("safety_first_threshold")
        if isinstance(safety_threshold, (int, float)) and 0 < float(safety_threshold) < 1:
            SAFETY_THRESHOLD = float(safety_threshold)
            logger.info("Loaded safety threshold %.4f from %s", SAFETY_THRESHOLD, threshold_path)
    except Exception as e:
        logger.exception("Failed loading threshold config: %s", e)


# -------- backward-compatible helpers needed by score.py ----------
async def get_weather_visibility(lat: float, lng: float) -> float:
    # Deterministic placeholder until a live weather provider is wired in.
    return 7.0

def get_time_features(timestamp: str) -> dict:
    normalized = timestamp.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    return {
        "hour_of_day": dt.hour,
        "day_of_week": dt.weekday(),
        "is_weekend": dt.weekday() >= 5,
        "is_night": dt.hour < 6 or dt.hour > 21,
    }

def get_mock_crime_index(lat: float, lng: float) -> float:
    lat_offset = abs(lat - 12.9716)
    lng_offset = abs(lng - 77.5946)
    return max(0.05, min(0.95, 0.18 + (lat_offset * 8.0) + (lng_offset * 5.0)))


load_ml_pipeline()
load_city_graph()
load_threshold_config()
