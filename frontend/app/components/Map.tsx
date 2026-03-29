'use client';

import { useEffect, useRef, useState } from 'react';
import 'leaflet/dist/leaflet.css';

type Coords = { lat: number; lng: number };

export default function Map() {
  const mapRef = useRef<any>(null);
  const routeControlRef = useRef<any>(null);
  const mapContainerRef = useRef<HTMLDivElement | null>(null);

  const [mounted, setMounted] = useState(false);
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [time, setTime] = useState('12:00');
  const [risk, setRisk] = useState<'LOW' | 'MEDIUM' | 'HIGH'>('LOW');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || !mapContainerRef.current) return;

    let cancelled = false;

    const initMap = async () => {
      const L = (await import('leaflet')).default;
      await import('leaflet-routing-machine');

      if (cancelled || !mapContainerRef.current) return;
      if (mapRef.current) return;

      const existingLeafletId = (mapContainerRef.current as any)._leaflet_id;
      if (existingLeafletId) {
        mapContainerRef.current.innerHTML = '';
      }

      const map = L.map(mapContainerRef.current).setView([12.9716, 77.5946], 13);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
      }).addTo(map);

      mapRef.current = map;
      setTimeout(() => map.invalidateSize(), 0);
    };

    initMap();

    return () => {
      cancelled = true;

      if (routeControlRef.current && mapRef.current) {
        try {
          mapRef.current.removeControl(routeControlRef.current);
        } catch {}
        routeControlRef.current = null;
      }

      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [mounted]);

  const geocode = async (query: string): Promise<Coords> => {
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`;
    const res = await fetch(url, { headers: { Accept: 'application/json' } });
    if (!res.ok) throw new Error('Geocoding failed');

    const data = await res.json();
    if (!Array.isArray(data) || data.length === 0) throw new Error('Location not found');

    return { lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon) };
  };

  const handleCalculateRoute = async () => {
    try {
      if (!start || !end) return alert('Enter both locations');
      if (!mapRef.current) return alert('Map not loaded yet');

      setLoading(true);
      const L = (await import('leaflet')).default;

      const startCoords = await geocode(start);
      const endCoords = await geocode(end);

      if (routeControlRef.current) {
        mapRef.current.removeControl(routeControlRef.current);
        routeControlRef.current = null;
      }

      const control = (L as any).Routing.control({
        waypoints: [L.latLng(startCoords.lat, startCoords.lng), L.latLng(endCoords.lat, endCoords.lng)],
        routeWhileDragging: false,
        addWaypoints: false,
        draggableWaypoints: false,
        fitSelectedRoutes: true,
        show: false,
      }).addTo(mapRef.current);

      routeControlRef.current = control;

      const hour = parseInt(time.split(':')[0], 10);
      if (hour >= 6 && hour < 12) setRisk('LOW');
      else if (hour >= 12 && hour < 18) setRisk('MEDIUM');
      else setRisk('HIGH');
    } catch (err) {
      console.error(err);
      alert('Location not found or routing failed');
    } finally {
      setLoading(false);
    }
  };

  if (!mounted) return null;

  return (
    <div className="relative h-screen w-full">
      <div ref={mapContainerRef} className="absolute inset-0 z-0" />

      <div className="absolute top-5 left-5 z-[1000] bg-white p-5 rounded-xl shadow-xl w-72">
        <h1 className="text-xl font-bold text-yellow-500 text-center mb-4">Safety Dashboard</h1>

        <input
          type="text"
          placeholder="Start location"
          value={start}
          onChange={(e) => setStart(e.target.value)}
          className="w-full p-2 mb-2 border rounded"
        />
        <input
          type="text"
          placeholder="End location"
          value={end}
          onChange={(e) => setEnd(e.target.value)}
          className="w-full p-2 mb-2 border rounded"
        />
        <input
          type="time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
          className="w-full p-2 mb-2 border rounded"
        />

        <p className="mb-3">
          Risk Level:
          <span className="ml-2 font-bold text-yellow-500">{risk}</span>
        </p>

        <div className="text-sm mb-3">
          <p className="font-semibold">Legend</p>
          <p>🔵 Low Risk</p>
          <p>🟡 Medium Risk</p>
          <p>🔴 High Risk</p>
        </div>

        <button
          onClick={handleCalculateRoute}
          disabled={loading}
          className="w-full bg-yellow-400 text-black py-2 rounded hover:bg-yellow-300 disabled:opacity-70"
        >
          {loading ? 'Calculating...' : 'Calculate Route'}
        </button>
      </div>
    </div>
  );
}