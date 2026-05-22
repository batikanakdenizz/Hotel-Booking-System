import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { CommentResponse, PaginatedResponse, RatingDistribution } from "@/types/hotel";

export function useHotelComments(hotelId: string | undefined) {
  return useQuery({
    queryKey: ["comments", hotelId],
    queryFn: async () => {
      const r = await api.get<PaginatedResponse<CommentResponse>>(`/api/v1/comments/hotels/${hotelId}`);
      return r.data;
    },
    enabled: !!hotelId,
  });
}

export function useHotelDistribution(hotelId: string | undefined) {
  return useQuery({
    queryKey: ["comments-dist", hotelId],
    queryFn: async () => {
      const r = await api.get<RatingDistribution>(`/api/v1/comments/hotels/${hotelId}/distribution`);
      return r.data;
    },
    enabled: !!hotelId,
  });
}

export interface CommentCreate {
  hotel_id: string;
  text: string;
  ratings: {
    cleanliness: number; staff: number; amenities: number; comfort: number; eco_friendliness: number;
  };
}

export function useCreateComment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (c: CommentCreate) => (await api.post("/api/v1/comments", c)).data,
    onSuccess: (_d, vars) => {
      qc.invalidateQueries({ queryKey: ["comments", vars.hotel_id] });
      qc.invalidateQueries({ queryKey: ["comments-dist", vars.hotel_id] });
    },
  });
}
