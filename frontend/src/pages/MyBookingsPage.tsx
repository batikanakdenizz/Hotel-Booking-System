import { toast } from "sonner";
import { Link } from "react-router-dom";
import { CalendarDays, Users, X, CheckCircle2, XCircle } from "lucide-react";
import { useMyBookings, useCancelBooking } from "@/api/bookings";
import { Spinner } from "@/components/ui/Spinner";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { formatDate, formatPrice } from "@/lib/utils";

export default function MyBookingsPage() {
  const { data, isLoading, error } = useMyBookings();
  const cancel = useCancelBooking();

  async function onCancel(id: string) {
    if (!window.confirm("Cancel this booking?")) return;
    try {
      await cancel.mutateAsync(id);
      toast.success("Booking cancelled");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Cancel failed");
    }
  }

  return (
    <div className="bg-slate-50 min-h-[calc(100vh-4rem)]">
      <div className="mx-auto max-w-5xl px-4 py-8">
        <h1 className="text-3xl font-bold text-slate-900">My bookings</h1>
        <p className="mt-1 text-slate-500">All your reservations in one place.</p>

        {isLoading && (
          <div className="grid place-items-center py-16"><Spinner /></div>
        )}
        {error && <p className="mt-6 text-red-600">Failed to load bookings.</p>}

        {data && data.items.length === 0 && (
          <Card className="mt-8">
            <CardBody className="text-center py-12">
              <p className="text-slate-700 font-semibold">You don't have any bookings yet.</p>
              <Link to="/" className="mt-4 inline-block">
                <Button variant="primary">Start exploring</Button>
              </Link>
            </CardBody>
          </Card>
        )}

        <ul className="mt-6 space-y-4">
          {data?.items.map((b) => {
            const isCancelled = b.status === "cancelled";
            const isPast = new Date(b.check_out) < new Date();
            return (
              <li key={b.id}>
                <Card>
                  <CardBody>
                    <div className="flex items-start justify-between gap-4 flex-wrap">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          {isCancelled ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-xs font-semibold text-red-700">
                              <XCircle className="h-3.5 w-3.5" /> Cancelled
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700">
                              <CheckCircle2 className="h-3.5 w-3.5" /> Confirmed
                            </span>
                          )}
                          {b.notification_dispatched && (
                            <span className="text-[11px] text-slate-400">Notification sent</span>
                          )}
                        </div>
                        <Link
                          to={`/hotels/${b.hotel_id}`}
                          className="mt-2 inline-block text-lg font-bold text-slate-900 hover:text-brand-700"
                        >
                          Hotel {b.hotel_id.slice(0, 8)}…
                        </Link>
                        <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
                          <Detail icon={<CalendarDays className="h-4 w-4" />} label="Check-in" value={formatDate(b.check_in)} />
                          <Detail icon={<CalendarDays className="h-4 w-4" />} label="Check-out" value={formatDate(b.check_out)} />
                          <Detail icon={<Users className="h-4 w-4" />} label="Guests" value={String(b.guests)} />
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-slate-500">Total</p>
                        <p className="text-2xl font-bold text-slate-900">{formatPrice(b.total_price)}</p>
                        {!isCancelled && !isPast && (
                          <Button
                            variant="danger"
                            size="sm"
                            className="mt-3"
                            loading={cancel.isPending}
                            onClick={() => onCancel(b.id)}
                          >
                            <X className="h-4 w-4" /> Cancel
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardBody>
                </Card>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

function Detail({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <p className="flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-slate-500 font-semibold">
        {icon} {label}
      </p>
      <p className="mt-1 font-medium text-slate-900">{value}</p>
    </div>
  );
}
