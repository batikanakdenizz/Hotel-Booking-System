import { useMemo, useState } from "react";
import { useParams, useSearchParams, useNavigate, Link } from "react-router-dom";
import { toast } from "sonner";
import { MapPin, Star, Wifi, Coffee, Sparkles, Users } from "lucide-react";
import { useHotelDetail } from "@/api/hotels";
import { useHotelDistribution } from "@/api/comments";
import { useCreateBooking } from "@/api/bookings";
import { Spinner } from "@/components/ui/Spinner";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { RatingChart } from "@/components/RatingChart";
import { CommentList } from "@/components/CommentList";
import { useAuth } from "@/hooks/useAuth";
import { formatPrice } from "@/lib/utils";
import type { AvailableRoom } from "@/types/hotel";

const FALLBACK_IMG =
  "https://images.unsplash.com/photo-1564501049412-61c2a3083791?auto=format&fit=crop&w=1600&q=70";

export default function HotelDetailPage() {
  const { hotelId } = useParams<{ hotelId: string }>();
  const [sp] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const checkIn = sp.get("check_in") ?? "";
  const checkOut = sp.get("check_out") ?? "";
  const guests = Number(sp.get("guests") ?? 2);

  const { data: hotel, isLoading } = useHotelDetail(hotelId);
  const { data: dist } = useHotelDistribution(hotelId);
  const createBooking = useCreateBooking();

  const [selectedRoomId, setSelectedRoomId] = useState<string | null>(null);
  const nights = useMemo(() => diffDays(checkIn, checkOut), [checkIn, checkOut]);

  if (isLoading) {
    return <div className="grid h-[60vh] place-items-center"><Spinner /></div>;
  }
  if (!hotel) {
    return <div className="mx-auto max-w-6xl p-12 text-slate-600">Hotel not found.</div>;
  }

  const selectedRoom: AvailableRoom | undefined = hotel.available_rooms.find(
    (r) => r.room_id === selectedRoomId,
  );

  async function book() {
    if (!user) {
      navigate(`/login?next=${encodeURIComponent(window.location.pathname + window.location.search)}`);
      return;
    }
    if (!selectedRoom || !checkIn || !checkOut) {
      toast.error("Pick a room and dates first");
      return;
    }
    try {
      await createBooking.mutateAsync({
        hotel_id: hotel!.hotel_id,
        room_id: selectedRoom.room_id,
        check_in: checkIn,
        check_out: checkOut,
        guests,
      });
      toast.success("Booking confirmed");
      navigate("/my-bookings");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Booking failed");
    }
  }

  return (
    <div className="bg-slate-50 min-h-[calc(100vh-4rem)]">
      {/* Hero image */}
      <div className="relative h-72 md:h-96 overflow-hidden">
        <img src={hotel.image_url || FALLBACK_IMG} alt={hotel.name} className="h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 mx-auto max-w-6xl px-4 pb-6 text-white">
          <h1 className="text-3xl md:text-4xl font-bold drop-shadow">{hotel.name}</h1>
          <p className="mt-1 flex items-center gap-1 text-white/90">
            <MapPin className="h-4 w-4" /> {hotel.address}
          </p>
          {hotel.star_rating != null && (
            <p className="mt-2 inline-flex items-center gap-1 rounded-md bg-white/90 px-2 py-0.5 text-sm font-semibold text-brand-700">
              <Star className="h-4 w-4 fill-current" /> {hotel.star_rating} stars
            </p>
          )}
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-4 py-8 grid lg:grid-cols-[1fr_360px] gap-6">
        {/* Main column */}
        <div className="space-y-6">
          <Card>
            <CardBody>
              <h2 className="text-xl font-bold text-slate-900">About this stay</h2>
              <p className="mt-2 text-slate-700 leading-relaxed">{hotel.description || "No description provided."}</p>
              {hotel.amenities.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {hotel.amenities.map((a) => (
                    <span
                      key={a}
                      className="flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700"
                    >
                      <AmenityIcon name={a} /> {a}
                    </span>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <h2 className="text-xl font-bold text-slate-900">Available rooms</h2>
              {hotel.available_rooms.length === 0 ? (
                <p className="mt-3 text-slate-500">No rooms available for these dates.</p>
              ) : (
                <ul className="mt-4 space-y-3">
                  {hotel.available_rooms.map((r) => {
                    const isSel = selectedRoomId === r.room_id;
                    return (
                      <li
                        key={r.room_id}
                        onClick={() => setSelectedRoomId(r.room_id)}
                        className={
                          "flex items-center justify-between gap-3 rounded-xl border p-4 cursor-pointer transition-colors " +
                          (isSel ? "border-brand-600 bg-brand-50" : "border-slate-200 hover:border-brand-300 bg-white")
                        }
                      >
                        <div>
                          <p className="font-semibold text-slate-900">{r.room_type}</p>
                          <p className="text-sm text-slate-500 flex items-center gap-1">
                            <Users className="h-4 w-4" /> Up to {r.capacity} guests · {r.available_count} left
                          </p>
                        </div>
                        <div className="text-right">
                          {r.discount_applied && (
                            <p className="text-xs text-slate-400 line-through">{formatPrice(r.original_price)}</p>
                          )}
                          <p className={"text-lg font-bold " + (r.discount_applied ? "text-accent" : "text-slate-900")}>
                            {formatPrice(r.price_per_night)}
                          </p>
                          <p className="text-xs text-slate-500">per night</p>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
            </CardBody>
          </Card>

          {dist && dist.total_comments > 0 && (
            <Card>
              <CardBody>
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold text-slate-900">Guest ratings</h2>
                  <span className="text-sm text-slate-500">{dist.total_comments} reviews</span>
                </div>
                <p className="mt-1 text-3xl font-bold text-brand-700">
                  {dist.avg_overall?.toFixed(1) ?? "-"}
                  <span className="text-base font-normal text-slate-500"> / 10</span>
                </p>
                <div className="mt-4">
                  <RatingChart dist={dist} />
                </div>
              </CardBody>
            </Card>
          )}

          <div>
            <h2 className="text-xl font-bold text-slate-900 mb-3">Reviews</h2>
            <CommentList hotelId={hotel.hotel_id} />
          </div>
        </div>

        {/* Booking sidebar */}
        <aside className="lg:sticky lg:top-24 self-start">
          <Card>
            <CardBody>
              <div className="flex items-end justify-between">
                <div>
                  <p className="text-sm text-slate-500">From</p>
                  <p className="text-2xl font-bold text-slate-900">
                    {hotel.available_rooms.length > 0
                      ? formatPrice(
                          Math.min(...hotel.available_rooms.map((r) => Number(r.price_per_night))),
                        )
                      : "-"}
                    <span className="text-sm font-normal text-slate-500"> /night</span>
                  </p>
                </div>
                {hotel.available_rooms.some((r) => r.discount_applied) && (
                  <span className="rounded-full bg-accent/10 px-3 py-1 text-xs font-semibold text-accent">
                    Member 15% off
                  </span>
                )}
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-[11px] uppercase tracking-wide text-slate-500 font-semibold">Check-in</p>
                  <p className="mt-1 font-medium text-slate-900">{checkIn || "—"}</p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-[11px] uppercase tracking-wide text-slate-500 font-semibold">Check-out</p>
                  <p className="mt-1 font-medium text-slate-900">{checkOut || "—"}</p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3 col-span-2">
                  <p className="text-[11px] uppercase tracking-wide text-slate-500 font-semibold">Guests</p>
                  <p className="mt-1 font-medium text-slate-900">{guests}</p>
                </div>
              </div>

              <p className="mt-4 text-sm text-slate-600">
                {selectedRoom ? (
                  <>
                    <span className="font-medium">{selectedRoom.room_type}</span> ·{" "}
                    {nights} {nights === 1 ? "night" : "nights"} ·{" "}
                    <span className="font-semibold text-slate-900">
                      {formatPrice(Number(selectedRoom.price_per_night) * nights)}
                    </span>
                  </>
                ) : (
                  "Select a room to continue"
                )}
              </p>

              <Button
                onClick={book}
                disabled={!selectedRoom || nights <= 0}
                loading={createBooking.isPending}
                size="lg"
                variant="accent"
                className="mt-4 w-full"
              >
                {user ? "Book now" : "Sign in to book"}
              </Button>
              {!user && (
                <p className="mt-2 text-center text-xs text-slate-500">
                  Members save 15% — <Link to="/signup" className="text-brand-600 font-medium hover:underline">sign up</Link>
                </p>
              )}
            </CardBody>
          </Card>
        </aside>
      </div>
    </div>
  );
}

function diffDays(a: string, b: string): number {
  if (!a || !b) return 0;
  const d1 = new Date(a);
  const d2 = new Date(b);
  const ms = d2.getTime() - d1.getTime();
  return Math.max(0, Math.round(ms / (1000 * 60 * 60 * 24)));
}

function AmenityIcon({ name }: { name: string }) {
  const n = name.toLowerCase();
  if (n.includes("wifi")) return <Wifi className="h-4 w-4 text-brand-600" />;
  if (n.includes("breakfast") || n.includes("coffee")) return <Coffee className="h-4 w-4 text-brand-600" />;
  return <Sparkles className="h-4 w-4 text-brand-600" />;
}
