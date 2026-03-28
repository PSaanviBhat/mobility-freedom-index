'use client';

import { useEffect, useState } from 'react';
import 'leaflet/dist/leaflet.css';
import { getRouteRisk } from '../../lib/api';

export default function Map() {
  const [mounted, setMounted] = useState(false);
  const [risk, setRisk] = useState("LOADING...");

  useEffect(() => {
    setMounted(true);

    const loadMap = async () => {
      const L = (await import('leaflet')).default;
      await import('leaflet.heat');
      await import('leaflet-routing-machine');

      const map = L.map('map').setView([12.9716, 77.5946], 13);

      L.tileLayer(
        'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
      ).addTo(map);

      // 🔗 Backend / Dummy API
      const data = await getRouteRisk(
        { lat: 12.9716, lng: 77.5946 },
        { lat: 12.9352, lng: 77.6245 }
      );

      setRisk(data.risk);

      // 🔥 Heatmap
      const heat = (L as any).heatLayer(data.hotspots, {
        radius: 40,
        blur: 20,
        gradient: {
          0.2: 'blue',
          0.4: 'lime',
          0.6: 'yellow',
          1.0: 'red',
        },
      });

      heat.addTo(map);

      // 🛣️ Route
      (L as any).Routing.control({
        waypoints: data.route.map((p: any) =>
          L.latLng(p[0], p[1])
        ),
        routeWhileDragging: false,
      }).addTo(map);
    };

    loadMap();
  }, []);

  if (!mounted) return null;

  return (
    <>
      <div id="map" style={{ height: '100vh', width: '100%' }} />

      {/* Risk UI */}
      <div
        style={{
          position: 'absolute',
          top: 20,
          left: 20,
          background: 'black',
          color: 'white',
          padding: '12px',
          borderRadius: '10px',
          fontWeight: 'bold',
        }}
      >
        Route Risk: {risk}
      </div>
    </>
  );
}
