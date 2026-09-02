import type { TransitRoute } from '../types/transit';

interface RouteDetailsProps {
  route: TransitRoute;
  onClose?: () => void;
}

export function RouteDetailsProps({ route, onClose }: RouteDetailsProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex justify-between items-center mb-3">
        <h4 className="font-medium">Route Details</h4>
        {onClose && (
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">×</button>
        )}
      </div>
      <div className="space-y-2">
        {route.steps.map((step, i) => (
          <div key={i} className="flex items-center gap-3 py-1">
            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
              step.type === 'walk' ? 'bg-gray-200' : 'bg-primary-100 text-primary-700'
            }`}>
              {step.type === 'walk' ? 'W' : 'T'}
            </span>
            <span className="text-sm flex-1">{step.instruction || `${step.type} - ${step.duration} min`}</span>
            <span className="text-xs text-gray-500">{step.duration}m</span>
          </div>
        ))}
      </div>
    </div>
  );
}
