from datetime import datetime

OPENWEATHER_API_KEY = None  # add key later

async def get_weather_visibility(lat: float, lng: float) -> float:
    return 0.7  # mock until API key added

def get_time_features(timestamp: str) -> dict:
    dt = datetime.fromisoformat(timestamp)
    return {
        "hour": dt.hour,
        "is_weekend": dt.weekday() >= 5,
        "is_night": dt.hour < 6 or dt.hour > 21,
    }

def get_mock_crime_index(lat: float, lng: float) -> float:
    return 0.3