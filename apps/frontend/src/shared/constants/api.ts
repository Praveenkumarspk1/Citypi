export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
export const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8001/ws';

export const API_ENDPOINTS = {
  // Auth
  login: '/users/login',
  register: '/users/register',
  logout: '/users/logout',
  refresh: '/users/refresh',

  // Conversations
  conversations: '/conversations',
  messages: (id: string) => `/conversations/${id}/messages`,
  streamMessage: (id: string) => `/conversations/${id}/messages/stream`,

  // Itineraries
  itineraries: '/itineraries',
  itinerary: (id: string) => `/itineraries/${id}`,
  shareItinerary: (id: string) => `/itineraries/${id}/share`,

  // POIs
  pois: '/pois',
  nearbyPois: '/pois/nearby',
  poi: (id: string) => `/pois/${id}`,
  semanticSearch: '/pois/search/semantic',

  // Transit
  transitRoutes: '/transit/routes',
  nearbyStops: '/transit/stops/nearby',
  departures: (stopId: string) => `/transit/stops/${stopId}/departures`,

  // Weather
  currentWeather: '/weather/current',
  weatherForecast: '/weather/forecast',
  weatherAlerts: '/weather/alerts',

  // Media
  transcribe: '/media/transcribe',
  analyzeImage: '/media/analyze-image',
  uploadMedia: '/media/upload',

  // Users
  profile: '/users/me',
  preferences: '/users/me/preferences',
} as const;
