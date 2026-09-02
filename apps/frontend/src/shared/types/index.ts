/**
 * Shared TypeScript types for the frontend
 */

// User types
export interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
  locale: string;
  timezone: string;
  interests: string[];
  budget_level: 'budget' | 'mid_range' | 'luxury';
  accessibility_needs: string[];
  dietary_restrictions: string[];
  preferred_transport_modes: TransportMode[];
  role: 'user' | 'admin' | 'moderator' | 'premium';
  status: 'active' | 'inactive' | 'suspended' | 'pending_verification';
  email_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
}

export type TransportMode = 
  | 'walking' 
  | 'cycling' 
  | 'transit' 
  | 'driving' 
  | 'rideshare' 
  | 'scooter' 
  | 'wheelchair';

// Auth types
export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterData {
  email: string;
  password: string;
  display_name: string;
}

// POI types
export interface POI {
  id: string;
  name: string;
  name_local?: string;
  description?: string;
  category: POICategory;
  subcategory?: string;
  tags: string[];
  coordinates: Coordinates;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  postal_code?: string;
  neighborhood?: string;
  contact?: ContactInfo;
  opening_hours?: OpeningHours;
  photos: string[];
  rating: number;
  review_count: number;
  popularity_score: number;
  is_verified: boolean;
  is_active: boolean;
  external_id?: string;
  source: POISource;
  created_at: string;
  updated_at: string;
}

export type POICategory = 
  | 'restaurant' 
  | 'cafe' 
  | 'bar' 
  | 'attraction' 
  | 'museum' 
  | 'park' 
  | 'shopping' 
  | 'hotel' 
  | 'transport' 
  | 'healthcare' 
  | 'emergency' 
  | 'education' 
  | 'religious' 
  | 'entertainment' 
  | 'sports' 
  | 'nature' 
  | 'historic' 
  | 'cultural' 
  | 'other';

export type POISource = 
  | 'manual' 
  | 'osm' 
  | 'google_places' 
  | 'foursquare' 
  | 'yelp' 
  | 'tripadvisor' 
  | 'wikidata' 
  | 'user_contributed';

export interface Coordinates {
  latitude: number;
  longitude: number;
}

export interface ContactInfo {
  phone?: string;
  email?: string;
  website?: string;
  social_media?: Record<string, string>;
}

export interface OpeningHours {
  monday?: TimeRange;
  tuesday?: TimeRange;
  wednesday?: TimeRange;
  thursday?: TimeRange;
  friday?: TimeRange;
  saturday?: TimeRange;
  sunday?: TimeRange;
  timezone: string;
}

export interface TimeRange {
  start: string; // HH:MM format
  end: string;   // HH:MM format
  is_closed: boolean;
}

// Itinerary types
export interface Itinerary {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  status: ItineraryStatus;
  start_date: string;
  end_date: string;
  budget_level: 'budget' | 'mid_range' | 'luxury';
  pace: 'relaxed' | 'moderate' | 'packed';
  interests: string[];
  accessibility_needs: string[];
  dietary_restrictions: string[];
  transport_preferences: TransportMode[];
  base_location?: Coordinates;
  base_address?: string;
  city?: string;
  country?: string;
  tags: string[];
  is_public: boolean;
  share_token?: string;
  collaborators: string[];
  total_estimated_cost?: number;
  currency: string;
  days: ItineraryDay[];
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export type ItineraryStatus = 
  | 'draft' 
  | 'active' 
  | 'completed' 
  | 'cancelled' 
  | 'archived';

export interface ItineraryDay {
  id: string;
  itinerary_id: string;
  day_number: number;
  date: string;
  title?: string;
  notes?: string;
  start_time?: string;
  end_time?: string;
  base_location?: Coordinates;
  base_address?: string;
  items: ItineraryItem[];
  created_at: string;
  updated_at: string;
}

export interface ItineraryItem {
  id: string;
  day_id: string;
  type: ItineraryItemType;
  poi_id?: string;
  title: string;
  description?: string;
  coordinates?: Coordinates;
  address?: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  transport_mode?: TransportMode;
  transit_details?: TransitDetails;
  from_location?: Coordinates;
  to_location?: Coordinates;
  estimated_cost?: number;
  currency: string;
  notes?: string;
  is_flexible: boolean;
  is_required: boolean;
  order_index: number;
  created_at: string;
  updated_at: string;
}

export type ItineraryItemType = 
  | 'poi_visit' 
  | 'transit' 
  | 'meal' 
  | 'activity' 
  | 'rest' 
  | 'custom' 
  | 'accommodation';

export interface TransitDetails {
  route_id?: string;
  route_name?: string;
  duration_minutes?: number;
  agency_name?: string;
  departure_stop?: string;
  arrival_stop?: string;
  departure_time?: string;
  arrival_time?: string;
  transfers: number;
  fare?: number;
  currency?: string;
}

// Chat types
export interface Conversation {
  id: string;
  user_id: string;
  title?: string;
  language: string;
  location?: Coordinates;
  context?: Record<string, any>;
  status: ConversationStatus;
  message_count: number;
  last_message_at?: string;
  created_at: string;
  updated_at: string;
}

export type ConversationStatus = 'active' | 'archived' | 'closed';

export interface Message {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  type: MessageType;
  tokens?: number;
  model?: string;
  processing_time_ms?: number;
  attachments?: MessageAttachment[];
  tool_calls?: ToolCall[];
  tool_call_id?: string;
  context?: Record<string, any>;
  location?: Coordinates;
  created_at: string;
}

export type MessageRole = 'user' | 'assistant' | 'system' | 'tool';
export type MessageType = 'text' | 'image' | 'audio' | 'location' | 'poi' | 'itinerary' | 'transit' | 'tool_call' | 'tool_result';

export interface MessageAttachment {
  id: string;
  type: 'image' | 'file' | 'audio';
  url: string;
  name: string;
  size: number;
  mime_type: string;
}

export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, any>;
}

// Transit types
export interface TransitRoute {
  id: string;
  origin: Coordinates;
  destination: Coordinates;
  origin_name?: string;
  destination_name?: string;
  departure_time?: string;
  arrival_time?: string;
  transport_modes: TransportMode[];
  duration_minutes: number;
  distance_meters: number;
  fare?: number;
  currency: string;
  steps: TransitStep[];
  polyline?: string;
  created_at: string;
}

export interface TransitStep {
  id: string;
  type: 'walk' | 'transit' | 'wait';
  transport_mode?: TransportMode;
  route_id?: string;
  route_name?: string;
  agency_name?: string;
  departure_stop?: string;
  arrival_stop?: string;
  departure_time?: string;
  arrival_time?: string;
  duration_minutes: number;
  distance_meters: number;
  instructions: string;
  transfers?: number;
  polyline?: string;
  fare?: number;
  currency?: string;
}

// Weather types
export interface WeatherForecast {
  location: Coordinates;
  current: CurrentWeather;
  hourly: HourlyWeather[];
  daily: DailyWeather[];
  alerts: WeatherAlert[];
  timezone: string;
  fetched_at: string;
}

export interface CurrentWeather {
  temperature: number;
  feels_like: number;
  humidity: number;
  pressure: number;
  wind_speed: number;
  wind_direction: number;
  visibility: number;
  uv_index: number;
  condition: string;
  description: string;
  icon: string;
  timestamp: string;
}

export interface HourlyWeather {
  timestamp: string;
  temperature: number;
  feels_like: number;
  humidity: number;
  pressure: number;
  wind_speed: number;
  wind_direction: number;
  visibility: number;
  precipitation_probability: number;
  precipitation_amount: number;
  condition: string;
  description: string;
  icon: string;
}

export interface DailyWeather {
  date: string;
  sunrise: string;
  sunset: string;
  temp_min: number;
  temp_max: number;
  feels_like_min: number;
  feels_like_max: number;
  humidity: number;
  pressure: number;
  wind_speed: number;
  wind_direction: number;
  precipitation_probability: number;
  precipitation_amount: number;
  condition: string;
  description: string;
  icon: string;
}

export interface WeatherAlert {
  id: string;
  type: string;
  severity: 'minor' | 'moderate' | 'severe' | 'extreme';
  title: string;
  description: string;
  start_time: string;
  end_time: string;
  areas: string[];
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ApiError {
  error: string;
  message: string;
  code: string;
  details?: Record<string, any>;
}

// WebSocket types
export interface WSMessage<T = any> {
  type: string;
  payload: T;
  timestamp: string;
  message_id?: string;
  correlation_id?: string;
}

export interface WSChatMessage {
  conversation_id: string;
  content: string;
  message_type: string;
  attachments?: MessageAttachment[];
  location?: Coordinates;
  reply_to?: string;
}

export interface WSLocationUpdate {
  user_id: string;
  latitude: number;
  longitude: number;
  accuracy?: number;
  heading?: number;
  speed?: number;
  altitude?: number;
  timestamp: string;
}

export interface WSTransitUpdate {
  route_id: string;
  vehicle_id?: string;
  trip_id?: string;
  latitude: number;
  longitude: number;
  bearing?: number;
  speed?: number;
  occupancy?: string;
  timestamp: string;
}

export interface WSItineraryUpdate {
  itinerary_id: string;
  action: string;
  user_id: string;
  data: Record<string, any>;
  timestamp: string;
}

export interface WSNotification {
  notification_id: string;
  type: string;
  title: string;
  body: string;
  data: Record<string, any>;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  timestamp: string;
}