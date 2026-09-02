import { Sun, Cloud, CloudRain, Wind, Droplets, Thermometer, AlertTriangle, ChevronRight, MapPin, Search, RefreshCw } from 'lucide-react';
import { useState } from 'react';

export function WeatherPage() {
  const [location, setLocation] = useState('New York, NY');
  const [unit, setUnit] = useState<'celsius' | 'fahrenheit'>('fahrenheit');

  const currentWeather = {
    temperature: 72,
    feels_like: 74,
    condition: 'Partly Cloudy',
    description: 'Partly cloudy with light winds',
    humidity: 65,
    wind_speed: 8,
    wind_direction: 'NW',
    pressure: 1013,
    visibility: 10,
    uv_index: 5,
    sunrise: '06:45',
    sunset: '17:30',
    high: 76,
    low: 62,
  };

  const hourlyForecast = [
    { time: '09:00', temp: 68, condition: 'Partly Cloudy', icon: Cloud, precip: 10 },
    { time: '10:00', temp: 70, condition: 'Partly Cloudy', icon: Cloud, precip: 10 },
    { time: '11:00', temp: 72, condition: 'Sunny', icon: Sun, precip: 5 },
    { time: '12:00', temp: 74, condition: 'Sunny', icon: Sun, precip: 5 },
    { time: '13:00', temp: 75, condition: 'Sunny', icon: Sun, precip: 5 },
    { time: '14:00', temp: 76, condition: 'Sunny', icon: Sun, precip: 5 },
    { time: '15:00', temp: 76, condition: 'Partly Cloudy', icon: Cloud, precip: 10 },
    { time: '16:00', temp: 75, condition: 'Partly Cloudy', icon: Cloud, precip: 15 },
    { time: '17:00', temp: 73, condition: 'Partly Cloudy', icon: Cloud, precip: 20 },
    { time: '18:00', temp: 70, condition: 'Cloudy', icon: Cloud, precip: 25 },
    { time: '19:00', temp: 68, condition: 'Cloudy', icon: Cloud, precip: 30 },
    { time: '20:00', temp: 66, condition: 'Light Rain', icon: CloudRain, precip: 40 },
  ];

  const dailyForecast = [
    { day: 'Today', date: 'Feb 15', high: 76, low: 62, condition: 'Partly Cloudy', icon: Cloud, precip: 20 },
    { day: 'Tomorrow', date: 'Feb 16', high: 72, low: 58, condition: 'Sunny', icon: Sun, precip: 5 },
    { day: 'Sat', date: 'Feb 17', high: 68, low: 55, condition: 'Light Rain', icon: CloudRain, precip: 60 },
    { day: 'Sun', date: 'Feb 18', high: 65, low: 52, condition: 'Rain', icon: CloudRain, precip: 80 },
    { day: 'Mon', date: 'Feb 19', high: 62, low: 48, condition: 'Cloudy', icon: Cloud, precip: 30 },
    { day: 'Tue', date: 'Feb 20', high: 64, low: 50, condition: 'Partly Cloudy', icon: Cloud, precip: 15 },
    { day: 'Wed', date: 'Feb 21', high: 68, low: 52, condition: 'Sunny', icon: Sun, precip: 5 },
  ];

  const alerts = [
    { type: 'Weather Advisory', severity: 'moderate', title: 'Dense Fog Advisory', description: 'Visibility reduced to 1/4 mile in some areas until 10 AM', areas: ['Manhattan', 'Brooklyn', 'Queens'], expires: '2024-02-15T10:00:00Z' },
  ];

  const formatTemp = (temp: number) => `${unit === 'celsius' ? Math.round((temp - 32) * 5/9) : temp}°${unit === 'celsius' ? 'C' : 'F'}`;

  return (
    <div className="space-y-6">
      {/* Location Search */}
      <div className="card">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Weather</h2>
          <div className="flex items-center gap-2">
            <button className="btn-ghost btn-sm">
              <RefreshCw className="w-4 h-4 mr-1" />
              Refresh
            </button>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={unit === 'celsius'}
                onChange={(e) => setUnit(e.target.checked ? 'celsius' : 'fahrenheit')}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              °C
            </label>
          </div>
        </div>
        <div className="p-4">
          <div className="relative max-w-md">
            <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search location..."
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="input pl-10 pr-10"
            />
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          </div>
        </div>
      </div>

      {/* Current Weather */}
      <div className="card">
        <div className="p-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div className="flex items-center gap-6">
              <div className="w-32 h-32 rounded-2xl bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center">
                <Sun className="w-16 h-16 text-white" />
              </div>
              <div>
                <h1 className="text-5xl font-bold text-gray-900">{formatTemp(currentWeather.temperature)}</h1>
                <p className="text-xl text-gray-500 capitalize">{currentWeather.condition}</p>
                <p className="text-gray-400 mt-1">{currentWeather.description}</p>
                <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                  <span className="flex items-center gap-1">
                    <Thermometer className="w-4 h-4" />
                    Feels like {formatTemp(currentWeather.feels_like)}
                  </span>
                  <span className="flex items-center gap-1">
                    <Droplets className="w-4 h-4" />
                    {currentWeather.humidity}%
                  </span>
                  <span className="flex items-center gap-1">
                    <Wind className="w-4 h-4" />
                    {currentWeather.wind_speed} mph {currentWeather.wind_direction}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-center lg:ml-8">
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-2xl font-bold text-gray-900">{formatTemp(currentWeather.high || 76)}</p>
                <p className="text-sm text-gray-500">High</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-2xl font-bold text-gray-900">{formatTemp(currentWeather.low || 62)}</p>
                <p className="text-sm text-gray-500">Low</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-2xl font-bold text-gray-900">{currentWeather.uv_index}</p>
                <p className="text-sm text-gray-500">UV Index</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-2xl font-bold text-gray-900">{currentWeather.visibility} mi</p>
                <p className="text-sm text-gray-500">Visibility</p>
              </div>
            </div>
          </div>

          {/* Sunrise/Sunset */}
          <div className="mt-6 pt-6 border-t border-gray-200 flex items-center justify-center gap-8">
            <div className="flex items-center gap-3 text-center">
              <div className="w-12 h-12 rounded-full bg-yellow-100 flex items-center justify-center mx-auto">
                <Sun className="w-6 h-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Sunrise</p>
                <p className="font-medium text-gray-900">{currentWeather.sunrise}</p>
              </div>
            </div>
            <div className="w-px h-8 bg-gray-200" />
            <div className="flex items-center gap-3 text-center">
              <div className="w-12 h-12 rounded-full bg-orange-100 flex items-center justify-center mx-auto">
                <Sun className="w-6 h-6 text-orange-600" style={{ transform: 'rotate(180deg)' }} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Sunset</p>
                <p className="font-medium text-gray-900">{currentWeather.sunset}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="card border-yellow-200">
          <div className="p-4 bg-yellow-50 border-b border-yellow-200">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              <div>
                <p className="font-medium text-yellow-800">Weather Alert</p>
                <p className="text-sm text-yellow-700">{alerts.length} active alert{alerts.length > 1 ? 's' : ''}</p>
              </div>
            </div>
          </div>
          <div className="p-4 space-y-3">
            {alerts.map((alert) => (
              <div key={alert.type} className="p-3 bg-white border border-yellow-200 rounded-lg">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="badge badge-warning">{alert.severity}</span>
                      <span className="font-medium text-gray-900">{alert.title}</span>
                    </div>
                    <p className="text-sm text-gray-600">{alert.description}</p>
                    <p className="text-xs text-gray-500 mt-1">Areas: {alert.areas.join(', ')}</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400 mt-1" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Hourly Forecast */}
      <div className="card">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Hourly Forecast</h2>
        </div>
        <div className="p-4">
          <div className="overflow-x-auto pb-4">
            <div className="flex gap-4 min-w-max">
              {hourlyForecast.map((hour) => (
                <div key={hour.time} className="flex-shrink-0 w-20 text-center">
                  <p className="text-sm font-medium text-gray-900">{hour.time}</p>
                  <div className="w-12 h-12 mx-auto my-2">
                    <hour.icon className="w-12 h-12 text-primary-600" />
                  </div>
                  <p className="text-lg font-semibold text-gray-900">{formatTemp(hour.temp)}</p>
                  <p className="text-xs text-gray-500 capitalize">{hour.condition}</p>
                  <div className="flex items-center justify-center gap-1 text-xs text-blue-600 mt-1">
                    <Droplets className="w-3 h-3" />
                    <span>{hour.precip}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Daily Forecast */}
      <div className="card">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">7-Day Forecast</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {dailyForecast.map((day) => (
            <div key={day.date} className="p-4 flex items-center justify-between hover:bg-gray-50">
              <div className="flex items-center gap-4 min-w-[200px]">
                <div className="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center">
                  <day.icon className="w-6 h-6 text-primary-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{day.day}</p>
                  <p className="text-sm text-gray-500">{day.date}</p>
                </div>
              </div>
              <div className="flex items-center gap-6 text-center">
                <div className="w-24">
                  <p className="text-sm text-gray-500">High</p>
                  <p className="font-semibold text-gray-900">{formatTemp(day.high)}</p>
                </div>
                <div className="w-24">
                  <p className="text-sm text-gray-500">Low</p>
                  <p className="font-semibold text-gray-900">{formatTemp(day.low)}</p>
                </div>
                <div className="w-32">
                  <p className="text-sm text-gray-500">Precip</p>
                  <p className="font-medium text-blue-600">{day.precip}%</p>
                </div>
                <div className="w-32">
                  <p className="text-sm text-gray-500">Condition</p>
                  <p className="text-sm text-gray-900 capitalize">{day.condition}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { title: 'Humidity', value: `${currentWeather.humidity}%`, icon: Droplets, color: 'blue' },
          { title: 'Wind', value: `${currentWeather.wind_speed} mph ${currentWeather.wind_direction}`, icon: Wind, color: 'green' },
          { title: 'Pressure', value: `${currentWeather.pressure} hPa`, icon: Thermometer, color: 'purple' },
          { title: 'UV Index', value: `${currentWeather.uv_index} (Moderate)`, icon: Sun, color: 'orange' },
        ].map((detail, i) => (
          <div key={i} className="card p-4">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg bg-${detail.color}-100 flex items-center justify-center`}>
                <detail.icon className={`w-5 h-5 text-${detail.color}-600`} />
              </div>
              <div>
                <p className="text-sm text-gray-500">{detail.title}</p>
                <p className="font-semibold text-gray-900">{detail.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}