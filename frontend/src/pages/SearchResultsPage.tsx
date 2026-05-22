import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { SlidersHorizontal, Map as MapIcon, List as ListIcon } from "lucide-react";
import { SearchBar } from "@/components/SearchBar";
import { HotelCard } from "@/components/HotelCard";
import { HotelMap } from "@/components/HotelMap";
import { Spinner } from "@/components/ui/Spinner";
import { Button } from "@/components/ui/Button";
import { useSearchHotels, type SearchParams } from "@/api/hotels";

type SortKey = "best" | "price-asc" | "price-desc" | "rating-desc";

export default function SearchResultsPage() {
  const [sp] = useSearchParams();
  const [sort, setSort] = useState<SortKey>("best");
  const [showMapMobile, setShowMapMobile] = useState(false);

  const params: SearchParams | null = useMemo(() => {
    const destination = sp.get("destination");
    const check_in = sp.get("check_in");
    const check_out = sp.get("check_out");
    const guests = Number(sp.get("guests") ?? 2);
    if (!destination || !check_in || !check_out) return null;
    return { destination, check_in, check_out, guests, page: 1, limit: 20 };
  }, [sp]);

  const { data, isLoading, error } = useSearchHotels(params);

  const sortedItems = useMemo(() => {
    if (!data?.items) return [];
    const items = [...data.items];
    const minPrice = (h: typeof items[number]) =>
      h.available_rooms.reduce<number>((acc, r) => {
        const n = Number(r.price_per_night);
        return n < acc ? n : acc;
      }, Number.POSITIVE_INFINITY);
    switch (sort) {
      case "price-asc":
        return items.sort((a, b) => minPrice(a) - minPrice(b));
      case "price-desc":
        return items.sort((a, b) => minPrice(b) - minPrice(a));
      case "rating-desc":
        return items.sort((a, b) => (b.star_rating ?? 0) - (a.star_rating ?? 0));
      default:
        return items;
    }
  }, [data, sort]);

  return (
    <div className="bg-slate-50 min-h-[calc(100vh-4rem)]">
      <div className="bg-white border-b border-slate-200 px-4 py-4">
        <div className="mx-auto max-w-7xl">
          <SearchBar
            variant="compact"
            initial={{
              destination: sp.get("destination") ?? "",
              check_in: sp.get("check_in") ?? undefined,
              check_out: sp.get("check_out") ?? undefined,
              guests: sp.get("guests") ? Number(sp.get("guests")) : undefined,
            }}
          />
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-6 grid lg:grid-cols-[1fr_420px] gap-6">
        {/* Results column */}
        <div>
          <div className="flex items-center justify-between gap-2">
            <h1 className="text-2xl font-bold text-slate-900">
              {params?.destination ?? "Search"}{" "}
              <span className="text-sm font-normal text-slate-500">
                {data ? `· ${data.total} stays` : ""}
              </span>
            </h1>
            <div className="flex items-center gap-2">
              <label className="hidden md:flex items-center gap-2 text-sm text-slate-600">
                <SlidersHorizontal className="h-4 w-4" />
                <select
                  className="rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm"
                  value={sort}
                  onChange={(e) => setSort(e.target.value as SortKey)}
                >
                  <option value="best">Best match</option>
                  <option value="price-asc">Price (low to high)</option>
                  <option value="price-desc">Price (high to low)</option>
                  <option value="rating-desc">Star rating</option>
                </select>
              </label>
              <Button
                size="sm"
                variant="outline"
                className="lg:hidden"
                onClick={() => setShowMapMobile((s) => !s)}
              >
                {showMapMobile ? <ListIcon className="h-4 w-4" /> : <MapIcon className="h-4 w-4" />}
                {showMapMobile ? "List" : "Map"}
              </Button>
            </div>
          </div>

          {!params && (
            <p className="mt-8 text-slate-500">Enter a destination to start searching.</p>
          )}
          {isLoading && (
            <div className="grid place-items-center py-20">
              <Spinner />
            </div>
          )}
          {error && (
            <p className="mt-8 text-red-600">Search failed. Please try again.</p>
          )}
          {!isLoading && data && sortedItems.length === 0 && (
            <div className="mt-12 rounded-2xl bg-white p-10 text-center shadow-card">
              <p className="text-slate-700 font-semibold">No hotels available for these dates.</p>
              <p className="mt-1 text-sm text-slate-500">Try changing the destination or dates above.</p>
            </div>
          )}

          <div className={showMapMobile ? "hidden lg:block mt-4 space-y-4" : "mt-4 space-y-4"}>
            {sortedItems.map((h) => (
              <HotelCard key={h.hotel_id} hotel={h} searchQuery={sp.toString()} />
            ))}
          </div>
        </div>

        {/* Map column */}
        <aside
          className={
            "h-[70vh] lg:h-[calc(100vh-12rem)] lg:sticky lg:top-24 " +
            (showMapMobile ? "block" : "hidden lg:block")
          }
        >
          <div className="h-full overflow-hidden rounded-2xl shadow-card bg-white">
            <HotelMap hotels={sortedItems} />
          </div>
        </aside>
      </div>
    </div>
  );
}
