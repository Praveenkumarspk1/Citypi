import { apiClient } from '@shared/utils/api';
import type { POI } from '../types/map';

export const mapApi = {
  getNearbyPOIs: async (coordinates: { lat: number; lng: number }, radius: number): Promise<POI[]> => {
    const { data } = await apiClient.get('/pois/nearby', {
      params: { lat: coordinates.lat, lng: coordinates.lng, radius },
    });
    return data.items;
  },

  searchPOIs: async (query: string, coordinates?: { lat: number; lng: number }): Promise<POI[]> => {
    const { data } = await apiClient.get('/pois', {
      params: { query, lat: coordinates?.lat, lng: coordinates?.lng },
    });
    return data.items;
  },

  getPOIDetails: async (poiId: string): Promise<POI> => {
    const { data } = await apiClient.get(`/pois/${poiId}`);
    return data;
  },
};
