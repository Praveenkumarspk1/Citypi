import type { POI } from '../../map/types/map';

interface POICardProps {
  poi: POI;
  onView?: () => void;
  onAddToItinerary?: () => void;
}

export function POICard({ poi, onView, onAddToItinerary }: POICardProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
      <div className="p-3">
        <div className="flex justify-between items-start">
          <h4 className="font-medium text-sm">{poi.name}</h4>
          {poi.rating && (
            <span className="text-xs text-yellow-600">★ {poi.rating}</span>
          )}
        </div>
        <p className="text-xs text-gray-500 mt-1 line-clamp-2">{poi.description}</p>
        <div className="flex gap-2 mt-2">
          <span className="text-xs px-2 py-0.5 bg-gray-100 rounded">{poi.category}</span>
        </div>
        <div className="flex gap-2 mt-3">
          {onView && (
            <button onClick={onView} className="text-xs text-primary-600 hover:text-primary-700">View</button>
          )}
          {onAddToItinerary && (
            <button onClick={onAddToItinerary} className="text-xs text-primary-600 hover:text-primary-700">+ Add</button>
          )}
        </div>
      </div>
    </div>
  );
}
