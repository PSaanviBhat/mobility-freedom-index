from fastapi import APIRouter
from models.schemas import LocationInput, MobilityScoreResponse
from services.scoring import compute_mobility_score
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
    risk = "low" if mfs > 65 else "medium" if mfs > 40 else "high"
    tip = generate_recommendation(risk, time_features["is_night"])

    return MobilityScoreResponse(
        lat=location.lat, lng=location.lng,
        recommendation=tip, risk_level=risk,
        **scores
    )

def generate_recommendation(risk: str, is_night: bool) -> str:
    if risk == "high":
        return "This area has elevated risk. Consider a ride-hail or a well-lit alternate route."
    elif is_night:
        return "Lower visibility at this hour. Stick to main roads with active foot traffic."
    return "This zone looks relatively safe. Stay aware of your surroundings."