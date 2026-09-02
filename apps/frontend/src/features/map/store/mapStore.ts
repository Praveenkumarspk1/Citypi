import { create } from 'zustand';
import type { Coordinates, POI } from '../types/map';

interface MapState {
  center: Coordinates;
  zoom: number;
  selectedPOI: POI | null;
  searchRadius: number;
  setCenter: (center: Coordinates) => void;
  setZoom: (zoom: number) => void;
  setSelectedPOI: (poi: POI | null) => void;
  setSearchRadius: (radius: number) => void;
}

export const useMapStore = create<MapState>((set) => ({
  center: { lat: 37.7749, lng: -122.4194 },
  zoom: 14,
  selectedPOI: null,
  searchRadius: 1000,
  setCenter: (center) => set({ center }),
  setZoom: (zoom) => set({ zoom }),
  setSelectedPOI: (poi) => set({ selectedPOI: poi }),
  setSearchRadius: (radius) => set({ searchRadius: radius }),
}));
