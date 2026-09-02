export const TRANSIT_MODES = {
  WALKING: 'walking',
  CYCLING: 'cycling',
  TRANSIT: 'transit',
  DRIVING: 'driving',
} as const;

export const TRANSIT_MODE_LABELS: Record<string, string> = {
  walking: 'Walking',
  cycling: 'Cycling',
  transit: 'Public Transit',
  driving: 'Driving',
} as const;

export const ROUTE_TYPES = {
  TRAM: 0,
  SUBWAY: 1,
  RAIL: 2,
  BUS: 3,
  FERRY: 4,
  CABLE_CAR: 5,
  GONDOLA: 6,
  FUNICULAR: 7,
} as const;

export const ROUTE_TYPE_LABELS: Record<number, string> = {
  0: 'Tram',
  1: 'Subway',
  2: 'Rail',
  3: 'Bus',
  4: 'Ferry',
  5: 'Cable Car',
  6: 'Gondola',
  7: 'Funicular',
} as const;

export const ACCESSIBILITY = {
  WHEELCHAIR: 'wheelchair',
  AUDIO: 'audio',
  VISUAL: 'visual',
} as const;
