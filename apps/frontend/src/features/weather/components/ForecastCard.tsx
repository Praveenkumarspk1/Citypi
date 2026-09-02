import type { WeatherForecast } from '../types/weather';

interface ForecastCardProps {
  forecast: WeatherForecast;
}

export function ForecastCard({ forecast }: ForecastCardProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h4 className="font-medium text-sm mb-3">7-Day Forecast</h4>
      <div className="grid grid-cols-7 gap-2">
        {forecast.forecast.map((day) => (
          <div key={day.date} className="text-center p-2 rounded-lg hover:bg-gray-50">
            <p className="text-xs text-gray-500">{new Date(day.date).toLocaleDateString('en', { weekday: 'short' })}</p>
            <p className="text-sm font-medium mt-1">{Math.round(day.temperature_max)}°</p>
            <p className="text-xs text-gray-400">{Math.round(day.temperature_min)}°</p>
            {day.precipitation_probability > 0 && (
              <p className="text-xs text-blue-500 mt-1">{day.precipitation_probability}%</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
