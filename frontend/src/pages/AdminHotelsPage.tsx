import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Plus, Building2, MapPin, Star } from "lucide-react";
import { useAdminHotels, useCreateHotel } from "@/api/hotels";
import { Spinner } from "@/components/ui/Spinner";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardBody } from "@/components/ui/Card";

const Schema = z.object({
  name: z.string().min(2),
  description: z.string().optional(),
  destination: z.string().min(2),
  address: z.string().min(2),
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180),
  admin_email: z.string().email(),
  star_rating: z.number().min(1).max(5).optional(),
  amenities_csv: z.string().optional(),
});
type Values = z.infer<typeof Schema>;

export default function AdminHotelsPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, error } = useAdminHotels(page, 20);
  const create = useCreateHotel();
  const [showForm, setShowForm] = useState(false);

  const { register, handleSubmit, formState: { errors }, reset } = useForm<Values>({
    resolver: zodResolver(Schema),
    defaultValues: { star_rating: 4 },
  });

  const onCreate = async (v: Values) => {
    try {
      await create.mutateAsync({
        name: v.name,
        description: v.description,
        destination: v.destination,
        address: v.address,
        latitude: v.latitude,
        longitude: v.longitude,
        admin_email: v.admin_email,
        star_rating: v.star_rating ?? null,
        amenities: v.amenities_csv
          ? v.amenities_csv.split(",").map((x) => x.trim()).filter(Boolean)
          : [],
      });
      toast.success("Hotel created");
      reset();
      setShowForm(false);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Create failed (admin role required?)");
    }
  };

  return (
    <div className="bg-slate-50 min-h-[calc(100vh-4rem)]">
      <div className="mx-auto max-w-6xl px-4 py-8">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Admin · Hotels</h1>
            <p className="mt-1 text-slate-500">Create and manage hotels. Admin role required.</p>
          </div>
          <Button onClick={() => setShowForm((s) => !s)}>
            <Plus className="h-4 w-4" /> {showForm ? "Close" : "New hotel"}
          </Button>
        </div>

        {showForm && (
          <Card className="mt-6">
            <CardBody>
              <form onSubmit={handleSubmit(onCreate)} className="grid md:grid-cols-2 gap-4">
                <Input label="Name" error={errors.name?.message} {...register("name")} />
                <Input label="Destination" error={errors.destination?.message} {...register("destination")} />
                <Input label="Address" error={errors.address?.message} {...register("address")} className="md:col-span-2" />
                <Input label="Latitude" type="number" step="any" error={errors.latitude?.message} {...register("latitude", { valueAsNumber: true })} />
                <Input label="Longitude" type="number" step="any" error={errors.longitude?.message} {...register("longitude", { valueAsNumber: true })} />
                <Input label="Admin email" type="email" error={errors.admin_email?.message} {...register("admin_email")} />
                <Input label="Star rating (1–5)" type="number" step="1" min={1} max={5} error={errors.star_rating?.message} {...register("star_rating", { valueAsNumber: true })} />
                <Input
                  label="Amenities (comma-separated)"
                  placeholder="WiFi, Breakfast, Pool"
                  error={errors.amenities_csv?.message}
                  className="md:col-span-2"
                  {...register("amenities_csv")}
                />
                <div className="md:col-span-2">
                  <label className="mb-1 block text-sm font-medium text-slate-700">Description</label>
                  <textarea
                    rows={3}
                    {...register("description")}
                    className="w-full rounded-lg border border-slate-300 bg-white p-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div className="md:col-span-2 flex gap-2">
                  <Button type="submit" loading={create.isPending}>Create</Button>
                  <Button type="button" variant="ghost" onClick={() => setShowForm(false)}>Cancel</Button>
                </div>
              </form>
            </CardBody>
          </Card>
        )}

        {isLoading && <div className="grid place-items-center py-12"><Spinner /></div>}
        {error && (
          <Card className="mt-6">
            <CardBody>
              <p className="text-red-600 font-semibold">Failed to load hotels.</p>
              <p className="text-sm text-slate-500 mt-1">Make sure you have an admin role in Postgres (`users.role = 'admin'`).</p>
            </CardBody>
          </Card>
        )}

        {data && (
          <>
            <ul className="mt-6 grid md:grid-cols-2 gap-4">
              {data.items.map((h) => (
                <li key={h.id}>
                  <Card>
                    <CardBody>
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h3 className="font-bold text-slate-900 flex items-center gap-2">
                            <Building2 className="h-4 w-4 text-brand-600" /> {h.name}
                          </h3>
                          <p className="mt-1 flex items-center gap-1 text-sm text-slate-500">
                            <MapPin className="h-3.5 w-3.5" /> {h.destination}
                          </p>
                        </div>
                        {h.star_rating != null && (
                          <span className="flex items-center gap-1 text-sm font-semibold text-amber-600">
                            <Star className="h-4 w-4 fill-current" /> {h.star_rating}
                          </span>
                        )}
                      </div>
                      <p className="mt-2 text-sm text-slate-600 line-clamp-2">{h.description}</p>
                      <p className="mt-2 text-xs text-slate-400">ID: {h.id}</p>
                    </CardBody>
                  </Card>
                </li>
              ))}
            </ul>

            <div className="mt-6 flex items-center justify-between text-sm text-slate-600">
              <span>
                Page {data.page} · {data.items.length} of {data.total}
              </span>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Prev</Button>
                <Button variant="outline" size="sm" disabled={data.items.length < data.limit} onClick={() => setPage((p) => p + 1)}>Next</Button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
