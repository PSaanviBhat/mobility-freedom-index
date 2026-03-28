# ============================================================
# ML INTEGRATION POINT
# The ML team replaces the stub below with their trained model.
# Input: dict of features. Output: dict of scores.
# ============================================================

def compute_mobility_score(features: dict) -> dict:
    """
    Stub scoring function.
    Replace the body of this function with the real ML model call.
    
    Expected features keys:
        - hour (int): 0-23
        - crowd_density (float): 0-1 proxy score
        - lighting_index (float): 0-1 from weather/time proxy
        - crime_index (float): 0-1 from NCRB/dataset
        - transit_access (float): 0-1
    
    Returns dict with scores 0-100.
    """
    # --- STUB: Replace this block ---
    hour = features.get("hour", 12)
    is_night = hour < 6 or hour > 21
    
    safety = 40 if is_night else 75
    accessibility = features.get("transit_access", 0.5) * 100
    visibility = 30 if is_night else 80
    mfs = (safety * 0.5) + (accessibility * 0.3) + (visibility * 0.2)
    # --- End stub ---
    
    return {
        "mobility_freedom_score": round(mfs, 2),
        "safety_score": round(safety, 2),
        "accessibility_score": round(accessibility, 2),
        "visibility_score": round(visibility, 2),
    }