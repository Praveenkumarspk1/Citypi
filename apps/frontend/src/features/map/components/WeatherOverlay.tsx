interface WeatherOverlayProps {
  temperature?: number;
  condition?: string;
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
}

export function WeatherOverlay({ temperature, condition, position = 'top-right' }: WeatherOverlayProps) {
  const positionClasses = {
    'top-left': 'top-4 left-4',
    'top-right': 'top-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-right': 'bottom-4 right-4',
  };

  return (
    <div className={`absolute ${positionClasses[position]} bg-white/90 backdrop-blur-sm rounded-lg px-3 py-2 shadow-md`}>
      {temperature !== undefined && <span className="text-lg font-bold">{Math.round(temperature)}°C</span>}
      {condition && <span className="text-sm text-gray-600 ml-2">{condition}</span>}
    </div>
  );
}
