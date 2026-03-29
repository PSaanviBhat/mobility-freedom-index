'use client';

import { useEffect, useState } from 'react';
import 'leaflet/dist/leaflet.css';
import 'leaflet-routing-machine/dist/leaflet-routing-machine.css';

// 🌍 Convert place name → lat/lng
async function geocode(place: string) {
  const res = await fetch(
    `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(place)}&limit=1`,
    {
      headers: {
        'User-Agent': 'safety-map-app',
      },
    }
  );

  const data = await res.json();

  if (!data.length) {
    throw new Error('Location not found');
  }

  return {
    lat: parseFloat(data[0].lat),
    lng: parseFloat(data[0].lon),
  };
}

export default function Map() {
  const [mounted, setMounted] = useState(false);
  const [risk, setRisk] = useState('LOW');

  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [time, setTime] = useState('');

  const [map, setMap] = useState<any>(null);
  const [routeControl, setRouteControl] = useState<any>(null);

  useEffect(() => {
    setMounted(true);

    // ⏰ Set current time
    const now = new Date();
    const formattedTime = now.toTimeString().slice(0, 5);
    setTime(formattedTime);

    const loadMap = async () => {
      const L = (await import('leaflet')).default;
      await import('leaflet-routing-machine');

      const mapInstance = L.map('map').setView([12.9716, 77.5946], 13);

      L.tileLayer(
        'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
      ).addTo(mapInstance);

      setMap(mapInstance);
    };

    loadMap();
  }, []);

  if (!mounted) return null;

  return (
    <div className="relative h-screen w-full">

      {/* 🗺️ MAP */}
      <div id="map" className="absolute top-0 left-0 h-full w-full" />

      {/* 🔥 DASHBOARD */}
      <div className="absolute top-5 left-5 z-[1000] bg-white p-5 rounded-xl shadow-xl w-72">

        <h1 className="text-xl font-bold text-yellow-500 text-center mb-4">
          Safety Dashboard
        </h1>

        {/* 📍 Start */}
        <input
          type="text"
          placeholder="Start location"
          value={start}
          onChange={(e) => setStart(e.target.value)}
          className="w-full p-2 mb-2 border rounded"
        />

        {/* 📍 End */}
        <input
          type="text"
          placeholder="End location"
          value={end}
          onChange={(e) => setEnd(e.target.value)}
          className="w-full p-2 mb-2 border rounded"
        />

        {/* 🕒 Time */}
        <input
          type="time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
          className="w-full p-2 mb-2 border rounded"
        />

        {/* 🚨 Risk */}
        <p className="mb-3">
          Risk Level:
          <span className="ml-2 font-bold text-yellow-500">
            {risk}
          </span>
        </p>

        {/* 🎨 Legend */}
        <div className="text-sm mb-3">
          <p className="font-semibold">Legend</p>
          <p>🔵 Low Risk</p>
          <p>🟡 Medium Risk</p>
          <p>🔴 High Risk</p>
        </div>

        {/* 🚀 Button */}
        <button
          onClick={async () => {
            try {
              if (!start || !end) {
                alert('Enter both locations');
                return;
              }

              if (!map) {
                alert('Map not loaded yet');
                return;
              }

              const L = (await import('leaflet')).default;

              const startCoords = await geocode(start);
              const endCoords = await geocode(end);

              // 🧹 Remove previous route
              if (routeControl) {
                map.removeControl(routeControl);
              }

              // 🧭 Add new route
              const control = L.Routing.control({
                waypoints: [
                  L.latLng(startCoords.lat, startCoords.lng),
                  L.latLng(endCoords.lat, endCoords.lng),
                ],
                routeWhileDragging: false,
              }).addTo(map);

              setRouteControl(control);

              // ⏰ Risk based on time
              const hour = parseInt(time.split(':')[0]);

              if (hour >= 6 && hour < 12) setRisk('LOW');
              else if (hour >= 12 && hour < 18) setRisk('MEDIUM');
              else setRisk('HIGH');

            } catch (err) {
              alert('Location not found');
            }
          }}
          className="w-full bg-yellow-400 text-black py-2 rounded hover:bg-yellow-300"
        >
          Calculate Route
        </button>

      </div>
    </div>
  );
}
