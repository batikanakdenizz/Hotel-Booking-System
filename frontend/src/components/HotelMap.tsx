import { useEffect, useMemo } from "react";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
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

// Forces Leaflet to recompute its tile grid after the container reaches its
// final layout size. Without this the map renders a partial / fragmented grid
// when mounted inside a sticky sidebar that grows after first paint.
function FitToContainer({ hotels }: { hotels: SearchResultItem[] }) {
  const map = useMap();

  useEffect(() => {
    const recalc = () => map.invalidateSize();
    const t1 = window.setTimeout(recalc, 0);
    const t2 = window.setTimeout(recalc, 250);
    const ro = new ResizeObserver(recalc);
    ro.observe(map.getContainer());
    window.addEventListener("resize", recalc);
    return () => {
      window.clearTimeout(t1);
      window.clearTimeout(t2);
      ro.disconnect();
      window.removeEventListener("resize", recalc);
    };
  }, [map]);

  useEffect(() => {
    if (hotels.length === 0) return;
    const bounds = L.latLngBounds(hotels.map((h) => [h.latitude, h.longitude] as [number, number]));
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 13 });
  }, [hotels, map]);

  return null;
}

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
      <FitToContainer hotels={hotels} />
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
