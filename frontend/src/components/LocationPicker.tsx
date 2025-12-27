import { useEffect, useRef, useState } from "react";

import { loadLeafletAssets } from "../utils/leafletLoader";

type Coordinates = { latitude: number; longitude: number };

type LocationPickerProps = {
  value?: Coordinates;
  onChange: (coords: Coordinates) => void;
};

declare global {
  interface Window {
    L?: any;
  }
}

export function LocationPicker({ value, onChange }: LocationPickerProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<any>(null);
  const markerRef = useRef<any>(null);
  const onChangeRef = useRef(onChange);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  useEffect(() => {
    let destroyed = false;
    loadLeafletAssets()
      .then(() => {
        if (destroyed || typeof window === "undefined" || !mapContainerRef.current || !window.L) return;

        const L = window.L;
        const center: [number, number] = value?.latitude && value?.longitude ? [value.latitude, value.longitude] : [35.715298, 51.404343];

        mapRef.current = L.map(mapContainerRef.current).setView(center, 15);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: "&copy; OpenStreetMap contributors",
        }).addTo(mapRef.current);

        markerRef.current = L.marker(center).addTo(mapRef.current);

        mapRef.current.on("click", (e: any) => {
          const coords = { latitude: e.latlng.lat, longitude: e.latlng.lng };
          markerRef.current.setLatLng(e.latlng);
          onChangeRef.current(coords);
        });

        setReady(true);
      })
      .catch(() => {
        setReady(false);
      });

    return () => {
      destroyed = true;
      if (mapRef.current) {
        mapRef.current.off();
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
    // We intentionally run this only once to avoid remounting the map container.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!ready || !window.L || !markerRef.current || !value) return;
    markerRef.current.setLatLng([value.latitude, value.longitude]);
    mapRef.current?.setView([value.latitude, value.longitude]);
  }, [ready, value]);

  return <div ref={mapContainerRef} style={{ height: 320, width: "100%", border: "1px solid #e5e7eb", borderRadius: 12 }} />;
}
