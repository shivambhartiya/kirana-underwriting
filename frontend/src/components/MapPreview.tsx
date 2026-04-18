import { useEffect, useMemo } from "react";
import L from "leaflet";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
import { Circle, MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet";

L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

function DraggableMarker({
  lat,
  lng,
  onPositionChange,
}: {
  lat: number;
  lng: number;
  onPositionChange?: (lat: number, lng: number) => void;
}) {
  useMapEvents({
    click(event) {
      onPositionChange?.(event.latlng.lat, event.latlng.lng);
    },
  });

  return (
    <Marker
      draggable
      position={[lat, lng]}
      eventHandlers={{
        dragend(event) {
          const marker = event.target;
          const position = marker.getLatLng();
          onPositionChange?.(position.lat, position.lng);
        },
      }}
    />
  );
}

function RecenterMap({ center }: { center: [number, number] }) {
  const map = useMap();

  useEffect(() => {
    map.invalidateSize();
    map.flyTo(center, 18, { animate: true, duration: 0.8 });
  }, [center, map]);

  return null;
}

export function MapPreview({
  lat,
  lng,
  label,
  accuracyMeters,
  locationSource,
  onPositionChange,
}: {
  lat?: number;
  lng?: number;
  label?: string;
  accuracyMeters?: number | null;
  locationSource?: string;
  onPositionChange?: (lat: number, lng: number) => void;
}) {
  const center = useMemo<[number, number]>(() => [lat ?? 19.076, lng ?? 72.8777], [lat, lng]);
  const accuracyRadius = useMemo(() => {
    if (!accuracyMeters) return null;
    return Math.min(Math.max(accuracyMeters, 12), 120);
  }, [accuracyMeters]);

  return (
    <div className="panel overflow-hidden">
      <div className="h-80 w-full">
        <MapContainer center={center} zoom={18} scrollWheelZoom className="h-full w-full">
          <RecenterMap center={center} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            detectRetina
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {accuracyRadius ? <Circle center={center} radius={accuracyRadius} pathOptions={{ color: "#0f766e", opacity: 0.45, fillOpacity: 0.08 }} /> : null}
          <DraggableMarker lat={center[0]} lng={center[1]} onPositionChange={onPositionChange} />
        </MapContainer>
      </div>
      <div className="border-t border-ink/10 px-4 py-3 text-sm text-ink/70">
        <div className="font-medium text-ink">{label || "Tap or drag the pin to confirm the exact shop location."}</div>
        <div className="mt-1 flex flex-wrap gap-4">
          <span>Lat {center[0].toFixed(5)}, Lng {center[1].toFixed(5)}</span>
          {locationSource ? <span>Source: {locationSource}</span> : null}
          {accuracyRadius ? <span>GPS accuracy radius: ~{Math.round(accuracyRadius)}m</span> : null}
        </div>
      </div>
    </div>
  );
}
