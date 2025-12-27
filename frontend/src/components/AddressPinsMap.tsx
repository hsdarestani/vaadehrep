import { useEffect, useRef, useState } from "react";

import type { Address } from "../api/types";
import { loadLeafletAssets } from "../utils/leafletLoader";

type Props = {
  addresses: Address[];
  highlightId?: number;
};

declare global {
  interface Window {
    L?: any;
  }
}

export function AddressPinsMap({ addresses, highlightId }: Props) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let destroyed = false;
    loadLeafletAssets()
      .then(() => {
        if (destroyed || typeof window === "undefined" || !mapContainerRef.current || !window.L) return;
        const L = window.L;
        mapRef.current = L.map(mapContainerRef.current).setView([35.715298, 51.404343], 12);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: "&copy; OpenStreetMap contributors",
        }).addTo(mapRef.current);
        setReady(true);
      })
      .catch(() => setReady(false));

    return () => {
      destroyed = true;
      if (mapRef.current) {
        mapRef.current.off();
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!ready || !window.L || !mapRef.current) return;
    const L = window.L;
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    const points: [number, number][] = [];
    addresses.forEach((address) => {
      if (address.latitude == null || address.longitude == null) return;
      const latLng: [number, number] = [Number(address.latitude), Number(address.longitude)];
      const marker = L.circleMarker(latLng, {
        radius: highlightId === address.id ? 10 : 8,
        color: highlightId === address.id ? "#2563eb" : "#0f172a",
        fillColor: highlightId === address.id ? "#3b82f6" : "#1f2937",
        fillOpacity: 0.9,
        weight: 2,
      }).addTo(mapRef.current);
      marker.bindTooltip(address.title || "آدرس");
      markersRef.current.push(marker);
      points.push(latLng);
    });

    if (points.length > 1) {
      mapRef.current.fitBounds(L.latLngBounds(points), { padding: [20, 20] });
    } else if (points.length === 1) {
      mapRef.current.setView(points[0], 15);
    }
  }, [addresses, highlightId, ready]);

  return (
    <div
      ref={mapContainerRef}
      style={{
        height: 320,
        width: "100%",
        border: "1px solid #e5e7eb",
        borderRadius: 12,
      }}
    />
  );
}
