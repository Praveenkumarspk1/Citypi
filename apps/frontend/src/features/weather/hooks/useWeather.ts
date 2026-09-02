import { useQuery } from '@tanstack/react-query';
import { weatherApi } from '../api/weatherApi';
import type { WeatherData, WeatherForecast } from '../types/weather';

export function useWeather(coordinates: { lat: number; lng: number } | null) {
  return useQuery({
    queryKey: ['weather', 'current', coordinates],
    queryFn: () => weatherApi.getCurrentWeather(coordinates!),
    enabled: !!coordinates,
  });
}

export function useWeatherForecast(coordinates: { lat: number; lng: number } | null, days: number = 7) {
  return useQuery({
    queryKey: ['weather', 'forecast', coordinates, days],
    queryFn: () => weatherApi.getForecast(coordinates!, days),
    enabled: !!coordinates,
  });
}
