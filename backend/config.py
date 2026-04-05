from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent
ML_ENGINE_DIR = REPO_ROOT / "ml-engine"
ML_ARTIFACTS_DIR = ML_ENGINE_DIR / "artifacts"
BACKEND_MODELS_DIR = BACKEND_DIR / "models"
DATA_DIR = BACKEND_DIR / "data"

DEFAULT_FEATURE_SCHEMA_VERSION = "v1.0.0"
DEFAULT_SCORING_POLICY_VERSION = "v1.1.0"
DEFAULT_MODEL_VERSION = "best_risk_model_pipeline.joblib"
