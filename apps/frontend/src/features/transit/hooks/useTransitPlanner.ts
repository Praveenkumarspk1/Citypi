import { useMutation, useQuery } from '@tanstack/react-query';
import { transitApi } from '../api/transitApi';
import type { TransitRoute, PlanRouteParams } from '../types/transit';

export function useTransitPlanner() {
  const planRouteMutation = useMutation({
    mutationFn: (params: PlanRouteParams) => transitApi.planRoute(params),
  });

  return {
    planRoute: planRouteMutation.mutateAsync,
    routes: planRouteMutation.data ?? [],
    isPlanning: planRouteMutation.isPending,
  };
}

export function useNearbyStops(coordinates: { lat: number; lng: number } | null) {
  return useQuery({
    queryKey: ['transit', 'stops', 'nearby', coordinates],
    queryFn: () => transitApi.getNearbyStops(coordinates!),
    enabled: !!coordinates,
  });
}

export function useRealtimeDepartures(stopId: string | null) {
  return useQuery({
    queryKey: ['transit', 'departures', stopId],
    queryFn: () => transitApi.getDepartures(stopId!),
    enabled: !!stopId,
    refetchInterval: 30000,
  });
}
