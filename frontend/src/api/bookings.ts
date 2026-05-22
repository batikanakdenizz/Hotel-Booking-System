import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { BookingResponse, PaginatedResponse } from "@/types/hotel";

export interface BookingCreate {
  hotel_id: string;
  room_id: string;
  check_in: string;
  check_out: string;
  guests: number;
}

export function useMyBookings() {
  return useQuery({
    queryKey: ["my-bookings"],
    queryFn: async () => {
      const r = await api.get<PaginatedResponse<BookingResponse>>("/api/v1/bookings");
      return r.data;
    },
  });
}

export function useCreateBooking() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (b: BookingCreate) => {
      const r = await api.post<BookingResponse>("/api/v1/bookings", b);
      return r.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["my-bookings"] }),
  });
}

export function useCancelBooking() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const r = await api.delete<BookingResponse>(`/api/v1/bookings/${id}`);
      return r.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["my-bookings"] }),
  });
}
