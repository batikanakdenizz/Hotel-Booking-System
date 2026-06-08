import { Link } from "react-router-dom";
import { ShieldCheck, Sparkles, MessageCircle, Building2 } from "lucide-react";
import { SearchBar } from "@/components/SearchBar";

// Mirrors the cities seeded in scripts/seed_demo_data.py so every card returns
// at least one hotel when clicked.
const FEATURED_DESTINATIONS = [
  { name: "Rome", image: "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=800&q=70" },
  { name: "Paris", image: "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=800&q=70" },
  { name: "Istanbul", image: "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=800&q=70" },
  { name: "Barcelona", image: "https://images.unsplash.com/photo-1583422409516-2895a77efded?auto=format&fit=crop&w=800&q=70" },
  { name: "New York", image: "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?auto=format&fit=crop&w=800&q=70" },
  { name: "Tokyo", image: "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=800&q=70" },
  { name: "Bodrum", image: "https://images.unsplash.com/photo-1602391833977-358a52198938?auto=format&fit=crop&w=800&q=70" },
];

export default function HomePage() {
  return (
    <div className="bg-slate-50 min-h-[calc(100vh-4rem)]">
      {/* Hero */}
      <section className="relative overflow-hidden min-h-[78vh] flex flex-col justify-end">
        {/* Cinematic full-bleed background with subtle Ken Burns zoom */}
        <div
          className="absolute inset-0 animate-subtle-zoom"
          style={{
            backgroundImage:
              "url('https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=2000&q=80')",
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
          aria-hidden="true"
        />
        {/* Layered darkening so the headline always reads, regardless of photo */}
        <div
          className="absolute inset-0 bg-gradient-to-b from-brand-900/70 via-brand-900/45 to-brand-900/85"
          aria-hidden="true"
        />
        <div
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 70% 50% at 50% 35%, rgba(201,169,110,0.18), transparent 65%)",
          }}
          aria-hidden="true"
        />
        <div className="absolute inset-0 grain-overlay" aria-hidden="true" />
        {/* Soft fade into the page background at the bottom edge */}
        <div
          className="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-b from-transparent to-slate-50"
          aria-hidden="true"
        />

        <div className="relative mx-auto max-w-6xl px-4 pt-24 pb-40 text-center text-white animate-fade-in-up">
          <p className="text-xs md:text-sm uppercase tracking-[0.4em] text-accent/90 font-semibold">
            — Stayfinder —
          </p>
          <h1 className="mt-5 text-5xl md:text-7xl font-bold leading-[1.05] tracking-tight">
            Find your next{" "}
            <span className="font-serif italic font-medium text-accent">escape</span>,
            <br className="hidden md:block" />
            from city breaks to coastal retreats.
          </h1>
          <p className="mt-6 text-base md:text-lg text-slate-200/90 max-w-2xl mx-auto leading-relaxed">
            Curated stays across the world's most loved destinations, with member discounts and an AI concierge that books for you.
          </p>
        </div>
      </section>

      {/* Search card overlapping hero */}
      <section className="relative -mt-24 px-4">
        <div className="mx-auto max-w-5xl">
          <SearchBar variant="hero" />
        </div>
      </section>

      {/* Featured destinations */}
      <section className="mx-auto max-w-6xl px-4 py-20">
        <div className="flex items-end justify-between gap-4 mb-2">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-accent-dark font-semibold">Destinations</p>
            <h2 className="mt-2 text-3xl md:text-4xl font-bold text-slate-900 tracking-tight">
              Where to <span className="font-serif italic font-medium">next</span>?
            </h2>
            <p className="mt-2 text-slate-500 max-w-xl">Hand-picked cities worth exploring this season — from Aegean coastlines to Pacific skylines.</p>
          </div>
        </div>
        <div className="mt-8 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
          {FEATURED_DESTINATIONS.map((d) => (
            <Link
              key={d.name}
              to={`/search?destination=${encodeURIComponent(d.name)}&check_in=${todayISO(1)}&check_out=${todayISO(3)}&guests=2`}
              className="group relative overflow-hidden rounded-2xl shadow-card aspect-[4/5] transition-all duration-300 hover:-translate-y-1 hover:shadow-card-lg"
            >
              <img
                src={d.image}
                alt={d.name}
                loading="lazy"
                className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-110"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-brand-900/80 via-brand-900/15 to-transparent" />
              {/* Hover-revealed gold underline */}
              <div className="absolute bottom-4 left-5 right-5">
                <span className="block text-white font-semibold text-xl drop-shadow tracking-tight">{d.name}</span>
                <span className="mt-1 block h-[2px] w-8 bg-accent transition-all duration-300 group-hover:w-16" />
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Value props */}
      <section className="mx-auto max-w-6xl px-4 pb-24">
        <div className="grid md:grid-cols-3 gap-5">
          <Value
            icon={<ShieldCheck className="h-6 w-6 text-accent" />}
            title="Trusted bookings"
            text="Firebase-backed auth and a transactional booking engine that never double-books."
          />
          <Value
            icon={<Sparkles className="h-6 w-6 text-accent" />}
            title="15% member discount"
            text="Sign in and every nightly rate drops by 15% — automatically, at checkout."
          />
          <Value
            icon={<MessageCircle className="h-6 w-6 text-accent" />}
            title="AI travel concierge"
            text="Tell our concierge what you want in natural language. It searches and books for you."
          />
        </div>
      </section>

      {/* Footer banner */}
      <footer className="bg-brand-900 text-slate-300 py-10 border-t border-accent/20">
        <div className="mx-auto max-w-6xl px-4 flex flex-col md:flex-row gap-3 md:items-center md:justify-between">
          <div className="flex items-center gap-2 font-semibold text-white tracking-tight">
            <Building2 className="h-5 w-5 text-accent" />
            <span className="font-serif italic text-lg">Stayfinder</span>
          </div>
          <span className="text-sm text-slate-400">SE 4458 — Final project · Crafted with care.</span>
        </div>
      </footer>
    </div>
  );
}

function Value({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <div className="group bg-white rounded-2xl shadow-card p-7 flex flex-col items-start transition-all duration-300 hover:-translate-y-0.5 hover:shadow-card-md border border-slate-100">
      <div className="rounded-xl bg-accent/10 p-3 ring-1 ring-accent/20 transition-colors group-hover:bg-accent/15">{icon}</div>
      <h3 className="mt-5 font-semibold text-slate-900 text-lg tracking-tight">{title}</h3>
      <p className="mt-1.5 text-sm text-slate-500 leading-relaxed">{text}</p>
    </div>
  );
}

function todayISO(offset = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + offset);
  return d.toISOString().slice(0, 10);
}
