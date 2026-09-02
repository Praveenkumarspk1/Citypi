// WeatherDisplay Component
// Weather forecast display with current conditions and hourly/daily forecasts

import { useState, useEffect } from 'react';
import { 
  Sun, 
  Cloud, 
  CloudRain, 
  CloudSnow, 
  CloudLightning, 
  Wind, 
  Droplets, 
  Thermometer, 
  Eye, 
  Sunrise, 
  Sunset,
  Clock,
  Calendar,
  AlertTriangle,
  MapPin,
  RefreshCw,
} from 'lucide-react';
import { useWeatherForecast, useWeatherAlerts } from '@shared/hooks/useApi';
import type { WeatherForecast, HourlyWeather, DailyWeather, WeatherAlert, Coordinates } from '@shared/types';

interface WeatherDisplayProps {
  location?: Coordinates;
  locationName?: string;
  className?: string;
  compact?: boolean;
}

export function WeatherDisplay({
  location,
  locationName = 'Current Location',
  className = '',
  compact = false,
}: WeatherDisplayProps) {
  const [forecast, setForecast] = useState<WeatherForecast | null>(null);
  const [alerts, setAlerts] = useState<WeatherAlert[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'current' | 'hourly' | 'daily'>('current');
  
  const { data: forecastData, isLoading: forecastLoading, refetch } = useWeatherForecast(
    location?.latitude || 0,
    location?.longitude || 0,
    7,
    { enabled: !!location }
  );
  
  const { data: alertsData } = useWeatherAlerts(
    location?.latitude || 0,
    location?.longitude || 0,
    { enabled: !!location }
  );
  
  useEffect(() => {
    if (forecastData) {
      setForecast(forecastData);
    }
  }, [forecastData]);
  
  useEffect(() => {
    if (alertsData) {
      setAlerts(alertsData);
    }
  }, [alertsData]);
  
  const handleRefresh = async () => {
    setIsLoading(true);
    try {
      await refetch();
    } catch (err) {
      setError('Failed to refresh weather data');
    } finally {
      setIsLoading(false);
    }
  };
  
  if (!location) {
    return (
      <div className={`card p-8 text-center ${className}`}>
        <MapPin className="w-12 h-12 mx-auto text-gray-300 mb-4" />
        <p className="text-gray-500">Select a location to view weather</p>
      </div>
    );
  }
  
  if (isLoading || forecastLoading) {
    return (
      <div className={`card p-8 text-center ${className}`}>
        <div className="w-8 h-8 animate-spin mx-auto border-2 border-primary-600 border-t-transparent rounded-full mb-4" />
        <p className="text-gray-500">Loading weather...</p>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className={`card p-4 border-red-200 bg-red-50 ${className}`}>
        <div className="flex items-center gap-2 text-red-700">
          <AlertTriangle className="w-5 h-5" />
          <span>{error}</span>
          <button onClick={handleRefresh} className="ml-auto text-red-500 hover:text-red-700">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }
  
  if (!forecast) {
    return (
      <div className={`card p-8 text-center ${className}`}>
        <p className="text-gray-500">No weather data available</p>
      </div>
    );
  }
  
  const current = forecast.current;
  const hourly = forecast.hourly.slice(0, 24);
  const daily = forecast.daily.slice(0, 7);
  
  const getConditionIcon = (condition: string) => {
    const conditionLower = condition.toLowerCase();
    if (conditionLower.includes('clear') || conditionLower.includes('sunny')) return <Sun className="w-6 h-6" />;
    if (conditionLower.includes('cloud')) return <Cloud className="w-6 h-6" />;
    if (conditionLower.includes('rain') || conditionLower.includes('drizzle')) return <CloudRain className="w-6 h-6" />;
    if (conditionLower.includes('snow')) return <CloudSnow className="w-6 h-6" />;
    if (conditionLower.includes('thunder') || conditionLower.includes('storm')) return <CloudLightning className="w-6 h-6" />;
    return <Cloud className="w-6 h-6" />;
  };
  
  const getConditionColor = (condition: string) => {
    const conditionLower = condition.toLowerCase();
    if (conditionLower.includes('clear') || conditionLower.includes('sunny')) return 'text-yellow-500';
    if (conditionLower.includes('cloud')) return 'text-gray-500';
    if (conditionLower.includes('rain') || conditionLower.includes('drizzle')) return 'text-blue-500';
    if (conditionLower.includes('snow')) return 'text-blue-300';
    if (conditionLower.includes('thunder') || conditionLower.includes('storm')) return 'text-purple-500';
    return 'text-gray-500';
  };
  
  const formatTemp = (temp: number) => `${Math.round(temp)}°`;
  const formatTime = (timestamp: string) => new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const formatDay = (date: string) => new Date(date).toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
  
  if (compact) {
    return (
      <div className={`card ${className}`}>
        <div className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-16 h-16 rounded-xl bg-primary-100 flex items-center justify-center ${getConditionColor(current.condition)}`}>
                {getConditionIcon(current.condition)}
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">{locationName}</h3>
                <p className="text-sm text-gray-500">{current.description}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold text-gray-900">{formatTemp(current.temperature)}</p>
              <p className="text-sm text-gray-500">Feels like {formatTemp(current.feels_like)}</p>
            </div>
          </div>
          
          <div className="mt-4 grid grid-cols-4 gap-4 text-center">
            <WeatherMetric icon={<Thermometer className="w-5 h-5 mx-auto" />} label="Humidity" value={`${current.humidity}%`} />
            <WeatherMetric icon={<Wind className="w-5 h-5 mx-auto" />} label="Wind" value={`${Math.round(current.wind_speed)} m/s`} />
            <WeatherMetric icon={<Eye className="w-5 h-5 mx-auto" />} label="Visibility" value={`${Math.round(current.visibility / 1000)} km`} />
            <WeatherMetric icon={<Droplets className="w-5 h-5 mx-auto" />} label="UV Index" value={current.uv_index.toString()} />
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className={`card ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-16 h-16 rounded-xl bg-primary-100 flex items-center justify-center ${getConditionColor(current.condition)}`}>
              {getConditionIcon(current.condition)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-semibold text-gray-900">{locationName}</h2>
                {alerts.length > 0 && (
                  <span className="px-2 py-0.5 text-xs bg-red-100 text-red-700 rounded">
                    {alerts.length} Alert{alerts.length > 1 ? 's' : ''}
                  </span>
                )}
              </div>
              <p className="text-gray-500 capitalize">{current.description}</p>
            </div>
          </div>
          
          <div className="text-right">
            <p className="text-4xl font-bold text-gray-900">{formatTemp(current.temperature)}</p>
            <p className="text-sm text-gray-500">Feels like {formatTemp(current.feels_like)}</p>
          </div>
        </div>
        
        {/* Tab Navigation */}
        <div className="mt-4 flex gap-1 bg-gray-100 rounded-lg p-1">
          {[
            { id: 'current', label: 'Now', icon: <Sun className="w-4 h-4" /> },
            { id: 'hourly', label: 'Hourly', icon: <Clock className="w-4 h-4" /> },
            { id: 'daily', label: '7-Day', icon: <Calendar className="w-4 h-4" /> },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-white text-primary-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>
      
      {/* Current Conditions Details */}
      {activeTab === 'current' && (
        <div className="p-4 space-y-4">
          {/* Main Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <WeatherMetric 
              icon={<Thermometer className="w-5 h-5 mx-auto" />} 
              label="Temperature" 
              value={formatTemp(current.temperature)}
              subValue={`Feels like ${formatTemp(current.feels_like)}`}
            />
            <WeatherMetric 
              icon={<Droplets className="w-5 h-5 mx-auto" />} 
              label="Humidity" 
              value={`${current.humidity}%`}
            />
            <WeatherMetric 
              icon={<Wind className="w-5 h-5 mx-auto" />} 
              label="Wind" 
              value={`${Math.round(current.wind_speed)} m/s`}
              subValue={`${current.wind_direction}°`}
            />
            <WeatherMetric 
              icon={<Eye className="w-5 h-5 mx-auto" />} 
              label="Visibility" 
              value={`${Math.round(current.visibility / 1000)} km`}
            />
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <WeatherMetric 
              icon={<Sunrise className="w-5 h-5 mx-auto" />} 
              label="Sunrise" 
              value={formatTime(forecast.daily[0].sunrise)}
            />
            <WeatherMetric 
              icon={<Sunset className="w-5 h-5 mx-auto" />} 
              label="Sunset" 
              value={formatTime(forecast.daily[0].sunset)}
            />
            <WeatherMetric 
              icon={<Droplets className="w-5 h-5 mx-auto" />} 
              label="Pressure" 
              value={`${current.pressure} hPa`}
            />
            <WeatherMetric 
              icon={<AlertTriangle className="w-5 h-5 mx-auto" />} 
              label="UV Index" 
              value={current.uv_index.toString()}
              subValue={getUVDescription(current.uv_index)}
            />
          </div>
          
          {/* Alerts */}
          {alerts.length > 0 && (
            <div className="border-t border-gray-200 pt-4">
              <h3 className="font-medium text-gray-900 mb-3">Weather Alerts</h3>
              <div className="space-y-2">
                {alerts.map(alert => (
                  <div key={alert.id} className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0" />
                      <div className="flex-1">
                        <p className="font-medium text-yellow-800">{alert.title}</p>
                        <p className="text-sm text-yellow-700 mt-1">{alert.description}</p>
                        <p className="text-xs text-yellow-600 mt-1">
                          {formatTime(alert.start_time)} - {formatTime(alert.end_time)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Hourly Forecast */}
      {activeTab === 'hourly' && (
        <div className="p-4">
          <div className="overflow-x-auto pb-4">
            <div className="flex gap-4 min-w-max">
              {hourly.map((hour, index) => (
                <HourlyForecastCard 
                  key={index} 
                  hour={hour} 
                  isNow={index === 0}
                  formatTemp={formatTemp}
                  formatTime={formatTime}
                  getConditionIcon={getConditionIcon}
                  getConditionColor={getConditionColor}
                />
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* Daily Forecast */}
      {activeTab === 'daily' && (
        <div className="p-4 space-y-2">
          {daily.map((day, index) => (
            <DailyForecastCard
              key={index}
              day={day}
              isToday={index === 0}
              formatTemp={formatTemp}
              formatDay={formatDay}
              getConditionIcon={getConditionIcon}
              getConditionColor={getConditionColor}
            />
          ))}
        </div>
      )}
      
      {/* Footer */}
      <div className="p-4 border-t border-gray-200 flex items-center justify-between text-sm text-gray-500">
        <span>Updated: {formatTime(forecast.fetched_at)}</span>
        <button onClick={handleRefresh} disabled={isLoading} className="flex items-center gap-1 text-primary-600 hover:text-primary-700">
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>
    </div>
  );
}

// WeatherMetric Component
interface WeatherMetricProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  subValue?: string;
}

function WeatherMetric({ icon, label, value, subValue }: WeatherMetricProps) {
  return (
    <div className="p-3 bg-gray-50 rounded-lg text-center">
      <div className="text-gray-400 mb-1">{icon}</div>
      <p className="text-lg font-semibold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
      {subValue && <p className="text-xs text-gray-400">{subValue}</p>}
    </div>
  );
}

// HourlyForecastCard Component
interface HourlyForecastCardProps {
  hour: HourlyWeather;
  isNow: boolean;
  formatTemp: (temp: number) => string;
  formatTime: (timestamp: string) => string;
  getConditionIcon: (condition: string) => React.ReactNode;
  getConditionColor: (condition: string) => string;
}

function HourlyForecastCard({ hour, isNow, formatTemp, formatTime, getConditionIcon, getConditionColor }: HourlyForecastCardProps) {
  return (
    <div className={`flex-shrink-0 w-20 p-3 rounded-xl text-center ${isNow ? 'bg-primary-50 border border-primary-200' : 'bg-gray-50'}`}>
      <p className={`text-sm font-medium ${isNow ? 'text-primary-600' : 'text-gray-600'}`}>
        {isNow ? 'Now' : formatTime(hour.timestamp)}
      </p>
      <div className={`my-2 ${getConditionColor(hour.condition)}`}>
        {getConditionIcon(hour.condition)}
      </div>
      <p className="text-lg font-bold text-gray-900">{formatTemp(hour.temperature)}</p>
      <p className="text-xs text-gray-500">{hour.precipitation_probability}% rain</p>
      <div className="mt-2 flex items-center justify-center gap-1 text-xs text-gray-500">
        <Wind className="w-3 h-3" />
        <span>{Math.round(hour.wind_speed)} m/s</span>
      </div>
    </div>
  );
}

// DailyForecastCard Component
interface DailyForecastCardProps {
  day: DailyWeather;
  isToday: boolean;
  formatTemp: (temp: number) => string;
  formatDay: (date: string) => string;
  getConditionIcon: (condition: string) => React.ReactNode;
  getConditionColor: (condition: string) => string;
}

function DailyForecastCard({ day, isToday, formatTemp, formatDay, getConditionIcon, getConditionColor }: DailyForecastCardProps) {
  return (
    <div className={`p-3 rounded-lg ${isToday ? 'bg-primary-50 border border-primary-200' : 'hover:bg-gray-50'}`}>
      <div className="flex items-center gap-4">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${getConditionColor(day.condition)}`}>
          {getConditionIcon(day.condition)}
        </div>
        <div className="flex-1 min-w-0">
          <p className={`font-medium ${isToday ? 'text-primary-600' : 'text-gray-900'}`}>
            {isToday ? 'Today' : formatDay(day.date)}
          </p>
          <p className="text-sm text-gray-500 capitalize">{day.description}</p>
        </div>
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span className="font-medium text-gray-900">{formatTemp(day.temp_max)}</span>
          <span className="text-gray-400">{formatTemp(day.temp_min)}</span>
          <span className="flex items-center gap-1">
            <Droplets className="w-3 h-3" />
            {day.precipitation_probability}%
          </span>
          <span className="flex items-center gap-1">
            <Wind className="w-3 h-3" />
            {Math.round(day.wind_speed)} m/s
          </span>
        </div>
      </div>
    </div>
  );
}

function getUVDescription(uvIndex: number): string {
  if (uvIndex <= 2) return 'Low';
  if (uvIndex <= 5) return 'Moderate';
  if (uvIndex <= 7) return 'High';
  if (uvIndex <= 10) return 'Very High';
  return 'Extreme';
}
