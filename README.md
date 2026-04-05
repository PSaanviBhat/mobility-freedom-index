# FreedomMap – Mobility Freedom Index (ML Backend)

FreedomMap is a data-driven Machine Learning backend that computes a **Mobility Freedom Score** for urban routes and locations, representing how safe, accessible, and comfortable they are for women.  
While traditional navigation systems optimize for speed and distance, FreedomMap quantifies often invisible trade-offs by factoring in safety risks, lighting, crowd density, and transit accessibility.

This branch contains the end-to-end ML pipeline for:

- Generating realistic urban mobility data
- Training route risk prediction models
- Tuning decision thresholds for safety-first deployment

---

## Repository Structure

```plaintext
├── artifacts/                           # Serialized models, scalers, and datasets
│   ├── best_risk_model_pipeline.joblib  # Final XGBoost model pipeline
│   ├── preprocessor.joblib              # Scikit-learn ColumnTransformer
│   ├── threshold_config.joblib          # Tuned safety-first thresholds
│   └── *.csv                            # Generated train/test splits
├── preprocessing.ipynb                  # 1. Data generation & preprocessing
├── model.ipynb                          # 2. Model training & evaluation
└── threshold-tuning.ipynb               # 3. Asymmetric error & threshold tuning
```

---

## Data Pipeline Overview

Because hyper-localized, real-time safety and environmental data is difficult to source in a cohesive format, FreedomMap uses a simulation engine to generate realistic urban profiles based on urban-planning and sociological correlations.

### Features Generated

- **Spatial / Environmental**
  - `crime_density`
  - `crime_trend`
  - `crime_type_violence_ratio`
  - `avg_lighting_quality`
  - `weather_visibility`
  - `street_connectivity`
  - `route_length_km`
  - `num_intersections`

- **Temporal / Social**
  - `hour_of_day`
  - `day_of_week`
  - `is_holiday`
  - `crowd_density`

- **Transit**
  - `transit_lines_nearby`
  - `transit_frequency`

- **Target**
  - `risk` (binary `0/1`) generated using a probabilistic noise model to simulate real-world uncertainty and edge cases.

---

## Machine Learning Workflow

### 1) `preprocessing.ipynb`

- Synthesizes dataset with realistic correlations (for example, nighttime with lower lighting, higher transit frequency with increased crowd density).
- Injects a **15% high-risk baseline** to reduce severe class imbalance.
- Builds a Scikit-learn `ColumnTransformer` with `StandardScaler`.
- Performs an **80/20 stratified train/test split**.
- Exports datasets and preprocessors to `artifacts/`.

### 2) `model.ipynb`

- Trains and evaluates:
  - Baseline **Logistic Regression**
  - Advanced **XGBoost Classifier**
- Uses `scale_pos_weight` and monitors boosting rounds to optimize log loss and control overfitting.
- Evaluates feature importance (Crime Density, Time of Day, and Lighting as top predictors).
- Packages the winning model (XGBoost) with preprocessing into a unified Scikit-learn `Pipeline` for deployment.

### 3) `threshold-tuning.ipynb`

- Optimizes for asymmetric error cost:
  - **False Negative** (dangerous route predicted safe) is high-cost.
  - **False Positive** (safe route predicted dangerous) is lower-cost.
- Evaluates ROC and Precision-Recall behavior (**AUC ~0.93**).
- Tunes decision threshold from default `0.5` to a **Safety-First Threshold**.
- Prioritizes high recall (detecting >98% of threats) while maintaining acceptable false positives.

---

## Installation and Setup

1. Clone the repository and move into the ML project directory.
2. Install dependencies:

```bash
pip install pandas numpy scikit-learn xgboost matplotlib joblib
```

3. Run notebooks in order:

1. `preprocessing.ipynb`
2. `model.ipynb`
3. `threshold-tuning.ipynb`

This sequence will generate all required local outputs in the `artifacts/` folder.

---

## Artifacts Produced

- `artifacts/best_risk_model_pipeline.joblib`
- `artifacts/preprocessor.joblib`
- `artifacts/threshold_config.joblib`
- Train/test split CSV files in `artifacts/`

---

## API Integration Ready

The pipeline exports a `predict_with_custom_threshold` function intended for direct integration into a FastAPI backend.

Given a route feature payload (JSON), it returns:

- `risk_probability`: Raw model probability (`0.0 - 1.0`)
- `risk_label`: Binary decision (`Safe` / `Risk`) using the tuned threshold
- `risk_multiplier`: Scaled routing penalty (`0.7 - 1.3`) used by the frontend A* routing engine to compute the final Mobility Freedom Score

---

## Safety-First Modeling Principle

FreedomMap is intentionally optimized for user safety, not only aggregate accuracy.  
Threshold tuning is designed to minimize dangerous misses (false negatives), accepting moderate over-warning when necessary for safer route recommendations.

---

## Suggested Next Steps

- Replace or augment simulated data with validated municipal/open-data feeds
- Add geospatial context features (POI categories, CCTV presence, street activity proxies)
- Implement model monitoring and threshold recalibration in production
- Periodically retrain with fresh data to account for temporal drift
