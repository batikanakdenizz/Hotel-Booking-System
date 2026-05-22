import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip } from "recharts";
import type { RatingDistribution } from "@/types/hotel";

export function RatingChart({ dist }: { dist: RatingDistribution }) {
  const data = [
    { dim: "Cleanliness", value: dist.avg_cleanliness ?? 0 },
    { dim: "Staff", value: dist.avg_staff ?? 0 },
    { dim: "Amenities", value: dist.avg_amenities ?? 0 },
    { dim: "Comfort", value: dist.avg_comfort ?? 0 },
    { dim: "Eco", value: dist.avg_eco_friendliness ?? 0 },
  ];
  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
          <XAxis type="number" domain={[0, 10]} tick={{ fontSize: 11, fill: "#64748b" }} />
          <YAxis dataKey="dim" type="category" width={90} tick={{ fontSize: 12, fill: "#0f172a" }} />
          <Tooltip cursor={{ fill: "#f1f5f9" }} formatter={(v) => (typeof v === "number" ? v.toFixed(1) : String(v))} />
          <Bar dataKey="value" fill="#21589a" radius={[0, 6, 6, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
