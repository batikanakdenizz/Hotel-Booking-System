import { useMemo } from "react";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";
import type { SearchResultItem } from "@/types/hotel";

// Fix default Leaflet marker icon paths under bundlers.
const DefaultIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

export function HotelMap({ hotels }: { hotels: SearchResultItem[] }) {
  const center = useMemo<[number, number]>(() => {
    if (hotels.length === 0) return [41.9, 12.5];
    const avgLat = hotels.reduce((s, h) => s + h.latitude, 0) / hotels.length;
    const avgLng = hotels.reduce((s, h) => s + h.longitude, 0) / hotels.length;
    return [avgLat, avgLng];
  }, [hotels]);

  return (
    <MapContainer
      center={center}
      zoom={hotels.length > 0 ? 12 : 4}
      scrollWheelZoom={false}
      className="h-full w-full rounded-2xl"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {hotels.map((h) => (
        <Marker key={h.hotel_id} position={[h.latitude, h.longitude]}>
          <Popup>
            <strong>{h.name}</strong>
            <br />
            {h.address}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
