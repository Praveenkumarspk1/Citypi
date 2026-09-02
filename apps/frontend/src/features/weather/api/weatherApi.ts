import { apiClient } from '@shared/utils/api';
import type { WeatherData, WeatherForecast } from '../types/weather';

export const weatherApi = {
  getCurrentWeather: async (coordinates: { lat: number; lng: number }): Promise<WeatherData> => {
    const { data } = await apiClient.get('/weather/current', {
      params: { lat: coordinates.lat, lng: coordinates.lng },
    });
    return data;
  },

  getForecast: async (coordinates: { lat: number; lng: number }, days: number): Promise<WeatherForecast> => {
    const { data } = await apiClient.get('/weather/forecast', {
      params: { lat: coordinates.lat, lng: coordinates.lng, days },
    });
    return data;
  },

  getAlerts: async (coordinates: { lat: number; lng: number }): Promise<unknown[]> => {
    const { data } = await apiClient.get('/weather/alerts', {
      params: { lat: coordinates.lat, lng: coordinates.lng },
    });
    return data.items;
  },
};
