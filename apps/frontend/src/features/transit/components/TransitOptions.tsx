import type { TransitRoute } from '../types/transit';

interface TransitOptionsProps {
  routes: TransitRoute[];
  selectedRouteId?: string;
  onSelectRoute: (routeId: string) => void;
}

export function TransitOptions({ routes, selectedRouteId, onSelectRoute }: TransitOptionsProps) {
  return (
    <div className="space-y-2">
      {routes.map((route) => (
        <div
          key={route.route_id}
          onClick={() => onSelectRoute(route.route_id)}
          className={`p-3 rounded-lg border cursor-pointer transition-colors ${
            selectedRouteId === route.route_id
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-200 hover:border-gray-300'
          }`}
        >
          <div className="flex justify-between items-center">
            <span className="font-medium">{route.duration_minutes} min</span>
            <span className="text-sm text-gray-500">{route.transfers} transfers</span>
          </div>
        </div>
      ))}
    </div>
  );
}
