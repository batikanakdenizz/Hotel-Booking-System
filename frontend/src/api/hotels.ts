import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PaginatedResponse, SearchResultItem, HotelCreate, HotelResponse } from "@/types/hotel";

export interface SearchParams {
  destination: string;
  check_in: string;
  check_out: string;
  guests: number;
  page?: number;
  limit?: number;
}

export function useSearchHotels(params: SearchParams | null) {
  return useQuery({
    queryKey: ["search", params],
    queryFn: async () => {
      const r = await api.get<PaginatedResponse<SearchResultItem>>("/api/v1/search", { params });
      return r.data;
    },
    enabled: !!params,
  });
}

export function useHotelDetail(hotelId: string | undefined) {
  return useQuery({
    queryKey: ["hotel-detail", hotelId],
    queryFn: async () => {
      const r = await api.get<SearchResultItem>(`/api/v1/search/hotels/${hotelId}`);
      return r.data;
    },
    enabled: !!hotelId,
  });
}

// --- Admin -------------------------------------------------------------------

export function useAdminHotels(page = 1, limit = 20) {
  return useQuery({
    queryKey: ["admin-hotels", page, limit],
    queryFn: async () => {
      const r = await api.get<PaginatedResponse<HotelResponse>>("/api/v1/admin/hotels", { params: { page, limit } });
      return r.data;
    },
  });
}

export function useCreateHotel() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: HotelCreate) => {
      const r = await api.post<HotelResponse>("/api/v1/admin/hotels", body);
      return r.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-hotels"] }),
  });
}
