import { useEffect, useRef, useState } from "react";

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

function loadLeafletAssets() {
  return new Promise<void>((resolve, reject) => {
    if (typeof window === "undefined") {
      resolve();
      return;
    }
    if (window.L) {
      resolve();
      return;
    }

    const existingScript = document.querySelector('script[data-leaflet="true"]');
    const existingCss = document.querySelector('link[data-leaflet="true"]');
    let pending = 0;

    const finish = () => {
      pending -= 1;
      if (pending <= 0) resolve();
    };

    if (!existingCss) {
      pending += 1;
      const css = document.createElement("link");
      css.rel = "stylesheet";
      css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      css.dataset.leaflet = "true";
      css.onload = finish;
      css.onerror = reject;
      document.head.appendChild(css);
    }

    if (!existingScript) {
      pending += 1;
      const script = document.createElement("script");
      script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
      script.defer = true;
      script.dataset.leaflet = "true";
      script.onload = finish;
      script.onerror = reject;
      document.body.appendChild(script);
    }

    if (pending === 0) {
      resolve();
    }
  });
}

export function LocationPicker({ value, onChange }: LocationPickerProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<any>(null);
  const markerRef = useRef<any>(null);
  const [ready, setReady] = useState(false);

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
          onChange(coords);
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
      }
    };
  }, [onChange, value?.latitude, value?.longitude]);

  useEffect(() => {
    if (!ready || !window.L || !markerRef.current || !value) return;
    markerRef.current.setLatLng([value.latitude, value.longitude]);
    mapRef.current?.setView([value.latitude, value.longitude]);
  }, [ready, value]);

  return <div ref={mapContainerRef} style={{ height: 320, width: "100%", border: "1px solid #e5e7eb", borderRadius: 12 }} />;
}
