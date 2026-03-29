const BASE_URL = "http://127.0.0.1:8000/api/v1";

export async function getMobilityScore(lat: number, lng: number, timestamp: string) {
  const res = await fetch(`${BASE_URL}/score/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat, lng, timestamp }),
  });

  if (!res.ok) {
    throw new Error(`Score API failed: ${res.status}`);
  }
  return res.json();
}

export async function compareRoutes(
  source_id: string,
  dest_id: string,
  hour_of_day: number,
  weather_visibility = 8
) {
  const res = await fetch(`${BASE_URL}/routes/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_id, dest_id, hour_of_day, weather_visibility }),
  });

  if (!res.ok) {
    throw new Error(`Routes API failed: ${res.status}`);
  }
  return res.json();
}