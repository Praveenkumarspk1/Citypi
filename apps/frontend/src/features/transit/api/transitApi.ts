import { apiClient } from '@shared/utils/api';
import type { TransitRoute, PlanRouteParams, TransitStop } from '../types/transit';

export const transitApi = {
  planRoute: async (params: PlanRouteParams): Promise<TransitRoute[]> => {
    const { data } = await apiClient.post('/transit/routes', params);
    return data.routes;
  },

  getNearbyStops: async (coordinates: { lat: number; lng: number }): Promise<TransitStop[]> => {
    const { data } = await apiClient.get('/transit/stops/nearby', {
      params: { lat: coordinates.lat, lng: coordinates.lng },
    });
    return data.items;
  },

  getDepartures: async (stopId: string): Promise<unknown[]> => {
    const { data } = await apiClient.get(`/transit/stops/${stopId}/departures`);
    return data.items;
  },
};
