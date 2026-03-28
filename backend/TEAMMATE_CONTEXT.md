# Freedom Map — Teammate Integration Guide
> Backend is live and tested. Read this before touching any code.

---

## Quick Links
- **Swagger UI (API Docs):** http://127.0.0.1:8000/docs
- **Base URL:** http://127.0.0.1:8000
- **GitHub Repo:** [add link here]

---

## Project Structure
```
freedom-map-backend/
├── main.py                  # Entry point — do not touch
├── routers/
│   ├── score.py             # POST /api/score/ — main scoring endpoint
│   ├── routes.py            # POST /api/routes/ — route recommendation
│   └── heatmap.py           # GET /api/heatmap/bengaluru — zone data
├── models/
│   └── schemas.py           # Shared data models (inputs/outputs)
├── services/
│   ├── scoring.py           # ← ML TEAM: your integration point
│   ├── data_layer.py        # Data fetching (GPS, weather, crime)
│   └── recommendation.py   # Natural language tip generation
├── config.py                # API keys via .env
└── .env                     # Never commit this — use .env.example
```

---

## For the ML Team

### Your only file: `services/scoring.py`

The function signature is fixed — do not rename it or change the return keys.

```python
def compute_mobility_score(features: dict) -> dict:
    """
    INPUT — features dict will always contain:
        hour          (int)   : 0–23
        is_night      (bool)  : True if hour < 6 or hour > 21
        is_weekend    (bool)  : True if Saturday/Sunday
        lighting_index (float): 0–1, from OpenWeatherMap (1 = bright)
        crime_index   (float) : 0–1, from dataset (0 = safe, 1 = dangerous)
        crowd_density (float) : 0–1 proxy (currently mocked at 0.4)
        transit_access (float): 0–1 proxy (currently mocked at 0.6)

    OUTPUT — return dict must have exactly these keys:
        mobility_freedom_score (float): 0–100, overall score
        safety_score           (float): 0–100
        accessibility_score    (float): 0–100
        visibility_score       (float): 0–100
    """
    # Replace this stub with your model
    ...
```

### How to plug in your model

```python
import joblib  # or torch, sklearn, etc.

model = joblib.load("your_model.pkl")  # load once at top of file

def compute_mobility_score(features: dict) -> dict:
    input_vector = [
        features["hour"],
        features["lighting_index"],
        features["crime_index"],
        features["crowd_density"],
        features["transit_access"],
    ]
    mfs = model.predict([input_vector])[0]
    
    # derive sub-scores however your model outputs them
    return {
        "mobility_freedom_score": round(float(mfs), 2),
        "safety_score": round(float(features["crime_index"] * 100), 2),
        "accessibility_score": round(float(features["transit_access"] * 100), 2),
        "visibility_score": round(float(features["lighting_index"] * 100), 2),
    }
```

### Git workflow
```bash
git checkout feat/ml-scoring   # work on your branch
# make changes to services/scoring.py only
git add services/scoring.py
git commit -m "feat: integrate trained mobility scoring model"
git push
# then open a PR into dev
```

---

## For the Frontend Team

### Running the backend locally
```bash
cd freedom-map-backend
venv\Scripts\activate       # Windows
pip install -r requirements.txt
uvicorn main:app --reload
# API is now live at http://127.0.0.1:8000
```

### Endpoints

#### 1. Get Mobility Score
```
POST /api/score/
Content-Type: application/json
```
Request:
```json
{
  "lat": 12.9716,
  "lng": 77.5946,
  "timestamp": "2025-03-28T21:00:00"
}
```
Response:
```json
{
  "lat": 12.9716,
  "lng": 77.5946,
  "mobility_freedom_score": 71.5,
  "safety_score": 75.0,
  "accessibility_score": 60.0,
  "visibility_score": 80.0,
  "risk_level": "low",
  "recommendation": "This zone looks relatively safe. Stay aware of your surroundings."
}
```
`risk_level` is always one of: `"low"` | `"medium"` | `"high"`

---

#### 2. Get Heatmap Data (for Leaflet/Mapbox overlay)
```
GET /api/heatmap/bengaluru
```
Response:
```json
[
  { "lat": 12.9716, "lng": 77.5946, "score": 72.0, "zone_type": "freedom" },
  { "lat": 12.9352, "lng": 77.6245, "score": 38.0, "zone_type": "constraint" }
]
```
`zone_type` is always: `"freedom"` (score > 65) or `"constraint"` (score ≤ 65)

Use `score` to set heatmap intensity in Leaflet. Color suggestion:
- Green (`#22c55e`) → freedom zones (score > 65)
- Yellow (`#eab308`) → medium zones (score 40–65)  
- Red (`#ef4444`) → constraint zones (score < 40)

---

#### 3. Get Safe Route
```
POST /api/routes/
Content-Type: application/json
```
Request:
```json
{
  "origin_lat": 12.9716,
  "origin_lng": 77.5946,
  "dest_lat": 12.9352,
  "dest_lng": 77.6245,
  "timestamp": "2025-03-28T21:00:00"
}
```

---

### Calling the API from React

```javascript
// Get mobility score for a location
const getMobilityScore = async (lat, lng) => {
  const response = await fetch("http://127.0.0.1:8000/api/score/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      lat,
      lng,
      timestamp: new Date().toISOString().slice(0, 19)
    })
  });
  return await response.json();
};

// Get heatmap zones
const getHeatmapData = async () => {
  const response = await fetch("http://127.0.0.1:8000/api/heatmap/bengaluru");
  return await response.json();
};
```

### CORS
CORS is already enabled for all origins — no proxy setup needed during the hackathon.

---

## Shared Data Types (reference)

| Field | Type | Range | Notes |
|---|---|---|---|
| lat / lng | float | valid coords | WGS84 |
| timestamp | string | ISO 8601 | e.g. `"2025-03-28T21:00:00"` |
| mobility_freedom_score | float | 0–100 | higher = safer |
| risk_level | string | low/medium/high | derived from MFS |
| zone_type | string | freedom/constraint | for heatmap coloring |

---

## Environment Variables (.env)
```
OPENWEATHER_API_KEY=       # get free key at openweathermap.org
GOOGLE_MAPS_API_KEY=       # for routes integration
GROQ_API_KEY=              # for LLaMA-3 natural language tips
```
Copy `.env.example` → `.env` and fill in your keys. Never commit `.env`.

---

## Questions?
Check Swagger UI first: **http://127.0.0.1:8000/docs** — every endpoint is interactable there.
