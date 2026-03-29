const BASE_URL = "http://localhost:5000";

export async function getRouteRisk(start: any, end: any) {
  try {
    const res = await fetch(`${BASE_URL}/route-risk`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ start, end }),
    });

    return await res.json();
  } catch (err) {
    console.log("Using dummy data");

    // 🔥 fallback (so frontend always works)
    return {
      risk: "MEDIUM",
      score: 0.5,
      route: [
        [12.9716, 77.5946],
        [12.965, 77.60],
        [12.95, 77.61],
        [12.9352, 77.6245],
      ],
      hotspots: [
        [12.9716, 77.5946, 1],
        [12.9717, 77.5947, 1],
        [12.9720, 77.5950, 1],
      ],
    };
  }
}
