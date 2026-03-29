import pandas as pd
import logging
from .data_layer import ML_PIPELINE, SAFETY_THRESHOLD, CITY_GRAPH

logger = logging.getLogger(__name__)

# THE SINGLE SOURCE OF TRUTH:
# This exact order matches your model.ipynb and preprocessing.ipynb generation.
UNIFORM_FEATURE_COLUMNS = [
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
    "num_intersections"
]

def aggregate_route_features(path_nodes: list, travel_time: int, visibility: float, actual_distance: float) -> pd.DataFrame:
    """
    Translates route nodes into a perfectly formatted, typed DataFrame for XGBoost.
    """
    if not path_nodes:
        raise ValueError("Path nodes list cannot be empty.")

    total_lighting = 0
    total_crowd = 0
    total_transit = 0
    max_crime = 0.0
    max_violence = 0.0

    for node_id in path_nodes:
        node = CITY_GRAPH.nodes.get(node_id, {})
        
        total_lighting += node.get("base_lighting", 50)
        total_crowd += node.get("base_crowd", 50)
        total_transit += node.get("transport_availability", 0)
        
        crime = node.get("base_crime_density", 0.0)
        if crime > max_crime:
            max_crime = crime
            
        violence = node.get("violence_ratio", 0.0)
        if violence > max_violence:
            max_violence = violence

    num_nodes = len(path_nodes)
    avg_lighting = total_lighting / num_nodes
    avg_crowd = total_crowd / num_nodes
    avg_transit_freq = total_transit / num_nodes

    is_night = 1 if (travel_time >= 20 or travel_time <= 5) else 0
    actual_lighting = avg_lighting if is_night else 100
    actual_crowd = avg_crowd * 0.2 if is_night else avg_crowd

    # Build the dictionary with strict type-casting to prevent XGBoost ValueError
    features_dict = {
        "crime_density": float(max_crime),
        "crime_trend": 0.0, 
        "crime_type_violence_ratio": float(max_violence),
        "transit_lines_nearby": int(num_nodes), 
        "transit_frequency": float(avg_transit_freq * 5), 
        "street_connectivity": 0.8, 
        "avg_lighting_quality": float(actual_lighting),
        "crowd_density": float(actual_crowd),
        "weather_visibility": float(visibility),
        "hour_of_day": int(travel_time),
        "day_of_week": 5, 
        "is_holiday": 0,
        "route_length_km": float(actual_distance), 
        "num_intersections": int(max(0, num_nodes - 2))
    }
    
    # Ensure the DataFrame is created first, THEN reindexed to the strict order
    df = pd.DataFrame([features_dict])
    
    # This guarantees the columns are in the exact order the model expects
    df = df.reindex(columns=UNIFORM_FEATURE_COLUMNS)
    
    return df

def calculate_route_risk(path_nodes: list, travel_time: int, visibility: float, actual_distance: float):
    if ML_PIPELINE is None:
        logger.error("ML Pipeline is not loaded. Defaulting to maximum risk.")
        return 0.0, 1.0, True

    try:
        feature_df = aggregate_route_features(path_nodes, travel_time, visibility, actual_distance)
        
        # Inference using the perfectly aligned DataFrame
        prob = float(ML_PIPELINE.predict_proba(feature_df)[0, 1])
        
        is_risky = int(prob >= SAFETY_THRESHOLD)
        risk_penalty = prob * 100 
        freedom_score = max(0.0, min(100.0, 100.0 - risk_penalty))
        
        return freedom_score, prob, bool(is_risky)

    except Exception as e:
        logger.error(f"ML Prediction failed: {str(e)}")
        raise e