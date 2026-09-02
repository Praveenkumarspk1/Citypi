export interface Itinerary {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  status: string;
  start_date: string | null;
  end_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface ItineraryDay {
  id: string;
  itinerary_id: string;
  day_number: number;
  date: string | null;
  title: string | null;
  items: ItineraryItem[];
}

export interface ItineraryItem {
  id: string;
  day_id: string;
  poi_id: string | null;
  custom_name: string | null;
  start_time: string | null;
  end_time: string | null;
  duration_minutes: number;
  order_index: number;
  travel_time_minutes: number;
  transport_mode: string | null;
}

export interface CreateItineraryParams {
  title: string;
  description?: string;
  start_date?: string;
  end_date?: string;
  timezone?: string;
}
