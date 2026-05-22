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

// Aggressively force Leaflet to recompute its tile grid. The map mounts inside
// a sticky sidebar that grows after first paint; if we only invalidate once
// the early grid points at tiles that never get fetched, leaving gaps. We
// invalidate at a handful of timings + on every container resize + on every
// hotels-change, and we redraw the TileLayer after each invalidation so the
// fetcher reconsiders any tile that previously failed.
function FitToContainer({ hotels }: { hotels: SearchResultItem[] }) {
  const map = useMap();

  useEffect(() => {
    const recalc = () => {
      map.invalidateSize({ animate: false });
      map.eachLayer((layer) => {
        if (layer instanceof L.TileLayer) {
          layer.redraw();
        }
      });
    };

    // Spread across the first ~1.5 s -- covers layout settling, font load,
    // sidebar becoming sticky, image lazy-load shifts, etc.
    const timers = [0, 80, 200, 500, 900, 1500].map((ms) =>
      window.setTimeout(recalc, ms),
    );

    const ro = new ResizeObserver(recalc);
    ro.observe(map.getContainer());
    window.addEventListener("resize", recalc);

    // Also redraw once Leaflet finishes its initial load.
    map.whenReady(recalc);

    return () => {
      timers.forEach(window.clearTimeout);
      ro.disconnect();
      window.removeEventListener("resize", recalc);
    };
  }, [map]);

  useEffect(() => {
    if (hotels.length === 0) return;
    const bounds = L.latLngBounds(hotels.map((h) => [h.latitude, h.longitude] as [number, number]));
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 13 });
    // Immediately after a fitBounds, the tile grid may need another nudge.
    window.setTimeout(() => map.invalidateSize({ animate: false }), 50);
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
      // Pre-rendering a buffer of tiles outside the viewport avoids visible
      // gaps when the user pans / when the container resizes.
      preferCanvas={false}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors · &copy; <a href="https://carto.com/attributions">CARTO</a>'
        // CartoDB Voyager -- much friendlier rate limits than raw OSM tiles
        // (osm.org throttles unless you have a registered subdomain). Voyager
        // also has retina-quality tiles via the {r} placeholder.
        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        subdomains={["a", "b", "c", "d"]}
        maxZoom={19}
        // Buffer tiles outside the viewport so panning / resizes don't show
        // gray squares while new tiles fetch.
        keepBuffer={4}
        crossOrigin
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
