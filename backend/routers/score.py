from fastapi import APIRouter
from models.schemas import LocationInput, MobilityScoreResponse
from services.scoring import compute_mobility_score, derive_risk_level, build_recommendation, get_integrity_meta
from services.data_layer import get_weather_visibility, get_time_features, get_mock_crime_index

router = APIRouter()

@router.post("/", response_model=MobilityScoreResponse)
async def get_mobility_score(location: LocationInput):
    time_features = get_time_features(location.timestamp)
    visibility = await get_weather_visibility(location.lat, location.lng)
    crime_index = get_mock_crime_index(location.lat, location.lng)

    features = {
        **time_features,
        "lighting_index": visibility,
        "crime_index": crime_index,
        "crowd_density": 0.4,
        "transit_access": 0.6,
    }

    scores = compute_mobility_score(features)
    mfs = scores["mobility_freedom_score"]
    risk = derive_risk_level(mfs)
    tip = build_recommendation(risk, time_features["is_night"])
    meta = get_integrity_meta()

    return MobilityScoreResponse(
        lat=location.lat,
        lng=location.lng,
        mobility_freedom_score=scores["mobility_freedom_score"],
        safety_score=scores["safety_score"],
        accessibility_score=scores["accessibility_score"],
        visibility_score=scores["visibility_score"],
        risk_probability=scores["risk_probability"],
        risk_level=risk,
        recommendation=tip,
        model_version=meta["model_version"],
        feature_schema_version=meta["feature_schema_version"],
        scoring_policy_version=meta["scoring_policy_version"],
        engine_mode=scores["engine_mode"],
    )