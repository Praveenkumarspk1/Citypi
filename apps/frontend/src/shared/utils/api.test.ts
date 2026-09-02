import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { handleApiError, buildPaginationParams, queryKeys } from './api';
import axios from 'axios';

// Mock axios
vi.mock('axios');
const mockedAxios = vi.mocked(axios);

describe('API Utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('handleApiError', () => {
    it('should handle axios error with response data', () => {
      const error = {
        isAxiosError: true,
        response: {
          data: {
            error: 'VALIDATION_ERROR',
            message: 'Email is required',
            code: 'ERR_BAD_REQUEST',
          },
          status: 400,
        },
      } as unknown as axios.AxiosError;

      const result = handleApiError(error);
      expect(result).toBe('Email is required');
    });

    it('should handle axios error with response data but no message', () => {
      const error = {
        isAxiosError: true,
        response: {
          data: {
            error: 'VALIDATION_ERROR',
            code: 'ERR_BAD_REQUEST',
          },
          status: 400,
        },
      } as unknown as axios.AxiosError;

      const result = handleApiError(error);
      expect(result).toBe('VALIDATION_ERROR');
    });

    it('should handle axios error with no response data', () => {
      const error = {
        isAxiosError: true,
        message: 'Network Error',
      } as unknown as axios.AxiosError;

      const result = handleApiError(error);
      expect(result).toBe('Network Error');
    });

    it('should handle generic Error', () => {
      const error = new Error('Something went wrong');
      const result = handleApiError(error);
      expect(result).toBe('Something went wrong');
    });

    it('should handle unknown error', () => {
      const result = handleApiError('unknown error');
describe('buildPaginationParams', () => {
    it('should build params with defaults', () => {
      const result = buildPaginationParams({});
      expect(result).toEqual({ page: '1', page_size: '20' });
    });

    it('should use provided page and page_size', () => {
      const result = buildPaginationParams({ page: 3, page_size: 50 });
      expect(result).toEqual({ page: '3', page_size: '50' });
    });

    it('should only include page when page_size not provided', () => {
      const result = buildPaginationParams({ page: 2 });
      expect(result).toEqual({ page: '2', page_size: '20' });
    });

    it('should only include page_size when page not provided', () => {
      const result = buildPaginationParams({ page_size: 10 });
      expect(result).toEqual({ page: '1', page_size: '10' });
    });
  });

  describe('queryKeys', () => {
    it('should generate correct auth keys', () => {
      expect(queryKeys.auth.me).toEqual(['auth', 'me']);
      expect(queryKeys.auth.tokens).toEqual(['auth', 'tokens']);
    });

    it('should generate correct user keys', () => {
      expect(queryKeys.users.me).toEqual(['users', 'me']);
      expect(queryKeys.users.preferences).toEqual(['users', 'preferences']);
      expect(queryKeys.users.list({ page: 1 })).toEqual(['users', 'list', { page: 1 }]);
      expect(queryKeys.users.detail('user-123')).toEqual(['users', 'detail', 'user-123']);
    });

    it('should generate correct conversation keys', () => {
      expect(queryKeys.conversations.list({ page: 1 })).toEqual(['conversations', 'list', { page: 1 }]);
      expect(queryKeys.conversations.detail('conv-123')).toEqual(['conversations', 'detail', 'conv-123']);
      expect(queryKeys.conversations.messages('conv-123', { page: 1 })).toEqual(['conversations', 'messages', 'conv-123', { page: 1 }]);
    });

    it('should generate correct itinerary keys', () => {
      expect(queryKeys.itineraries.list({ page: 1 })).toEqual(['itineraries', 'list', { page: 1 }]);
      expect(queryKeys.itineraries.detail('itin-123')).toEqual(['itineraries', 'detail', 'itin-123']);
      expect(queryKeys.itineraries.days('itin-123')).toEqual(['itineraries', 'days', 'itin-123']);
    });

    it('should generate correct POI keys', () => {
      expect(queryKeys.pois.list({ page: 1 })).toEqual(['pois', 'list', { page: 1 }]);
      expect(queryKeys.pois.detail('poi-123')).toEqual(['pois', 'detail', 'poi-123']);
      expect(queryKeys.pois.search({ query: 'restaurant' })).toEqual(['pois', 'search', { query: 'restaurant' }]);
      expect(queryKeys.pois.nearby(40.7128, -74.0060, 1000, { page: 1 })).toEqual(['pois', 'nearby', 40.7128, -74.0060, 1000, { page: 1 }]);
    });

    it('should generate correct transit keys', () => {
      expect(queryKeys.transit.routes({ page: 1 })).toEqual(['transit', 'routes', { page: 1 }]);
      expect(queryKeys.transit.routeDetail('route-123')).toEqual(['transit', 'route', 'route-123']);
      expect(queryKeys.transit.stopsNearby(40.7128, -74.0060, 500)).toEqual(['transit', 'stops', 'nearby', 40.7128, -74.0060, 500]);
      expect(queryKeys.transit.stopDepartures('stop-123')).toEqual(['transit', 'departures', 'stop-123']);
      expect(queryKeys.transit.agencies()).toEqual(['transit', 'agencies']);
    });

    it('should generate correct weather keys', () => {
      expect(queryKeys.weather.current(40.7128, -74.0060)).toEqual(['weather', 'current', 40.7128, -74.0060]);
      expect(queryKeys.weather.forecast(40.7128, -74.0060, 7)).toEqual(['weather', 'forecast', 40.7128, -74.0060, 7]);
      expect(queryKeys.weather.alerts(40.7128, -74.0060)).toEqual(['weather', 'alerts', 40.7128, -74.0060]);
      expect(queryKeys.weather.historical(40.7128, -74.0060, '2024-01-01', '2024-01-07')).toEqual(['weather', 'historical', 40.7128, -74.0060, '2024-01-01', '2024-01-07']);
    });

    it('should generate correct media keys', () => {
      expect(queryKeys.media.list({ page: 1 })).toEqual(['media', 'list', { page: 1 }]);
      expect(queryKeys.media.detail('media-123')).toEqual(['media', 'detail', 'media-123']);
    });

    it('should generate correct analytics keys', () => {
      expect(queryKeys.analytics.dashboard()).toEqual(['analytics', 'dashboard']);
      expect(queryKeys.analytics.usage({ period: 'week' })).toEqual(['analytics', 'usage', { period: 'week' }]);
    });
  });
});
      expect(result).toBe('An unknown error occurred');
    });

    it('should handle null/undefined error', () => {
      const result = handleApiError(null);
      expect(result).toBe('An unknown error occurred');
    });
  });
