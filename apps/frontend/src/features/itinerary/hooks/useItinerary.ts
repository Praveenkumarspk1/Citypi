import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { itineraryApi } from '../api/itineraryApi';
import type { Itinerary, CreateItineraryParams } from '../types/itinerary';

export function useItinerary(itineraryId: string | undefined) {
  return useQuery({
    queryKey: ['itinerary', itineraryId],
    queryFn: () => itineraryApi.getItinerary(itineraryId!),
    enabled: !!itineraryId,
  });
}

export function useItineraries() {
  return useQuery({
    queryKey: ['itineraries'],
    queryFn: () => itineraryApi.listItineraries(),
  });
}

export function useCreateItinerary() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: CreateItineraryParams) => itineraryApi.createItinerary(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['itineraries'] });
    },
  });
}
