import { useEffect, useMemo, useState } from "react";
import type { LatLngExpression } from "leaflet";
import L from "leaflet";
import { MapContainer, Marker, TileLayer, useMapEvents } from "react-leaflet";

import "leaflet/dist/leaflet.css";

const markerIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

type Coordinates = { latitude: number; longitude: number };

type LocationPickerProps = {
  value?: Coordinates;
  onChange: (coords: Coordinates) => void;
};

function ClickCapture({ onSelect }: { onSelect: (coords: Coordinates) => void }) {
  useMapEvents({
    click(e) {
      onSelect({ latitude: e.latlng.lat, longitude: e.latlng.lng });
    },
  });
  return null;
}

export function LocationPicker({ value, onChange }: LocationPickerProps) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  const center: LatLngExpression = useMemo(() => {
    if (value?.latitude && value?.longitude) {
      return [value.latitude, value.longitude];
    }
    return [35.715298, 51.404343]; // Tehran as default
  }, [value]);

  if (!isClient) return null;

  return (
    <div style={{ border: "1px solid #e5e7eb", borderRadius: 12, overflow: "hidden" }}>
      <MapContainer center={center} zoom={15} style={{ height: 320, width: "100%" }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <ClickCapture onSelect={onChange} />
        {value ? <Marker position={[value.latitude, value.longitude]} icon={markerIcon} /> : null}
      </MapContainer>
    </div>
  );
}
