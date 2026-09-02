/**
 * Shared TypeScript Types for AI Smart City Concierge
 * Type definitions shared between frontend and backend.
 */

// Core domain types
export interface Coordinates {
  lat: number;
  lng: number;
}

export interface Money {
  amount: number;
  currency: string;
}

export interface TimeRange {
  start: string;
  end: string;
  timezone: string;
}

export interface Rating {
  value: number;
  review_count: number;
}

export interface Address {
  street?: string;
  city?: string;
  state?: string;
  country?: string;
  postal_code?: string;
}

// API types
export interface PaginatedRequest {
  page?: number;
  page_size?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

// User types
export interface User {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  locale: string;
  timezone: string;
  email_verified: boolean;
  role: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// Conversation types
export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  content_type: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  title: string | null;
  status: string;
  message_count: number;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
}

// POI types
export interface POI {
  id: string;
  name: string;
  description: string | null;
  category: string;
  latitude: number;
  longitude: number;
  address: Record<string, unknown> | null;
  rating: number | null;
  review_count: number;
  tags: string[];
}

// Transit types
export interface TransitRoute {
  route_id: string;
  duration_minutes: number;
  transfers: number;
  steps: TransitStep[];
  fare?: number;
}

export interface TransitStep {
  type: 'walk' | 'transit';
  duration: number;
  instruction?: string;
  line?: string;
  direction?: string;
  stops?: number;
}

// Weather types
export interface WeatherData {
  lat: number;
  lng: number;
  temperature: number | null;
  humidity: number | null;
  wind_speed: number | null;
  weather_description: string | null;
}

export interface WeatherForecast {
  lat: number;
  lng: number;
  forecast: ForecastDay[];
}

export interface ForecastDay {
  date: string;
  temperature_max: number;
  temperature_min: number;
  precipitation_probability: number;
  weather_code: number;
  weather_description: string;
}

// Itinerary types
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

// WebSocket types
export interface WSMessage {
  type: string;
  payload: Record<string, unknown>;
}

// Error types
export interface APIError {
  error: {
    code: string;
    message: string;
    type?: string;
  };
}
