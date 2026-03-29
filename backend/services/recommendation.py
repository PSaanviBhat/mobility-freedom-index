RISK_RECOMMENDATIONS = {
    "low": {
        False: "Conditions look favorable. Standard route guidance is appropriate.",
        True: "Conditions are favorable, but share your live location for extra confidence after dark.",
    },
    "medium": {
        False: "Use a moderately busy route and avoid unnecessary detours.",
        True: "Prefer well-lit main roads and active transit corridors during late hours.",
    },
    "high": {
        False: "Consider postponing travel or switching to a safer, busier corridor.",
        True: "Avoid solo travel on this route right now and use a monitored or higher-traffic option.",
    },
}


def build_recommendation(risk_level: str, is_night: bool) -> str:
    normalized = (risk_level or "medium").lower()
    return RISK_RECOMMENDATIONS.get(normalized, RISK_RECOMMENDATIONS["medium"])[bool(is_night)]
