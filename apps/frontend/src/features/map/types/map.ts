export interface Coordinates {
  lat: number;
  lng: number;
}

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

export interface MapViewProps {
  center: Coordinates;
  zoom?: number;
  pois?: POI[];
  routes?: TransitRoute[];
  userLocation?: Coordinates;
  onPoiClick?: (poi: POI) => void;
}

export interface TransitRoute {
  route_id: string;
  duration_minutes: number;
  transfers: number;
  steps: unknown[];
  fare?: number;
}
