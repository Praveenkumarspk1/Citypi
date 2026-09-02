import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { mapApi } from '../api/mapApi';
import type { POI, Coordinates } from '../types/map';

export function useMap(center: Coordinates, zoom: number = 14) {
  return {
    center,
    zoom,
  };
}

export function usePOISearch(coordinates: Coordinates | null, radius: number = 1000) {
  return useQuery({
    queryKey: ['pois', 'nearby', coordinates, radius],
    queryFn: () => mapApi.getNearbyPOIs(coordinates!, radius),
    enabled: !!coordinates,
  });
}

export function useGeolocation() {
  const getCurrentPosition = (): Promise<Coordinates> => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation not supported'));
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          });
        },
        (error) => reject(error),
      );
    });
  };

  return { getCurrentPosition };
}
