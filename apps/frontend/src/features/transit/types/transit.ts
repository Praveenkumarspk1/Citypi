export interface Coordinates {
  lat: number;
  lng: number;
}

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

export interface TransitStop {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  distance?: number;
}

export interface PlanRouteParams {
  origin_lat: number;
  origin_lng: number;
  destination_lat: number;
  destination_lng: number;
  departure_time?: string;
  preferences?: Record<string, unknown>;
}
