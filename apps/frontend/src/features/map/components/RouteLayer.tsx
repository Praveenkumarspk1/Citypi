interface RouteLayerProps {
  coordinates: [number, number][];
  color?: string;
  width?: number;
}

export function RouteLayer({ coordinates, color = '#3b82f6', width = 4 }: RouteLayerProps) {
  // This is a placeholder for the actual MapLibre GL JS route layer
  // In production, this would render a GeoJSON line on the map
  return (
    <div className="hidden" data-testid="route-layer" data-coordinates={JSON.stringify(coordinates)} data-color={color} />
  );
}
