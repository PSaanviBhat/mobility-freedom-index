def compute_mobility_score(features: dict) -> dict:
    crime = features.get("crime_density", 0.3)
    lighting = features.get("lighting", 80) / 100
    crowd = features.get("crowd_density", 70) / 100
    transport = features.get("transport_availability", 7) / 10
    violence = features.get("violence_ratio", 0.2)

    safety = (1 - crime) * 0.4 + (1 - violence) * 0.3 + lighting * 0.3
    accessibility = (crowd * 0.5) + (transport * 0.5)
    visibility = lighting

    mfs = (safety * 50) + (accessibility * 30) + (visibility * 20)

    return {
        "mobility_freedom_score": round(min(max(mfs, 0), 100), 2),
        "safety_score": round(safety * 100, 2),
        "accessibility_score": round(accessibility * 100, 2),
        "visibility_score": round(visibility * 100, 2),
    }