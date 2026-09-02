// useApi Hook
// Custom hooks for API calls with TanStack Query

import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { api, queryKeys, type PaginationParams } from '../utils/api';
import type { 
  User, 
  Conversation, 
  Message, 
  Itinerary, 
  POI, 
  TransitRoute, 
  WeatherForecast,
  PaginatedResponse 
} from '../types';

// Auth hooks
export function useLogin() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.auth.login,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.auth.me, data.user);
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.me });
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: api.auth.register,
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.auth.logout,
    onSuccess: () => {
      queryClient.clear();
    },
  });
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: api.auth.forgotPassword,
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: ({ token, password }: { token: string; password: string }) => 
      api.auth.resetPassword(token, password),
  });
}

export function useVerifyEmail() {
  return useMutation({
    mutationFn: api.auth.verifyEmail,
  });
}

export function useResendVerificationEmail() {
  return useMutation({
    mutationFn: (email: string) => api.auth.resendVerification(email),
  });
}

// User hooks
export function useCurrentUser(options?: UseQueryOptions<User, Error>) {
  return useQuery({
    queryKey: queryKeys.users.me,
    queryFn: api.users.getMe,
    ...options,
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.users.updateMe,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.users.me, data);
    },
  });
}

export function useUserPreferences(options?: UseQueryOptions<any, Error>) {
  return useQuery({
    queryKey: queryKeys.users.preferences,
    queryFn: api.users.getPreferences,
    ...options,
  });
}

export function useUpdatePreferences() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.users.updatePreferences,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.users.preferences, data);
    },
  });
}

export function useDeleteAccount() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.users.deleteAccount,
    onSuccess: () => {
      queryClient.clear();
    },
  });
}

export function useUploadAvatar() {
  return useMutation({
    mutationFn: api.users.uploadAvatar,
  });
}

// Conversation hooks
export function useConversations(params?: PaginationParams, options?: UseQueryOptions<PaginatedResponse<Conversation>, Error>) {
  return useQuery({
    queryKey: queryKeys.conversations.list(params),
    queryFn: () => api.conversations.list(params),
    ...options,
  });
}

export function useConversation(id: string, options?: UseQueryOptions<Conversation, Error>) {
  return useQuery({
    queryKey: queryKeys.conversations.detail(id),
    queryFn: () => api.conversations.get(id),
    enabled: !!id,
    ...options,
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.conversations.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations.all });
    },
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.conversations.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations.all });
    },
  });
}

export function useConversationMessages(conversationId: string, params?: PaginationParams, options?: UseQueryOptions<PaginatedResponse<Message>, Error>) {
  return useQuery({
    queryKey: queryKeys.conversations.messages(conversationId, params),
    queryFn: () => api.conversations.getMessages(conversationId, params),
    enabled: !!conversationId,
    ...options,
  });
}

export function useSendMessage() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ conversationId, data }: { conversationId: string; data: any }) => 
      api.conversations.sendMessage(conversationId, data),
    onSuccess: (_, { conversationId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations.messages(conversationId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations.detail(conversationId) });
    },
  });
}

export function useSendFeedback() {
  return useMutation({
    mutationFn: ({ conversationId, messageId, data }: { conversationId: string; messageId: string; data: any }) => 
      api.conversations.sendFeedback(conversationId, messageId, data),
  });
}

// Itinerary hooks
export function useItineraries(params?: PaginationParams, options?: UseQueryOptions<PaginatedResponse<Itinerary>, Error>) {
  return useQuery({
    queryKey: queryKeys.itineraries.list(params),
    queryFn: () => api.itineraries.list(params),
    ...options,
  });
}

export function useItinerary(id: string, options?: UseQueryOptions<Itinerary, Error>) {
  return useQuery({
    queryKey: queryKeys.itineraries.detail(id),
    queryFn: () => api.itineraries.get(id),
    enabled: !!id,
    ...options,
  });
}

export function useSharedItinerary(token: string, options?: UseQueryOptions<Itinerary, Error>) {
  return useQuery({
    queryKey: queryKeys.itineraries.shared(token),
    queryFn: () => api.itineraries.getShared(token),
    enabled: !!token,
    ...options,
  });
}

export function useCreateItinerary() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.itineraries.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.itineraries.all });
    },
  });
}

export function useUpdateItinerary() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => api.itineraries.update(id, data),
    onSuccess: (data, { id }) => {
      queryClient.setQueryData(queryKeys.itineraries.detail(id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.itineraries.all });
    },
  });
}

export function useDeleteItinerary() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.itineraries.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.itineraries.all });
    },
  });
}

export function useShareItinerary() {
  return useMutation({
    mutationFn: api.itineraries.share,
  });
}

export function useAddCollaborator() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, userId }: { id: string; userId: string }) => api.itineraries.addCollaborator(id, userId),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.itineraries.detail(id) });
    },
  });
}

export function useRemoveCollaborator() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, userId }: { id: string; userId: string }) => api.itineraries.removeCollaborator(id, userId),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.itineraries.detail(id) });
    },
  });
}

// POI hooks
export function usePOISearch(params: any, options?: UseQueryOptions<PaginatedResponse<POI>, Error>) {
  return useQuery({
    queryKey: queryKeys.pois.search(params),
    queryFn: () => api.pois.search(params),
    ...options,
  });
}

export function useNearbyPOIs(lat: number, lng: number, radius: number = 5000, params?: PaginationParams, options?: UseQueryOptions<PaginatedResponse<POI>, Error>) {
  return useQuery({
    queryKey: queryKeys.pois.nearby(lat, lng, radius, params),
    queryFn: () => api.pois.nearby(lat, lng, radius, params),
    enabled: lat !== undefined && lng !== undefined,
    ...options,
  });
}

export function usePOI(id: string, options?: UseQueryOptions<POI, Error>) {
  return useQuery({
    queryKey: queryKeys.pois.detail(id),
    queryFn: () => api.pois.get(id),
    enabled: !!id,
    ...options,
  });
}

export function usePOIReviews(id: string, params?: PaginationParams, options?: UseQueryOptions<PaginatedResponse<any>, Error>) {
  return useQuery({
    queryKey: queryKeys.pois.reviews(id, params),
    queryFn: () => api.pois.reviews(id, params),
    enabled: !!id,
    ...options,
  });
}

export function usePOIPhotos(id: string, options?: UseQueryOptions<any[], Error>) {
  return useQuery({
    queryKey: queryKeys.pois.photos(id),
    queryFn: () => api.pois.photos(id),
    enabled: !!id,
    ...options,
  });
}

export function useSemanticPOISearch(query: string, params?: PaginationParams, options?: UseQueryOptions<PaginatedResponse<POI>, Error>) {
  return useQuery({
    queryKey: queryKeys.pois.semanticSearch(query, params),
    queryFn: () => api.pois.semanticSearch(query, params),
    enabled: !!query,
    ...options,
  });
}

// Transit hooks
export function usePlanRoute() {
  return useMutation({
    mutationFn: api.transit.planRoute,
  });
}

export function useTransitRoute(id: string, options?: UseQueryOptions<TransitRoute, Error>) {
  return useQuery({
    queryKey: queryKeys.transit.routeDetail(id),
    queryFn: () => api.transit.getRoute(id),
    enabled: !!id,
    ...options,
  });
}

export function useNearbyStops(lat: number, lng: number, radius: number = 1000, options?: UseQueryOptions<any[], Error>) {
  return useQuery({
    queryKey: queryKeys.transit.stopsNearby(lat, lng, radius),
    queryFn: () => api.transit.nearbyStops(lat, lng, radius),
    enabled: lat !== undefined && lng !== undefined,
    ...options,
  });
}

export function useDepartures(stopId: string, options?: UseQueryOptions<any[], Error>) {
  return useQuery({
    queryKey: queryKeys.transit.departures(stopId),
    queryFn: () => api.transit.departures(stopId),
    enabled: !!stopId,
    refetchInterval: 30000, // Refresh every 30 seconds
    ...options,
  });
}

export function useAgencies(options?: UseQueryOptions<any[], Error>) {
  return useQuery({
    queryKey: queryKeys.transit.agencies(),
    queryFn: api.transit.agencies,
    ...options,
  });
}

export function useTransitLine(id: string, options?: UseQueryOptions<any, Error>) {
  return useQuery({
    queryKey: queryKeys.transit.line(id),
    queryFn: () => api.transit.line(id),
    enabled: !!id,
    ...options,
  });
}

// Weather hooks
export function useCurrentWeather(lat: number, lng: number, options?: Omit<UseQueryOptions<any, Error>, 'queryKey'>) {
  return useQuery({
    queryKey: queryKeys.weather.current(lat, lng),
    queryFn: () => api.weather.current(lat, lng),
    enabled: lat !== undefined && lng !== undefined,
    refetchInterval: 600000, // Refresh every 10 minutes
    ...options,
  });
}

export function useWeatherForecast(lat: number, lng: number, days: number = 7, options?: Omit<UseQueryOptions<WeatherForecast, Error>, 'queryKey'>) {
  return useQuery({
    queryKey: queryKeys.weather.forecast(lat, lng, days),
    queryFn: () => api.weather.forecast(lat, lng, days),
    enabled: lat !== undefined && lng !== undefined,
    refetchInterval: 1800000, // Refresh every 30 minutes
    ...options,
  });
}

export function useWeatherAlerts(lat: number, lng: number, options?: Omit<UseQueryOptions<any, Error>, 'queryKey'>) {
  return useQuery({
    queryKey: queryKeys.weather.alerts(lat, lng),
    queryFn: () => api.weather.alerts(lat, lng),
    enabled: lat !== undefined && lng !== undefined,
    refetchInterval: 300000, // Refresh every 5 minutes
    ...options,
  });
}

export function useHistoricalWeather(lat: number, lng: number, startDate: string, endDate: string, options?: UseQueryOptions<any[], Error>) {
  return useQuery({
    queryKey: queryKeys.weather.historical(lat, lng, startDate, endDate),
    queryFn: () => api.weather.historical(lat, lng, startDate, endDate),
    enabled: lat !== undefined && lng !== undefined && !!startDate && !!endDate,
    ...options,
  });
}

// Media hooks
export function useTranscribeAudio() {
  return useMutation({
    mutationFn: ({ file, options }: { file: File; options?: any }) => api.media.transcribe(file, options),
  });
}

export function useAnalyzeImage() {
  return useMutation({
    mutationFn: ({ file, options }: { file: File; options?: any }) => api.media.analyzeImage(file, options),
  });
}

export function useUploadMedia() {
  return useMutation({
    mutationFn: ({ file, metadata }: { file: File; metadata?: any }) => api.media.upload(file, metadata),
  });
}

// Analytics hooks
export function useAnalyticsDashboard(options?: UseQueryOptions<any, Error>) {
  return useQuery({
    queryKey: queryKeys.analytics.dashboard(),
    queryFn: api.analytics.getDashboard,
    ...options,
  });
}

export function useAnalyticsUsage(params?: Record<string, any>, options?: UseQueryOptions<any, Error>) {
  return useQuery({
    queryKey: queryKeys.analytics.usage(params),
    queryFn: () => api.analytics.getUsage(params),
    ...options,
  });
}

export function useTrackEvent() {
  return useMutation({
    mutationFn: ({ event, properties }: { event: string; properties?: any }) => api.analytics.trackEvent(event, properties),
  });
}