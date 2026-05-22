import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { MapPin, CalendarDays, Users, Search } from "lucide-react";
import { Button } from "@/components/ui/Button";

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
  const { register, handleSubmit, formState: { errors } } = useForm<Values>({
    resolver: zodResolver(Schema),
    defaultValues: {
      destination: initial?.destination ?? "",
      check_in: initial?.check_in ?? todayISO(1),
      check_out: initial?.check_out ?? todayISO(3),
      guests: initial?.guests ?? 2,
    },
  });

  const onSubmit = (v: Values) => {
    const qs = new URLSearchParams({
      destination: v.destination,
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
          ? "bg-white shadow-card rounded-2xl p-3 md:p-2 grid grid-cols-1 md:grid-cols-[1.4fr_1fr_1fr_0.7fr_auto] gap-2 items-stretch"
          : "bg-white border border-slate-200 rounded-xl p-2 grid grid-cols-1 md:grid-cols-[1.4fr_1fr_1fr_0.7fr_auto] gap-2 items-stretch"
      }
    >
      <Field icon={<MapPin className="h-4 w-4" />} label="Destination" error={errors.destination?.message}>
        <input
          {...register("destination")}
          placeholder="Rome, Paris, Istanbul..."
          className="w-full bg-transparent text-sm font-medium placeholder:text-slate-400 focus:outline-none"
        />
      </Field>
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
      <Button type="submit" variant="accent" size="lg" className="md:w-auto w-full">
        <Search className="h-5 w-5" /> Search
      </Button>
    </form>
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
