// API Client Utility
// Centralized API client with TanStack Query integration for the frontend

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../stores/authStore';
import type { ApiError, PaginatedResponse } from '../types';

// API base URL from environment
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8001';

// Create axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().tokens?.access_token;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config;
    
    // Handle 401 - token expired
    if (error.response?.status === 401 && originalRequest && !originalRequest.url?.includes('/auth/')) {
      // Try to refresh token
      try {
        const refreshToken = useAuthStore.getState().tokens?.refresh_token;
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const {
            access_token,
            refresh_token: newRefreshToken,
            token_type = 'bearer',
            expires_in = 0,
          } = response.data;
          useAuthStore.getState().setTokens({
            access_token,
            refresh_token: newRefreshToken,
            token_type,
            expires_in,
          });
          
          // Retry original request
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }
          return apiClient(originalRequest);
        }
      } catch {
        // Refresh failed, clear auth and redirect
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Generic API response wrapper
export interface ApiResponse<T> {
  data: T;
  meta?: {
    page?: number;
    page_size?: number;
    total?: number;
    total_pages?: number;
  };
}

// Error handling helper
export function handleApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.data) {
      const apiError = error.response.data as ApiError;
      return apiError.message || apiError.error || 'An error occurred';
    }
    if (error.message) {
      return error.message;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unknown error occurred';
}

// Pagination helpers
export interface PaginationParams {
  page?: number;
  page_size?: number;
}

export function buildPaginationParams(params: PaginationParams = {}): Record<string, string> {
  const result: Record<string, string> = {};
  if (params.page) result.page = params.page.toString();
  if (params.page_size) result.page_size = params.page_size.toString();
  return result;
}

// Query key factories for TanStack Query
export const queryKeys = {
  // Auth
  auth: {
    me: ['auth', 'me'] as const,
  },
  
  // Conversations
  conversations: {
    all: ['conversations'] as const,
    list: (params?: PaginationParams) => ['conversations', 'list', params] as const,
    detail: (id: string) => ['conversations', 'detail', id] as const,
    messages: (conversationId: string, params?: PaginationParams) => 
      ['conversations', 'messages', conversationId, params] as const,
  },
  
  // Itineraries
  itineraries: {
    all: ['itineraries'] as const,
    list: (params?: PaginationParams) => ['itineraries', 'list', params] as const,
    detail: (id: string) => ['itineraries', 'detail', id] as const,
    shared: (token: string) => ['itineraries', 'shared', token] as const,
  },
  
  // POIs
  pois: {
    all: ['pois'] as const,
    search: (params: Record<string, any>) => ['pois', 'search', params] as const,
    nearby: (lat: number, lng: number, radius: number, params?: PaginationParams) => 
      ['pois', 'nearby', lat, lng, radius, params] as const,
    detail: (id: string) => ['pois', 'detail', id] as const,
    reviews: (id: string, params?: PaginationParams) => ['pois', 'reviews', id, params] as const,
    photos: (id: string) => ['pois', 'photos', id] as const,
    semanticSearch: (query: string, params?: PaginationParams) => 
      ['pois', 'semantic', query, params] as const,
  },
  
  // Transit
  transit: {
    all: ['transit'] as const,
    routes: (params: Record<string, any>) => ['transit', 'routes', params] as const,
    routeDetail: (id: string) => ['transit', 'route', id] as const,
    stopsNearby: (lat: number, lng: number, radius: number) => 
      ['transit', 'stops', 'nearby', lat, lng, radius] as const,
    departures: (stopId: string) => ['transit', 'departures', stopId] as const,
    agencies: () => ['transit', 'agencies'] as const,
    line: (id: string) => ['transit', 'line', id] as const,
  },
  
  // Weather
  weather: {
    all: ['weather'] as const,
    current: (lat: number, lng: number) => ['weather', 'current', lat, lng] as const,
    forecast: (lat: number, lng: number, days: number) => 
      ['weather', 'forecast', lat, lng, days] as const,
    alerts: (lat: number, lng: number) => ['weather', 'alerts', lat, lng] as const,
    historical: (lat: number, lng: number, start: string, end: string) => 
      ['weather', 'historical', lat, lng, start, end] as const,
  },
  
  // Media
  media: {
    all: ['media'] as const,
    upload: () => ['media', 'upload'] as const,
    transcribe: () => ['media', 'transcribe'] as const,
    analyzeImage: () => ['media', 'analyze'] as const,
  },
  
  // Users
  users: {
    all: ['users'] as const,
    me: ['users', 'me'] as const,
    preferences: ['users', 'preferences'] as const,
  },
  
  // Analytics
  analytics: {
    all: ['analytics'] as const,
    dashboard: () => ['analytics', 'dashboard'] as const,
    usage: (params?: Record<string, any>) => ['analytics', 'usage', params] as const,
  },
} as const;

// Helper to extract data from axios response
function extractData<T>(response: { data: T }): T {
  return response.data;
}

// API endpoint functions
export const api = {
  // Auth
  auth: {
    login: (credentials: { email: string; password: string; remember_me?: boolean }) =>
      apiClient.post('/auth/login', credentials).then(extractData),
    
    register: (data: { email: string; password: string; display_name: string }) =>
      apiClient.post('/auth/register', data).then(extractData),
    
    refresh: (refreshToken: string) =>
      apiClient.post('/auth/refresh', { refresh_token: refreshToken }).then(extractData),
    
    logout: () =>
      apiClient.post('/auth/logout').then(extractData),
    
    forgotPassword: (email: string) =>
      apiClient.post('/auth/forgot-password', { email }).then(extractData),
    
    resetPassword: (token: string, password: string) =>
      apiClient.post('/auth/reset-password', { token, password }).then(extractData),
    
    verifyEmail: (token: string) =>
      apiClient.post('/auth/verify-email', { token }).then(extractData),

    resendVerification: (email: string) =>
      apiClient.post('/auth/resend-verification', { email }).then(extractData),
  },
  
  // Conversations
  conversations: {
    list: (params?: PaginationParams) =>
      apiClient.get<PaginatedResponse<any>>('/conversations', { params: buildPaginationParams(params) }).then(extractData),
    
    create: (data: { initial_message: string; context?: Record<string, any> }) =>
      apiClient.post('/conversations', data).then(extractData),
    
    get: (id: string) =>
      apiClient.get(`/conversations/${id}`).then(extractData),
    
    delete: (id: string) =>
      apiClient.delete(`/conversations/${id}`).then(extractData),
    
    sendMessage: (conversationId: string, data: { content: string; attachments?: any[]; location?: { lat: number; lng: number } }) =>
      apiClient.post(`/conversations/${conversationId}/messages`, data).then(extractData),
    
    getMessages: (conversationId: string, params?: PaginationParams) =>
      apiClient.get<PaginatedResponse<any>>(`/conversations/${conversationId}/messages`, { params: buildPaginationParams(params) }).then(extractData),
    
    sendFeedback: (conversationId: string, messageId: string, data: { rating: number; feedback?: string }) =>
      apiClient.post(`/conversations/${conversationId}/messages/${messageId}/feedback`, data).then(extractData),
    
    // Streaming
    streamMessage: (conversationId: string, data: { content: string; attachments?: any[] }) => {
      return fetch(`${API_BASE_URL}/conversations/${conversationId}/messages/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${useAuthStore.getState().tokens?.access_token}`,
        },
        body: JSON.stringify(data),
      });
    },
  },
  
  // Itineraries
  itineraries: {
    list: (params?: PaginationParams) =>
      apiClient.get<PaginatedResponse<any>>('/itineraries', { params: buildPaginationParams(params) }).then(extractData),
    
    create: (data: any) =>
      apiClient.post('/itineraries', data).then(extractData),
    
    get: (id: string) =>
      apiClient.get(`/itineraries/${id}`).then(extractData),
    
    update: (id: string, data: any) =>
      apiClient.put(`/itineraries/${id}`, data).then(extractData),
    
    delete: (id: string) =>
      apiClient.delete(`/itineraries/${id}`).then(extractData),
    
    share: (id: string) =>
      apiClient.post(`/itineraries/${id}/share`).then(extractData),
    
    getShared: (token: string) =>
      apiClient.get(`/itineraries/shared/${token}`).then(extractData),
    
    // Collaborative editing
    addCollaborator: (id: string, userId: string) =>
      apiClient.post(`/itineraries/${id}/collaborators`, { user_id: userId }).then(extractData),
    
    removeCollaborator: (id: string, userId: string) =>
      apiClient.delete(`/itineraries/${id}/collaborators/${userId}`).then(extractData),
  },
  
  // POIs
  pois: {
    search: (params: {
      query?: string;
      category?: string;
      lat?: number;
      lng?: number;
      radius?: number;
      min_rating?: number;
      tags?: string[];
      page?: number;
      page_size?: number;
    }) =>
      apiClient.get<PaginatedResponse<any>>('/pois', { params }).then(extractData),
    
    nearby: (lat: number, lng: number, radius: number = 5000, params?: PaginationParams) =>
      apiClient.get<PaginatedResponse<any>>('/pois/nearby', {
        params: { lat, lng, radius, ...buildPaginationParams(params) },
      }).then(extractData),
    
    get: (id: string) =>
      apiClient.get(`/pois/${id}`).then(extractData),
    
    reviews: (id: string, params?: PaginationParams) =>
      apiClient.get<PaginatedResponse<any>>(`/pois/${id}/reviews`, { params: buildPaginationParams(params) }).then(extractData),
    
    photos: (id: string) =>
      apiClient.get(`/pois/${id}/photos`).then(extractData),
    
    semanticSearch: (query: string, params?: PaginationParams) =>
      apiClient.post<PaginatedResponse<any>>('/pois/search/semantic', { query, ...params }).then(extractData),
  },
  
  // Transit
  transit: {
    planRoute: (data: {
      origin: { lat: number; lng: number; name?: string };
      destination: { lat: number; lng: number; name?: string };
      departure_time?: string;
      preferences?: {
        wheelchair_accessible?: boolean;
        minimize_transfers?: boolean;
        preferred_modes?: string[];
      };
    }) =>
      apiClient.post('/transit/routes', data).then(extractData),
    
    getRoute: (id: string) =>
      apiClient.get(`/transit/routes/${id}`).then(extractData),
    
    nearbyStops: (lat: number, lng: number, radius: number = 1000) =>
      apiClient.get(`/transit/stops/nearby`, { params: { lat, lng, radius } }).then(extractData),
    
    departures: (stopId: string) =>
      apiClient.get(`/transit/stops/${stopId}/departures`).then(extractData),
    
    agencies: () =>
      apiClient.get('/transit/agencies').then(extractData),
    
    line: (id: string) =>
      apiClient.get(`/transit/lines/${id}`).then(extractData),
  },
  
  // Weather
  weather: {
    current: (lat: number, lng: number) =>
      apiClient.get('/weather/current', { params: { lat, lng } }).then(extractData),
    
    forecast: (lat: number, lng: number, days: number = 7) =>
      apiClient.get('/weather/forecast', { params: { lat, lng, days } }).then(extractData),
    
    alerts: (lat: number, lng: number) =>
      apiClient.get('/weather/alerts', { params: { lat, lng } }).then(extractData),
    
    historical: (lat: number, lng: number, startDate: string, endDate: string) =>
      apiClient.get('/weather/historical', { params: { lat, lng, start_date: startDate, end_date: endDate } }).then(extractData),
  },
  
  // Media
  media: {
    transcribe: (file: File, options?: { language?: string; task?: string }) => {
      const formData = new FormData();
      formData.append('file', file);
      if (options?.language) formData.append('language', options.language);
      if (options?.task) formData.append('task', options.task);
      
      return apiClient.post('/media/transcribe', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then(extractData);
    },
    
    analyzeImage: (file: File, options?: { categories?: string[] }) => {
      const formData = new FormData();
      formData.append('file', file);
      if (options?.categories) formData.append('categories', JSON.stringify(options.categories));
      
      return apiClient.post('/media/analyze-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then(extractData);
    },
    
    upload: (file: File, metadata?: Record<string, any>) => {
      const formData = new FormData();
      formData.append('file', file);
      if (metadata) formData.append('metadata', JSON.stringify(metadata));
      
      return apiClient.post('/media/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then(extractData);
    },
  },
  
  // Users
  users: {
    getMe: () =>
      apiClient.get('/users/me').then(extractData),
    
    updateMe: (data: Partial<{
      display_name: string;
      avatar_url: string;
      locale: string;
      timezone: string;
      interests: string[];
      budget_level: string;
      accessibility_needs: string[];
      dietary_restrictions: string[];
      preferred_transport_modes: string[];
    }>) =>
      apiClient.put('/users/me', data).then(extractData),
    
    getPreferences: () =>
      apiClient.get('/users/me/preferences').then(extractData),
    
    updatePreferences: (data: any) =>
      apiClient.put('/users/me/preferences', data).then(extractData),
    
    deleteAccount: () =>
      apiClient.delete('/users/me').then(extractData),
    
    uploadAvatar: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return apiClient.post('/users/me/avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then(extractData);
    },
  },
  
  // Analytics
  analytics: {
    getDashboard: () =>
      apiClient.get('/analytics/dashboard').then(extractData),
    
    getUsage: (params?: Record<string, any>) =>
      apiClient.get('/analytics/usage', { params }).then(extractData),
    
    trackEvent: (event: string, properties?: Record<string, any>) =>
      apiClient.post('/analytics/events', { event, properties }).then(extractData),
  },
};

// WebSocket connection helper
export function createWebSocketUrl(path: string): string {
  const token = useAuthStore.getState().tokens?.access_token;
  const params = token ? `?token=${encodeURIComponent(token)}` : '';
  return `${WS_BASE_URL}${path}${params}`;
}

export default apiClient;