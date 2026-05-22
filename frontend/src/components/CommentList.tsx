import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Star, User as UserIcon, PenLine } from "lucide-react";
import { useHotelComments, useCreateComment } from "@/api/comments";
import { Spinner } from "@/components/ui/Spinner";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { formatDate } from "@/lib/utils";

const DIMS = ["cleanliness", "staff", "amenities", "comfort", "eco_friendliness"] as const;
type Dim = (typeof DIMS)[number];

const Schema = z.object({
  text: z.string().min(8, "Write at least 8 characters").max(2000),
  cleanliness: z.number().min(1).max(10),
  staff: z.number().min(1).max(10),
  amenities: z.number().min(1).max(10),
  comfort: z.number().min(1).max(10),
  eco_friendliness: z.number().min(1).max(10),
});
type Values = z.infer<typeof Schema>;

const LABELS: Record<Dim, string> = {
  cleanliness: "Cleanliness",
  staff: "Staff",
  amenities: "Amenities",
  comfort: "Comfort",
  eco_friendliness: "Eco-friendly",
};

export function CommentList({ hotelId }: { hotelId: string }) {
  const { user } = useAuth();
  const { data, isLoading } = useHotelComments(hotelId);
  const create = useCreateComment();
  const { register, handleSubmit, formState: { errors }, reset } = useForm<Values>({
    resolver: zodResolver(Schema),
    defaultValues: { text: "", cleanliness: 8, staff: 8, amenities: 8, comfort: 8, eco_friendliness: 8 },
  });

  const onSubmit = async (v: Values) => {
    try {
      await create.mutateAsync({
        hotel_id: hotelId,
        text: v.text,
        ratings: {
          cleanliness: v.cleanliness,
          staff: v.staff,
          amenities: v.amenities,
          comfort: v.comfort,
          eco_friendliness: v.eco_friendliness,
        },
      });
      toast.success("Comment posted");
      reset();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Failed to post comment");
    }
  };

  return (
    <div className="space-y-6">
      {user && (
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="rounded-2xl bg-white shadow-card p-5 space-y-4"
        >
          <div className="flex items-center gap-2 font-semibold text-slate-900">
            <PenLine className="h-4 w-4 text-brand-600" /> Leave a review
          </div>
          <textarea
            {...register("text")}
            rows={3}
            placeholder="Share your experience..."
            className="w-full rounded-lg border border-slate-300 bg-white p-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          {errors.text && <p className="text-xs text-red-600">{errors.text.message}</p>}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {DIMS.map((d) => (
              <label key={d} className="text-xs text-slate-600">
                <span className="block mb-1 font-medium">{LABELS[d]} (1–10)</span>
                <input
                  type="number"
                  min={1}
                  max={10}
                  {...register(d, { valueAsNumber: true })}
                  className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </label>
            ))}
          </div>
          <Button type="submit" loading={create.isPending}>Post review</Button>
        </form>
      )}

      {isLoading && <div className="grid place-items-center py-8"><Spinner /></div>}
      {data && data.items.length === 0 && (
        <p className="text-slate-500 text-sm">No reviews yet. Be the first to write one.</p>
      )}
      <ul className="space-y-3">
        {data?.items.map((c) => (
          <li key={c.id} className="rounded-2xl bg-white shadow-card p-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="rounded-full bg-brand-100 p-2 text-brand-700"><UserIcon className="h-4 w-4" /></div>
                <span className="font-medium text-slate-900">{c.user_display_name || "Anonymous"}</span>
              </div>
              <div className="flex items-center gap-1 text-sm font-semibold text-amber-600">
                <Star className="h-4 w-4 fill-current" /> {c.overall_rating.toFixed(1)}
              </div>
            </div>
            <p className="mt-2 text-sm text-slate-700">{c.text}</p>
            <p className="mt-2 text-xs text-slate-400">{formatDate(c.created_at)}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
