import os
import json
import joblib
import networkx as nx
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Directory & Path Configuration ---
# CURRENT_DIR is backend/services/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# BACKEND_DIR is backend/ (One level up)
BACKEND_DIR = os.path.dirname(CURRENT_DIR)

# --- Update these lines in services/data_layer.py ---

# Change ARTIFACTS_DIR to MODELS_DIR
MODELS_DIR = os.path.join(BACKEND_DIR, "models")
DATA_DIR = os.path.join(BACKEND_DIR, "data")

# Update the filename to match your actual file
MODEL_PATH = os.path.join(MODELS_DIR, "best_risk_model_pipeline.joblib")
GRAPH_PATH = os.path.join(DATA_DIR, "city_graph.json")

# --- ML Artifacts Configuration ---
ML_PIPELINE = None
SAFETY_THRESHOLD = 0.07 

logger.info("Initializing Data Layer...")

# Load ML Model
try:
    if os.path.exists(MODEL_PATH):
        ML_PIPELINE = joblib.load(MODEL_PATH)
        logger.info(f"ML Pipeline successfully loaded from {MODEL_PATH}")
    else:
        logger.error(f"Model file not found at {MODEL_PATH}. ML inference will fail.")
except Exception as e:
    logger.critical(f"Failed to load ML pipeline. Error: {str(e)}")

# --- Graph Memory Management ---
CITY_GRAPH = nx.DiGraph()

# --- Update this section in services/data_layer.py ---

def load_city_graph():
    try:
        with open(GRAPH_PATH, "r") as f:
            data = json.load(f)

        # 1. Load Nodes
        nodes_data = data.get("nodes", [])
        for node in nodes_data:
            CITY_GRAPH.add_node(
                node["node_id"],
                name=node.get("name"),
                lat=node.get("lat"),
                lng=node.get("lng"),
                base_crime_density=node.get("base_crime_density", 0.0),
                base_lighting=node.get("base_lighting", 50),
                base_crowd=node.get("base_crowd", 50),
                # Add these specifically for your ML features
                crime_trend=node.get("crime_trend", 0.0),
                violence_ratio=node.get("violence_ratio", 0.0),
                transport_availability=node.get("transport_availability", 0)
            )

        # 2. Load Edges (MATCHING YOUR JSON KEYS)
        # We use .get("routes") because that is what you named your connections
        routes_data = data.get("routes", []) 
        for route in routes_data:
            CITY_GRAPH.add_edge(
                route["source_id"],  # Changed from "source"
                route["dest_id"],    # Changed from "target"
                distance=route.get("distance_km", 1.0), # Changed from "distance"
                name=route.get("name", "Unnamed Street")
            )

        logger.info(f"Successfully loaded {CITY_GRAPH.number_of_nodes()} nodes and {CITY_GRAPH.number_of_edges()} edges.")

    except Exception as e:
        logger.error(f"Failed to load graph: {e}")

load_city_graph()