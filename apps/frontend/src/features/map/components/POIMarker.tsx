import type { POI } from '../types/map';

interface POIMarkerProps {
  poi: POI;
  isSelected?: boolean;
  onClick?: (poi: POI) => void;
}

export function POIMarker({ poi, isSelected = false, onClick }: POIMarkerProps) {
  return (
    <div
      className={`cursor-pointer transition-transform hover:scale-110 ${isSelected ? 'scale-125 z-10' : ''}`}
      onClick={() => onClick?.(poi)}
      title={poi.name}
    >
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-lg ${
        isSelected ? 'bg-primary-600 ring-2 ring-primary-300' : 'bg-primary-500'
      }`}>
        {poi.category[0]?.toUpperCase()}
      </div>
    </div>
  );
}
