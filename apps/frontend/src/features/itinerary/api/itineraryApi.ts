import { apiClient } from '@shared/utils/api';
import type { Itinerary, CreateItineraryParams } from '../types/itinerary';

export const itineraryApi = {
  listItineraries: async (): Promise<Itinerary[]> => {
    const { data } = await apiClient.get('/itineraries');
    return data.items;
  },

  getItinerary: async (itineraryId: string): Promise<Itinerary> => {
    const { data } = await apiClient.get(`/itineraries/${itineraryId}`);
    return data;
  },

  createItinerary: async (params: CreateItineraryParams): Promise<Itinerary> => {
    const { data } = await apiClient.post('/itineraries', params);
    return data;
  },

  updateItinerary: async (itineraryId: string, params: Partial<Itinerary>): Promise<Itinerary> => {
    const { data } = await apiClient.put(`/itineraries/${itineraryId}`, params);
    return data;
  },

  deleteItinerary: async (itineraryId: string): Promise<void> => {
    await apiClient.delete(`/itineraries/${itineraryId}`);
  },

  shareItinerary: async (itineraryId: string): Promise<{ share_token: string }> => {
    const { data } = await apiClient.post(`/itineraries/${itineraryId}/share`);
    return data;
  },
};
