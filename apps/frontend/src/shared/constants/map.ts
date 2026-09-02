export const MAP_CONFIG = {
  defaultCenter: { lat: 37.7749, lng: -122.4194 },
  defaultZoom: 14,
  minZoom: 10,
  maxZoom: 18,
  tileSize: 512,
  style: 'https://demotiles.maplibre.org/style.json',
} as const;

export const POI_COLORS: Record<string, string> = {
  restaurant: '#ef4444',
  museum: '#8b5cf6',
  park: '#22c55e',
  hotel: '#3b82f6',
  shop: '#f59e0b',
  transport: '#6366f1',
  landmark: '#ec4899',
  nature: '#10b981',
  default: '#6b7280',
} as const;

export const MAP_PROJECTION = {
  name: 'globe',
} as const;
