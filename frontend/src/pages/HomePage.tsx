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
      <section className="relative overflow-hidden">
        <div
          className="absolute inset-0 bg-gradient-to-br from-brand-900 via-brand-700 to-brand-500"
          aria-hidden="true"
        />
        {/* Radial spotlight to draw attention to the centered headline */}
        <div
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 80% 60% at 50% 25%, rgba(255,255,255,0.18), transparent 70%)",
          }}
          aria-hidden="true"
        />
        <div className="absolute inset-0 opacity-25 mix-blend-overlay"
          style={{
            backgroundImage:
              "url('https://images.unsplash.com/photo-1455587734955-081b22074882?auto=format&fit=crop&w=1600&q=70')",
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
          aria-hidden="true"
        />
        <div className="absolute inset-0 grain-overlay" aria-hidden="true" />
        {/* Subtle vignette at the bottom edge */}
        <div
          className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-b from-transparent to-slate-50/40"
          aria-hidden="true"
        />
        <div className="relative mx-auto max-w-6xl px-4 pt-16 pb-32 text-center text-white animate-fade-in-up">
          <p className="text-sm uppercase tracking-[0.3em] text-brand-100/90">Stayfinder</p>
          <h1 className="mt-3 text-4xl md:text-6xl font-bold leading-tight tracking-tight">
            Find your next stay,<br className="hidden md:block" /> from city breaks to weekend escapes.
          </h1>
          <p className="mt-4 text-lg text-brand-100/90 max-w-2xl mx-auto">
            Compare hotels across destinations, with member discounts and AI-powered search.
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
      <section className="mx-auto max-w-6xl px-4 py-16">
        <h2 className="text-2xl font-bold text-slate-900">Popular destinations</h2>
        <p className="mt-1 text-slate-500">Hand-picked cities worth exploring this season.</p>
        <div className="mt-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
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
                className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent" />
              <span className="absolute bottom-3 left-4 text-white font-semibold text-lg drop-shadow">{d.name}</span>
            </Link>
          ))}
        </div>
      </section>

      {/* Value props */}
      <section className="mx-auto max-w-6xl px-4 pb-20">
        <div className="grid md:grid-cols-3 gap-4">
          <Value
            icon={<ShieldCheck className="h-6 w-6 text-brand-600" />}
            title="Trusted bookings"
            text="Firebase-backed auth & secure payment workflow."
          />
          <Value
            icon={<Sparkles className="h-6 w-6 text-accent" />}
            title="15% member discount"
            text="Sign in for instant savings on every booking."
          />
          <Value
            icon={<MessageCircle className="h-6 w-6 text-brand-600" />}
            title="AI travel concierge"
            text="Chat with our agent to find hotels in natural language."
          />
        </div>
      </section>

      {/* Footer banner */}
      <footer className="bg-slate-900 text-slate-300 py-8">
        <div className="mx-auto max-w-6xl px-4 flex items-center justify-between">
          <span className="flex items-center gap-2 font-semibold text-white">
            <Building2 className="h-5 w-5" /> Stayfinder
          </span>
          <span className="text-sm text-slate-400">SE 4458 — Final project</span>
        </div>
      </footer>
    </div>
  );
}

function Value({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <div className="bg-white rounded-2xl shadow-card p-6 flex flex-col items-start transition-all duration-300 hover:-translate-y-0.5 hover:shadow-card-md">
      <div className="rounded-xl bg-slate-100 p-3">{icon}</div>
      <h3 className="mt-4 font-semibold text-slate-900">{title}</h3>
      <p className="mt-1 text-sm text-slate-500">{text}</p>
    </div>
  );
}

function todayISO(offset = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + offset);
  return d.toISOString().slice(0, 10);
}
