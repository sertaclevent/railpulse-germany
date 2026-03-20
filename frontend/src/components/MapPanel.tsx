import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";

import type { Station } from "../types/dashboard";

const markerIcon = L.divIcon({
  className: "railpulse-marker",
  html: '<div class="h-4 w-4 rounded-full border-2 border-white bg-cyan-600 shadow-md"></div>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

interface MapPanelProps {
  station: Station | null;
}

export const MapPanel = ({ station }: MapPanelProps) => {
  const fallback = { lat: 48.140232, lon: 11.558335 };

  const lat = station?.latitude ?? fallback.lat;
  const lon = station?.longitude ?? fallback.lon;

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm shadow-slate-300/50">
      <div className="border-b border-slate-200 px-4 py-3">
        <h2 className="font-heading text-lg font-semibold text-slate-900">Station Map</h2>
      </div>
      <div className="h-[320px] md:h-[390px]">
        <MapContainer center={[lat, lon]} zoom={11} scrollWheelZoom className="h-full w-full">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker position={[lat, lon]} icon={markerIcon}>
            <Popup>
              <div className="space-y-1">
                <p className="font-semibold">{station?.name ?? "Muenchen Hbf"}</p>
                <p className="text-xs text-slate-600">{station?.city ?? "Muenchen"}</p>
                <p className="text-xs text-slate-600">{station?.short_description ?? "Selected station for current dashboard."}</p>
              </div>
            </Popup>
          </Marker>
        </MapContainer>
      </div>
    </section>
  );
};
