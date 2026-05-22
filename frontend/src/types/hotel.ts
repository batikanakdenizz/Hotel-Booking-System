// Mirrors shared.schemas on the backend.

export interface AvailableRoom {
  room_id: string;
  room_type: string;
  capacity: number;
  available_count: number;
  original_price: string;
  price_per_night: string;
  discount_applied: boolean;
}

export interface SearchResultItem {
  hotel_id: string;
  name: string;
  description: string | null;
  destination: string;
  address: string;
  latitude: number;
  longitude: number;
  star_rating: number | null;
  amenities: string[];
  image_url: string | null;
  available_rooms: AvailableRoom[];
}

export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  limit: number;
  total: number;
}

export interface HotelCreate {
  name: string;
  description?: string;
  destination: string;
  address: string;
  latitude: number;
  longitude: number;
  admin_email: string;
  star_rating?: number | null;
  amenities?: string[];
}

export interface HotelResponse extends HotelCreate {
  id: string;
  created_at: string;
  updated_at: string;
}

export interface BookingResponse {
  id: string;
  user_id: string;
  hotel_id: string;
  room_id: string;
  check_in: string;
  check_out: string;
  guests: number;
  total_price: string;
  status: "confirmed" | "cancelled";
  created_at: string;
  notification_dispatched: boolean;
}

export interface CommentResponse {
  id: string;
  hotel_id: string;
  user_id: string;
  user_display_name: string | null;
  text: string;
  ratings: {
    cleanliness: number;
    staff: number;
    amenities: number;
    comfort: number;
    eco_friendliness: number;
  };
  overall_rating: number;
  created_at: string;
}

export interface RatingDistribution {
  total_comments: number;
  avg_cleanliness: number | null;
  avg_staff: number | null;
  avg_amenities: number | null;
  avg_comfort: number | null;
  avg_eco_friendliness: number | null;
  avg_overall: number | null;
  breakdown: Record<string, number>;
}
