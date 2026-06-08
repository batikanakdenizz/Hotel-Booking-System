import { Link } from "react-router-dom";
import { Star, MapPin, BedDouble } from "lucide-react";
import type { SearchResultItem } from "@/types/hotel";
import { formatPrice } from "@/lib/utils";

const FALLBACK_IMG =
  "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?auto=format&fit=crop&w=900&q=70";

export interface HotelCardProps {
  hotel: SearchResultItem;
  searchQuery: string;
}

export function HotelCard({ hotel, searchQuery }: HotelCardProps) {
  const cheapest = hotel.available_rooms.reduce<number | null>((acc, r) => {
    const n = Number(r.price_per_night);
    return acc === null || n < acc ? n : acc;
  }, null);
  const hasDiscount = hotel.available_rooms.some((r) => r.discount_applied);

  return (
    <Link
      to={`/hotels/${hotel.hotel_id}?${searchQuery}`}
      className="group flex flex-col md:flex-row gap-4 bg-white rounded-2xl shadow-card overflow-hidden transition-all duration-300 ease-out hover:-translate-y-0.5 hover:shadow-card-lg"
    >
      <div className="md:w-72 md:flex-shrink-0 aspect-[4/3] md:aspect-auto overflow-hidden">
        <img
          src={hotel.image_url || FALLBACK_IMG}
          alt={hotel.name}
          loading="lazy"
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
        />
      </div>
      <div className="flex-1 p-5 flex flex-col">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h3 className="text-lg font-bold text-slate-900 group-hover:text-brand-700">{hotel.name}</h3>
            <p className="mt-1 flex items-center gap-1 text-sm text-slate-500">
              <MapPin className="h-4 w-4" /> {hotel.address}
            </p>
          </div>
          {hotel.star_rating != null && (
            <span className="flex items-center gap-1 rounded-md bg-brand-50 px-2 py-1 text-sm font-semibold text-brand-700">
              <Star className="h-4 w-4 fill-current" /> {hotel.star_rating}
            </span>
          )}
        </div>

        <p className="mt-2 text-sm text-slate-600 line-clamp-2">{hotel.description}</p>

        <div className="mt-3 flex flex-wrap gap-1.5">
          {hotel.amenities.slice(0, 4).map((a) => (
            <span
              key={a}
              className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700"
            >
              {a}
            </span>
          ))}
        </div>

        <div className="mt-auto flex items-end justify-between pt-4">
          <span className="flex items-center gap-1 text-sm text-slate-500">
            <BedDouble className="h-4 w-4" /> {hotel.available_rooms.length} room types
          </span>
          <div className="text-right">
            {hasDiscount && <p className="text-[11px] uppercase tracking-wide font-semibold text-accent">Member 15% off</p>}
            <p className="text-xs text-slate-500">From</p>
            <p className="text-xl font-bold text-slate-900">
              {cheapest != null ? formatPrice(cheapest) : "-"}
              <span className="text-xs font-normal text-slate-500"> /night</span>
            </p>
          </div>
        </div>
      </div>
    </Link>
  );
}
