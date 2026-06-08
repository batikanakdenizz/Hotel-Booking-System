import { useEffect, useMemo, useRef, useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { MapPin, CalendarDays, Users, Search } from "lucide-react";
import { Button } from "@/components/ui/Button";

// Canonical list mirrors `scripts/seed_demo_data.py` so picking from the
// dropdown always sends a destination string the backend can match.
const KNOWN_DESTINATIONS = [
  "Barcelona",
  "Bodrum",
  "Istanbul",
  "New York",
  "Paris",
  "Rome",
  "Tokyo",
];

// Accent/case/dotless-I-tolerant normalisation. Maps İstanbul/istanbul/İSTANBUL
// to the same key so the user sees a hit no matter how they typed it.
function _normalize(s: string): string {
  return s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")  // strip combining diacritics
    .replace(/[ıİ]/g, "i")            // Turkish dotless/dotted I -> i
    .toLowerCase()
    .trim();
}

const Schema = z
  .object({
    destination: z.string().min(2, "Where to?"),
    check_in: z.string().min(1, "Pick date"),
    check_out: z.string().min(1, "Pick date"),
    guests: z.number().int().min(1).max(10),
  })
  .refine((v) => new Date(v.check_out) > new Date(v.check_in), {
    path: ["check_out"],
    message: "Check-out must be after check-in",
  });
type Values = z.infer<typeof Schema>;

export interface SearchBarProps {
  initial?: Partial<Values>;
  variant?: "hero" | "compact";
}

function todayISO(offset = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + offset);
  return d.toISOString().slice(0, 10);
}

export function SearchBar({ initial, variant = "hero" }: SearchBarProps) {
  const navigate = useNavigate();
  const { register, handleSubmit, formState: { errors }, control, setValue } = useForm<Values>({
    resolver: zodResolver(Schema),
    defaultValues: {
      destination: initial?.destination ?? "",
      check_in: initial?.check_in ?? todayISO(1),
      check_out: initial?.check_out ?? todayISO(3),
      guests: initial?.guests ?? 2,
    },
  });

  const onSubmit = (v: Values) => {
    // Always submit the canonical spelling -- map whatever the user typed
    // back to the matching entry in KNOWN_DESTINATIONS when possible.
    const canonical =
      KNOWN_DESTINATIONS.find((d) => _normalize(d) === _normalize(v.destination)) ?? v.destination;
    const qs = new URLSearchParams({
      destination: canonical,
      check_in: v.check_in,
      check_out: v.check_out,
      guests: String(v.guests),
    });
    navigate(`/search?${qs.toString()}`);
  };

  const isHero = variant === "hero";

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className={
        isHero
          ? "bg-white shadow-card-md rounded-2xl p-3 md:p-2 grid grid-cols-1 md:grid-cols-[1.4fr_1fr_1fr_0.7fr_auto] gap-2 items-stretch ring-1 ring-accent/15"
          : "bg-white border border-brand-100 rounded-xl p-2 grid grid-cols-1 md:grid-cols-[1.4fr_1fr_1fr_0.7fr_auto] gap-2 items-stretch"
      }
    >
      <Controller
        control={control}
        name="destination"
        render={({ field }) => (
          <DestinationField
            value={field.value}
            onChange={field.onChange}
            onPick={(city) => setValue("destination", city, { shouldValidate: true })}
            error={errors.destination?.message}
          />
        )}
      />
      <Field icon={<CalendarDays className="h-4 w-4" />} label="Check-in" error={errors.check_in?.message}>
        <input type="date" {...register("check_in")} className="w-full bg-transparent text-sm font-medium focus:outline-none" />
      </Field>
      <Field icon={<CalendarDays className="h-4 w-4" />} label="Check-out" error={errors.check_out?.message}>
        <input type="date" {...register("check_out")} className="w-full bg-transparent text-sm font-medium focus:outline-none" />
      </Field>
      <Field icon={<Users className="h-4 w-4" />} label="Guests" error={errors.guests?.message}>
        <input
          type="number"
          min={1}
          max={10}
          {...register("guests", { valueAsNumber: true })}
          className="w-full bg-transparent text-sm font-medium focus:outline-none"
        />
      </Field>
      <Button type="submit" variant="primary" size="lg" className="md:w-auto w-full">
        <Search className="h-5 w-5" /> Search
      </Button>
    </form>
  );
}

interface DestinationFieldProps {
  value: string;
  onChange: (v: string) => void;
  onPick: (city: string) => void;
  error?: string;
}

function DestinationField({ value, onChange, onPick, error }: DestinationFieldProps) {
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const suggestions = useMemo(() => {
    const q = _normalize(value);
    if (!q) return KNOWN_DESTINATIONS;          // show all when empty
    return KNOWN_DESTINATIONS.filter((d) => _normalize(d).includes(q));
  }, [value]);

  // Close on outside click.
  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  // Reset highlight when suggestion list changes.
  useEffect(() => {
    setHighlight(0);
  }, [suggestions.length]);

  function commit(city: string) {
    onPick(city);
    setOpen(false);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!open || suggestions.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => (h + 1) % suggestions.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => (h - 1 + suggestions.length) % suggestions.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      commit(suggestions[highlight]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  }

  return (
    <div ref={wrapperRef} className="relative">
      <Field icon={<MapPin className="h-4 w-4" />} label="Destination" error={error}>
        <input
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder="Rome, Paris, Istanbul..."
          autoComplete="off"
          spellCheck={false}
          className="w-full bg-transparent text-sm font-medium placeholder:text-slate-400 focus:outline-none"
        />
      </Field>
      {open && suggestions.length > 0 && (
        <ul
          role="listbox"
          className="absolute left-0 right-0 top-full mt-1 z-30 max-h-64 overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-lg"
        >
          {suggestions.map((d, i) => (
            <li
              key={d}
              role="option"
              aria-selected={i === highlight}
              onMouseDown={(e) => {
                // Use mousedown so the click registers before input blur.
                e.preventDefault();
                commit(d);
              }}
              onMouseEnter={() => setHighlight(i)}
              className={
                "flex items-center gap-2 px-3 py-2 text-sm cursor-pointer " +
                (i === highlight ? "bg-brand-50 text-brand-700" : "text-slate-700 hover:bg-slate-50")
              }
            >
              <MapPin className="h-4 w-4 text-slate-400" />
              {d}
            </li>
          ))}
        </ul>
      )}
      {open && suggestions.length === 0 && value.trim() !== "" && (
        <div className="absolute left-0 right-0 top-full mt-1 z-30 rounded-xl border border-slate-200 bg-white shadow-lg px-3 py-2 text-xs text-slate-500">
          No match — try one of: {KNOWN_DESTINATIONS.join(", ")}.
        </div>
      )}
    </div>
  );
}

function Field({
  icon,
  label,
  children,
  error,
}: {
  icon: React.ReactNode;
  label: string;
  children: React.ReactNode;
  error?: string;
}) {
  return (
    <label className="flex flex-col rounded-lg border border-transparent bg-slate-50 px-3 py-2 hover:bg-slate-100 transition-colors cursor-text">
      <span className="flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-slate-500 font-semibold">
        {icon}
        {label}
      </span>
      <div className="mt-0.5">{children}</div>
      {error && <span className="mt-0.5 text-[11px] text-red-600">{error}</span>}
    </label>
  );
}
