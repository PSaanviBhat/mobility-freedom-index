import joblib
import pandas as pd
import numpy as np

# Load the exact artifacts you already generated from your notebooks
model_pipeline = joblib.load("artifacts/best_risk_model_pipeline.joblib")

# The threshold you found in threshold-tuning.ipynb (e.g., 0.07)
SAFETY_THRESHOLD = 0.07 

def aggregate_route_features(route_nodes: list, travel_time: int, visibility: float) -> dict:
    """
    Translates the new graph-based node list into the 14 features your ML model expects.
    """
    # 1. Aggregate static features from the nodes
    avg_lighting = sum(n["base_lighting"] for n in route_nodes) / len(route_nodes)
    avg_crowd = sum(n["base_crowd"] for n in route_nodes) / len(route_nodes)
    avg_transit_freq = sum(n["transport_availability"] for n in route_nodes) / len(route_nodes)
    
    # For crime, we take the WORST node on the route, not the average.
    max_crime = max(n["base_crime_density"] for n in route_nodes)
    max_violence = max(n["violence_ratio"] for n in route_nodes)
    
    # 2. Apply dynamic time-of-day logic (Example)
    is_night = 1 if (travel_time >= 20 or travel_time <= 5) else 0
    actual_lighting = avg_lighting if is_night else 100
    actual_crowd = avg_crowd * 0.2 if is_night else avg_crowd

    # 3. Construct the exact dictionary your ML model was trained on
    return {
        "crime_density": max_crime,
        "crime_trend": 0.0, # Neutral baseline for demo
        "crime_type_violence_ratio": max_violence,
        "transit_lines_nearby": len(route_nodes), 
        "transit_frequency": avg_transit_freq * 5, # Scale to minutes
        "street_connectivity": 0.8, # Static assumption for demo
        "avg_lighting_quality": actual_lighting,
        "crowd_density": actual_crowd,
        "weather_visibility": visibility,
        "hour_of_day": travel_time,
        "day_of_week": 5, # Assume Friday for demo
        "is_holiday": 0,
        "route_length_km": len(route_nodes) * 1.2, # Rough estimate based on node count
        "num_intersections": len(route_nodes) * 4
    }

def calculate_route_risk(route_nodes: list, travel_time: int, visibility: float):
    """
    Calls your existing XGBoost model using the new aggregated features.
    """
    # 1. Get the features
    features = aggregate_route_features(route_nodes, travel_time, visibility)
    
    # 2. Convert to DataFrame (just like in the notebook)
    df = pd.DataFrame([features])
    
    # 3. Predict using the unchanged XGBoost pipeline
    prob = float(model_pipeline.predict_proba(df)[0, 1])
    
    # 4. Apply your tuned threshold
    is_risky = int(prob >= SAFETY_THRESHOLD)
    
    # 5. Calculate Freedom Score (100 - risk penalty)
    risk_penalty = prob * 100 
    freedom_score = max(0, min(100, 100 - risk_penalty))
    
    return {
        "mobility_freedom_score": round(freedom_score, 1),
        "risk_probability": round(prob, 4),
        "is_high_risk": bool(is_risky),
        "features_used": features # Good for debugging or showing on frontend
    }