# Mobility Freedom Index

Mobility Freedom Index is a women-focused safety intelligence platform that calculates a route-level **Mobility Freedom Score** using crime, accessibility, visibility, and time-based risk factors. It helps users choose safer travel routes and better travel times through explainable risk scoring, map-based heatmaps, and actionable recommendations.

## Problem

Women often face uncertainty while traveling, especially at night or in low-visibility areas. Existing route planners optimize for time and distance but rarely prioritize personal safety and mobility confidence.

## Solution

Mobility Freedom Index provides:

- Mobility Freedom Score for routes and zones
- Route comparison across fastest, safest, and freedom-optimized options
- Safety heatmap for city regions
- Risk prediction by time of day
- Actionable recommendations to improve travel safety

## Core Features

- Mobility Freedom Score calculation
- Risk prediction module
- Route comparison engine
- Heatmap visualization
- Recommendation engine

## Bonus Features

- Time simulation for the same route at different hours
- Score explanation engine
- Personalized route suggestions

## Tech Stack

### Frontend
- Next.js
- TypeScript
- Mapbox GL JS
- Tailwind CSS
- Shadcn/ui
- Zustand
- React Query

### Backend
- FastAPI
- Pydantic
- SQLAlchemy
- Uvicorn
- HTTPX

### ML/Data
- Python
- Pandas
- NumPy
- Scikit-learn
- XGBoost
- Joblib

### Database
- PostgreSQL
- PostGIS

### Deployment
- Frontend: Vercel
- Backend: Render or Railway
- Database: Supabase


## Mobility Freedom Score

The score is normalized to 0–100.

- Safety
- Accessibility
- Visibility
- Time-based risk

Example weighted formulation:

\[
\text{Score} = 0.40 \cdot \text{Safety} + 0.25 \cdot \text{Accessibility} + 0.20 \cdot \text{Visibility} + 0.15 \cdot \text{TimeRisk}
\]

## Risk Model

The risk engine uses a hybrid approach:

- Rule-based signal logic for explainability
- Machine learning models for probabilistic prediction

Trained models:

- Logistic Regression
- XGBoost

Prediction output:

- `risk_probability`
- `risk_multiplier` in the range `0.7–1.3`

## Data and Labeling

Dataset includes these features:

- crime_density
- crime_trend
- crime_type_violence_ratio
- transit_lines_nearby
- transit_frequency
- street_connectivity
- avg_lighting_quality
- crowd_density
- weather_visibility
- hour_of_day
- day_of_week
- is_holiday
- route_length_km
- num_intersections

Label logic:

- `risk = 1` if `crime_density > 0.7` and `avg_lighting_quality < 40` and `crowd_density < 30` and `hour_of_day > 21`
- Else `risk = 0`

## API Overview

### `POST /api/score`
Calculates Mobility Freedom Score for a route request.

### `POST /api/compare-routes`
Returns route alternatives with score comparison.

### `GET /api/heatmap`
Returns geospatial heatmap layer data.

### `POST /api/predict-risk`
Returns risk probability and risk multiplier for a route-time context.

### `POST /api/recommendations`
Returns actionable safety recommendations.

## ML Workflow

1. Take in dataset
2. Preprocess features
3. Train Logistic Regression and XGBoost
4. Evaluate model accuracy
5. Plot ROC and PR curves
6. Tune threshold for deployment policy
7. Save model and threshold artifacts with Joblib

## Notebooks

### 1) `preprocessing.ipynb`
- Synthetic data generation
- Feature preprocessing
- Artifact creation

### 2) `model.ipynb`
- Model training
- Accuracy comparison
- XGBoost feature importance
- Save and load models
- Prediction functions

### 3) `threshold-tuning.ipynb`
- ROC curve and AUC
- PR curve and average precision
- Threshold tuning
- Save threshold configuration

## Setup

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Mapbox API key


## Demo Flow

1. Open safety heatmap
2. Enter source and destination
3. Compare fastest, safest, and freedom-optimized routes
4. Show score breakdown and explanation
5. Simulate time-of-day changes
6. Present recommendations with measurable safety impact

## Team Roles

- Frontend Engineer
- Backend Engineer
- ML/Data Engineer
- Integration and UX Engineer

## Success Criteria

- Working end-to-end web application
- Explainable Mobility Freedom Score
- Functional risk prediction API
- Interactive map and route comparison
- Clear demo-ready narrative for judges

## Future Scope

- Real-time crowdsourced incident reporting
- User personalization profiles
- City-level safety trend analytics
- Integration with transit and ride-hailing platforms
- Native mobile app

## License

MIT License
