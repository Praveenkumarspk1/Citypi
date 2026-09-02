interface TransitLayerProps {
  stops?: unknown[];
  routes?: unknown[];
  visible?: boolean;
}

export function TransitLayer({ stops = [], routes = [], visible = true }: TransitLayerProps) {
  if (!visible) return null;
  return (
    <div className="hidden" data-testid="transit-layer" data-stops={stops.length} data-routes={routes.length} />
  );
}
