// MapView Component
// Interactive map using MapLibre GL with POI markers and route layers

import { useEffect, useRef, useState, useCallback } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Target, Layers, Search } from 'lucide-react';
import { useNearbyPOIs, usePOISearch } from '@shared/hooks/useApi';
import { queryKeys } from '@shared/utils/api';
import type { POI, Coordinates } from '@shared/types';

interface MapViewProps {
  center?: Coordinates;
  zoom?: number;
  pois?: POI[];
  selectedPOI?: POI | null;
  onPOISelect?: (poi: POI) => void;
  onMapClick?: (coordinates: Coordinates) => void;
  showUserLocation?: boolean;
  showPOIs?: boolean;
  className?: string;
}

export function MapView({
  center = { latitude: 40.7128, longitude: -74.0060 }, // Default to NYC
  zoom = 12,
  pois = [],
  selectedPOI,
  onPOISelect,
  onMapClick,
  showUserLocation = true,
  showPOIs = true,
  className = '',
}: MapViewProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<Map<string, mapboxgl.Marker>>(new Map());
  const [mapLoaded, setMapLoaded] = useState(false);
  const [userLocation, setUserLocation] = useState<Coordinates | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  
  // Fetch nearby POIs when map moves
  const { data: nearbyPOIsData } = useNearbyPOIs(
    center.latitude,
    center.longitude,
    5000,
    { page: 1, page_size: 100 },
    { 
      enabled: showPOIs && mapLoaded,
      queryKey: queryKeys.pois.nearby(center.latitude, center.longitude, 5000, { page: 1, page_size: 100 }),
    }
  );
  
  const nearbyPOIs = nearbyPOIsData?.items || [];
  
  // Initialize map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;
    
    // Configure Mapbox token if needed
    // mapboxgl.accessToken = '';
    
    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: {
        version: 8,
        sources: {
          'osm': {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors',
            maxzoom: 19,
          },
        },
        layers: [
          {
            id: 'osm',
            type: 'raster',
            source: 'osm',
            minzoom: 0,
            maxzoom: 19,
          },
        ],
      },
      center: [center.longitude, center.latitude],
      zoom,
      attributionControl: false,
    });
    
    mapRef.current = map;
    
    map.on('load', () => {
      setMapLoaded(true);
      addPOILayer(map);
      addUserLocationLayer(map);
    });
    
    map.on('click', (e: mapboxgl.MapMouseEvent) => {
      if (onMapClick) {
        onMapClick({ latitude: e.lngLat.lat, longitude: e.lngLat.lng });
      }
    });
    
    map.on('moveend', () => {
      map.getCenter();
      // Update center in parent if needed
    });
    
    // Add navigation controls
    map.addControl(new mapboxgl.NavigationControl(), 'top-right');
    
    // Add geolocate control
    if (showUserLocation) {
      map.addControl(
        new mapboxgl.GeolocateControl({
          positionOptions: { enableHighAccuracy: true },
          trackUserLocation: true,
          showUserHeading: true,
        }),
        'top-right'
      );
    }
    
    return () => {
      map.remove();
      mapRef.current = null;
      markersRef.current.clear();
    };
  }, []);
  
  // Add POI layer with markers
  const addPOILayer = useCallback((map: mapboxgl.Map) => {
    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current.clear();
    
    // Combine passed POIs and nearby POIs
    const allPOIs = [...pois, ...nearbyPOIs];
    
    allPOIs.forEach(poi => {
      if (!poi.coordinates) return;
      
      const el = document.createElement('div');
      el.className = 'poi-marker';
      el.innerHTML = `
        <div class="marker-pin ${selectedPOI?.id === poi.id ? 'selected' : ''}" 
             data-poi-id="${poi.id}"
             style="--marker-color: ${getCategoryColor(poi.category)}">
          <span class="marker-icon">${getCategoryIcon(poi.category)}</span>
        </div>
      `;
      
      const marker = new mapboxgl.Marker(el, { anchor: 'bottom' })
        .setLngLat([poi.coordinates.longitude, poi.coordinates.latitude])
        .addTo(map);
      
      el.addEventListener('click', () => {
        onPOISelect?.(poi);
      });
      
      markersRef.current.set(poi.id, marker);
    });
  }, [pois, nearbyPOIs, selectedPOI, onPOISelect]);
  
  // Add user location layer
  const addUserLocationLayer = useCallback((map: mapboxgl.Map) => {
    if (!userLocation) return;
    
    // Add user location source and layer if not exists
    if (!map.getSource('user-location')) {
      map.addSource('user-location', {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: {
            type: 'Point',
            coordinates: [userLocation.longitude, userLocation.latitude],
          },
        },
      });
      
      map.addLayer({
        id: 'user-location',
        type: 'circle',
        source: 'user-location',
        paint: {
          'circle-radius': 8,
          'circle-color': '#3b82f6',
          'circle-stroke-width': 3,
          'circle-stroke-color': '#ffffff',
        },
      });
      
      map.addLayer({
        id: 'user-location-pulse',
        type: 'circle',
        source: 'user-location',
        paint: {
          'circle-radius': 16,
          'circle-color': '#3b82f6',
          'circle-opacity': 0.3,
        },
      });
    } else {
      // Update existing location
      const source = map.getSource('user-location') as mapboxgl.GeoJSONSource;
      source.setData({
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [userLocation.longitude, userLocation.latitude],
        },
      });
    }
  }, [userLocation]);
  
  // Update POIs when they change
  useEffect(() => {
    if (mapRef.current && mapLoaded) {
      addPOILayer(mapRef.current);
    }
  }, [addPOILayer, mapLoaded]);
  
  // Update selected POI
  useEffect(() => {
    if (mapRef.current && mapLoaded) {
      addPOILayer(mapRef.current);
    }
  }, [selectedPOI, addPOILayer, mapLoaded]);
  
  // Get user location
  const handleLocateUser = useCallback(() => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser');
      return;
    }
    
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const coords = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        };
        setUserLocation(coords);
        mapRef.current?.flyTo({ center: [coords.longitude, coords.latitude], zoom: 15 });
      },
      (error) => {
        setLocationError('Unable to retrieve your location');
        console.error('Geolocation error:', error);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }, []);
  
  // Fit bounds to show all POIs
  const fitToPOIs = useCallback(() => {
    if (!mapRef.current || allPOIs.length === 0) return;
    
    const bounds = new mapboxgl.LngLatBounds();
    allPOIs.forEach(poi => {
      if (poi.coordinates) {
        bounds.extend([poi.coordinates.longitude, poi.coordinates.latitude]);
      }
    });
    
    mapRef.current.fitBounds(bounds, { padding: 50, maxZoom: 15 });
  }, []);
  
  const allPOIs = [...pois, ...nearbyPOIs];
  
  return (
    <div className={`relative ${className}`}>
      <div
        ref={mapContainerRef}
        className="w-full h-full"
        style={{ minHeight: '400px' }}
      />
      
      {/* Map Controls Overlay */}
      <div className="absolute top-4 left-4 z-10 flex flex-col gap-2">
        <button
          onClick={handleLocateUser}
          disabled={locationError !== null}
          className="btn-secondary p-2 rounded-lg shadow-lg"
          title="Locate me"
        >
          <Target className="w-5 h-5" />
        </button>
        
        <button
          onClick={() => fitToPOIs()}
          disabled={allPOIs.length === 0}
          className="btn-secondary p-2 rounded-lg shadow-lg"
          title="Show all POIs"
        >
          <Layers className="w-5 h-5" />
        </button>
      </div>
      
      {/* Search Box */}
      <div className="absolute top-4 left-4 right-4 max-w-md mx-auto z-10 lg:left-20 lg:max-w-xs lg:mx-0">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search places..."
            className="input pl-10 w-full"
            onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
              if (e.key === 'Enter') {
                // Handle search
                console.log('Search:', e.currentTarget.value);
              }
            }}
          />
        </div>
      </div>
      
      {/* Selected POI Info Card */}
      {selectedPOI && (
        <div className="absolute bottom-4 left-4 right-4 max-w-sm mx-auto z-10 lg:left-4 lg:max-w-xs lg:mx-0">
          <div className="card p-4 shadow-xl animate-slide-up">
            <div className="flex items-start gap-3">
              <div className="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center flex-shrink-0">
                <span className="text-2xl">{getCategoryIcon(selectedPOI.category)}</span>
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-gray-900 truncate">{selectedPOI.name}</h3>
                <p className="text-sm text-gray-500 truncate">{selectedPOI.category}</p>
                {selectedPOI.rating && (
                  <div className="flex items-center gap-1 mt-1">
                    <span className="text-yellow-500">★</span>
                    <span className="text-sm font-medium">{selectedPOI.rating.toFixed(1)}</span>
                    <span className="text-xs text-gray-400">({selectedPOI.review_count || 0})</span>
                  </div>
                )}
              </div>
            </div>
            {selectedPOI.description && (
              <p className="mt-2 text-sm text-gray-600 line-clamp-2">{selectedPOI.description}</p>
            )}
            <div className="mt-3 flex gap-2">
              <button className="btn-primary flex-1 text-sm py-2">View Details</button>
              <button className="btn-outline flex-1 text-sm py-2">Directions</button>
            </div>
          </div>
        </div>
      )}
      
      {/* Location Error Toast */}
      {locationError && (
        <div className="absolute bottom-4 left-4 right-4 max-w-sm mx-auto z-20 lg:left-4 lg:max-w-xs lg:mx-0">
          <div className="card p-3 shadow-xl border-red-200 bg-red-50 animate-slide-up">
            <div className="flex items-center gap-2 text-red-700">
              <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span className="text-sm">{locationError}</span>
              <button onClick={() => setLocationError(null)} className="ml-auto text-red-500 hover:text-red-700">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Helper functions
function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    restaurant: '#ef4444',
    cafe: '#f97316',
    museum: '#8b5cf6',
    park: '#22c55e',
    attraction: '#eab308',
    hotel: '#3b82f6',
    shopping: '#ec4899',
    transit: '#06b6d4',
    default: '#6b7280',
  };
  return colors[category.toLowerCase()] || colors.default;
}

function getCategoryIcon(category: string): string {
  const icons: Record<string, string> = {
    restaurant: '🍽️',
    cafe: '☕',
    museum: '🏛️',
    park: '🌳',
    attraction: '🎡',
    hotel: '🏨',
    shopping: '🛍️',
    transit: '🚌',
    default: '📍',
  };
  return icons[category.toLowerCase()] || icons.default;
}

// POI Search Component
export function POISearch({ onSearch, onSelect }: { 
  onSearch: (query: string) => void;
  onSelect: (poi: POI) => void;
}) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<POI[]>([]);
  
  const { data: searchData, isLoading } = usePOISearch(
    { query, page: 1, page_size: 10 },
    { 
      enabled: query.length >= 2,
      queryKey: queryKeys.pois.search({ query, page: 1, page_size: 10 }),
    }
  );
  
  useEffect(() => {
    if (searchData?.items) {
      setResults(searchData.items);
    }
  }, [searchData]);
  
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query);
    }
  };
  
  return (
    <div className="relative">
      <form onSubmit={handleSearch} className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={query}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)}
          placeholder="Search for places..."
          className="input pl-10 w-full"
        />
      </form>
      
      {query.length >= 2 && (
        <div className="absolute top-full left-0 right-0 mt-1 card shadow-lg z-10 max-h-96 overflow-y-auto">
          {isLoading || searchData === undefined ? (
            <div className="p-4 text-center text-gray-500">
              <div className="w-6 h-6 animate-spin mx-auto border-2 border-primary-600 border-t-transparent rounded-full" />
            </div>
          ) : results.length === 0 ? (
            <div className="p-4 text-center text-gray-500">No results found</div>
          ) : (
            results.map((poi) => (
              <button
                key={poi.id}
                onClick={() => {
                  onSelect(poi);
                  setQuery('');
                  setResults([]);
                }}
                className="w-full text-left p-3 hover:bg-gray-50 border-b last:border-0 flex items-center gap-3"
              >
                <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                  <span className="text-lg">{getCategoryIcon(poi.category)}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">{poi.name}</p>
                  <p className="text-sm text-gray-500 truncate">{poi.category}</p>
                </div>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
