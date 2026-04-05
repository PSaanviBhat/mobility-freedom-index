'use client';

import { useEffect, useRef, useState } from 'react';
import 'leaflet/dist/leaflet.css';

type Coords = { lat: number; lng: number };

type RouteSummary = {
  id: string;
  label: string;
  distanceKm: number;
  durationMin: number;
  safetyIndex: number;
  instructions: string[];
  isPrimary: boolean;
};

export default function Map() {
  const mapRef = useRef<any>(null);
  const routeControlRef = useRef<any>(null);
  const hoverPopupRef = useRef<any>(null);
  const hoverLayersRef = useRef<any[]>([]);
  const mapContainerRef = useRef<HTMLDivElement | null>(null);

  const [mounted, setMounted] = useState(false);
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [time, setTime] = useState('12:00');
  const [risk, setRisk] = useState<'LOW' | 'MEDIUM' | 'HIGH'>('LOW');
  const [loading, setLoading] = useState(false);
  const [routes, setRoutes] = useState<RouteSummary[]>([]);

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

  const computeSafetyIndex = (distanceKm: number, currentRisk: 'LOW' | 'MEDIUM' | 'HIGH') => {
    const base = currentRisk === 'LOW' ? 92 : currentRisk === 'MEDIUM' ? 74 : 56;
    return Math.max(20, Math.round(base - distanceKm * 3));
  };

  const handleCalculateRoute = async () => {
    try {
      if (!start || !end) return alert('Enter both locations');
      if (!mapRef.current) return alert('Map not loaded yet');

      setLoading(true);
      setRoutes([]);
      const L = (await import('leaflet')).default;

      const hour = parseInt(time.split(':')[0], 10);
      const currentRisk: 'LOW' | 'MEDIUM' | 'HIGH' =
        hour >= 6 && hour < 12 ? 'LOW' : hour >= 12 && hour < 18 ? 'MEDIUM' : 'HIGH';
      setRisk(currentRisk);

      const startCoords = await geocode(start);
      const endCoords = await geocode(end);

      if (routeControlRef.current) {
        mapRef.current.removeControl(routeControlRef.current);
        routeControlRef.current = null;
      }
      hoverLayersRef.current.forEach((layer) => {
        if (mapRef.current && layer) {
          mapRef.current.removeLayer(layer);
        }
      });
      hoverLayersRef.current = [];
      if (hoverPopupRef.current && mapRef.current) {
        mapRef.current.removeLayer(hoverPopupRef.current);
        hoverPopupRef.current = null;
      }

      const router = (L as any).Routing?.osrmv1?.({
        serviceUrl: 'https://router.project-osrm.org/route/v1',
        profile: 'car',
        alternatives: true,
        steps: true,
      });

      const control = (L as any).Routing.control({
        waypoints: [L.latLng(startCoords.lat, startCoords.lng), L.latLng(endCoords.lat, endCoords.lng)],
        routeWhileDragging: false,
        addWaypoints: false,
        draggableWaypoints: false,
        fitSelectedRoutes: true,
        show: false,
        router,
        showAlternatives: true,
        altLineOptions: {
          styles: [
            { color: '#fbbf24', opacity: 0.5, weight: 4 },
            { color: '#fbbf24', opacity: 0.2, weight: 3 },
          ],
        },
        lineOptions: {
          styles: [
            { color: '#fde68a', opacity: 0.8, weight: 6 },
            { color: '#fbbf24', opacity: 0.5, weight: 4 },
            { color: '#f97316', opacity: 0.3, weight: 3 },
          ],
        },
      }).addTo(mapRef.current);

      routeControlRef.current = control;

      control.on('routesfound', (e: any) => {
        const foundRoutes = Array.isArray(e.routes) ? e.routes.slice(0, 3) : [];

        const attachHover = (route: any, index: number) => {
          const label = index === 0 ? 'Primary Route' : `Alternate Route ${index}`;
          const distanceKm = route.summary?.totalDistance ? route.summary.totalDistance / 1000 : 0;
          const safetyIndex = computeSafetyIndex(distanceKm, currentRisk);
          const content = `<div style="font-size:0.85rem;"><strong>${label}</strong><br/>Distance: ${distanceKm.toFixed(1)} km<br/>Safety index: ${safetyIndex}</div>`;

          const bindHoverToLayer = (layer: any) => {
            if (!layer || typeof layer.on !== 'function') return;
            layer.on('mouseover', (ev: any) => {
              if (!mapRef.current) return;
              if (hoverPopupRef.current) {
                mapRef.current.removeLayer(hoverPopupRef.current);
                hoverPopupRef.current = null;
              }

              hoverPopupRef.current = L.popup({
                closeButton: false,
                autoClose: false,
                closeOnClick: false,
                className: 'route-hover-popup',
                offset: [0, -10],
              })
                .setLatLng(ev.latlng)
                .setContent(content)
                .openOn(mapRef.current);
            });

            layer.on('mouseout', () => {
              if (!mapRef.current || !hoverPopupRef.current) return;
              mapRef.current.removeLayer(hoverPopupRef.current);
              hoverPopupRef.current = null;
            });
          };

          if (route.line && typeof route.line.on === 'function') {
            bindHoverToLayer(route.line);
          } else if (route.coordinates && Array.isArray(route.coordinates) && route.coordinates.length > 0) {
            const hoverLine = L.polyline(route.coordinates, {
              color: 'transparent',
              weight: 16,
              opacity: 0,
            }).addTo(mapRef.current);
            bindHoverToLayer(hoverLine);
            hoverLayersRef.current.push(hoverLine);
          }
        };

        const summaries = foundRoutes.map((route: any, index: number) => {
          const distanceKm = route.summary?.totalDistance ? route.summary.totalDistance / 1000 : 0;
          const durationMin = route.summary?.totalTime ? Math.round(route.summary.totalTime / 60) : 0;
          const instructions = Array.isArray(route.instructions)
            ? route.instructions.map((inst: any) => inst.text || inst.name || '').filter(Boolean)
            : [];

          attachHover(route, index);

          return {
            id: `${Date.now()}-${index}`,
            label: index === 0 ? 'Primary Route' : `Alternate Route ${index}`,
            distanceKm,
            durationMin,
            safetyIndex: computeSafetyIndex(distanceKm, currentRisk),
            instructions,
            isPrimary: index === 0,
          };
        });

        setRoutes(summaries);
      });
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

      <div className="absolute top-5 right-5 z-[1000]">
        <button
          type="button"
          onClick={() => alert('Mock SOS activated. Help is on the way!')}
          className="bg-red-600 text-white font-semibold px-4 py-2 rounded-full shadow-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-400"
        >
          SOS
        </button>
      </div>

      <div className="absolute top-5 left-5 z-[1000] bg-white p-5 rounded-xl shadow-xl w-80 max-w-[90vw] max-h-[calc(100vh-3rem)] overflow-hidden overflow-y-auto">
        <h1 className="text-xl font-bold text-yellow-500 text-center mb-4">Safety Dashboard</h1>

        <label className="block text-sm font-semibold text-slate-600 mb-1">From</label>
        <input
          type="text"
          placeholder="From location"
          value={start}
          onChange={(e) => setStart(e.target.value)}
          className="w-full p-2 mb-3 border rounded"
        />

        <label className="block text-sm font-semibold text-slate-600 mb-1">To</label>
        <input
          type="text"
          placeholder="To location"
          value={end}
          onChange={(e) => setEnd(e.target.value)}
          className="w-full p-2 mb-3 border rounded"
        />

        <label className="block text-sm font-semibold text-slate-600 mb-1">Departure time</label>
        <input
          type="time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
          className="w-full p-2 mb-3 border rounded"
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

        {routes.length > 0 && (
          <div className="mt-4 space-y-3">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
              <p className="font-semibold text-slate-700">From:</p>
              <p className="text-slate-600 truncate">{start}</p>
              <p className="mt-2 font-semibold text-slate-700">To:</p>
              <p className="text-slate-600 truncate">{end}</p>
            </div>

            {routes.map((route) => (
              <div
                key={route.id}
                className={`rounded-xl border p-3 ${route.isPrimary ? 'border-yellow-400/80 bg-yellow-50' : 'border-slate-200 bg-white'}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <p className="font-semibold text-slate-800">{route.label}</p>
                    <p className="text-xs text-slate-500">{route.isPrimary ? 'Fastest route' : 'Alternative route'}</p>
                  </div>
                  <span className="rounded-full bg-slate-200 px-2 py-1 text-[11px] uppercase tracking-[0.15em] text-slate-600">
                    {route.isPrimary ? 'Primary' : 'Alt'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-sm text-slate-600 mb-2">
                  <div>
                    <p className="font-semibold text-slate-800">Distance</p>
                    <p>{route.distanceKm.toFixed(1)} km</p>
                  </div>
                  <div>
                    <p className="font-semibold text-slate-800">Safety index</p>
                    <p>{route.safetyIndex}</p>
                  </div>
                </div>

                <div className="rounded-lg bg-slate-100 p-2 max-h-40 overflow-y-auto text-xs text-slate-700">
                  <p className="font-semibold text-slate-800 mb-2">Directions</p>
                  {route.instructions.length > 0 ? (
                    route.instructions.map((step, idx) => (
                      <p key={idx} className="leading-5 whitespace-normal break-words">{idx + 1}. {step}</p>
                    ))
                  ) : (
                    <p>No directions available for this route.</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}