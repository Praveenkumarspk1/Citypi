import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { act } from 'react';
import { useAuthStore } from './authStore';
import type { User, AuthTokens } from '@shared/types';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

// Test data
const mockUser: User = {
  id: 'user-123',
  email: 'test@example.com',
  display_name: 'Test User',
  avatar_url: 'https://example.com/avatar.png',
  locale: 'en',
  timezone: 'UTC',
  interests: ['museums', 'food'],
  budget_level: 'mid_range',
  accessibility_needs: [],
  dietary_restrictions: ['vegetarian'],
  preferred_transport_modes: ['walking', 'transit'],
  role: 'user',
  status: 'active',
  email_verified: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  last_login_at: '2024-01-01T00:00:00Z',
};

const mockTokens: AuthTokens = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'bearer',
  expires_in: 3600,
};

describe('AuthStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    useAuthStore.setState({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: true,
      error: null,
    });
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.tokens).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(true);
      expect(state.error).toBeNull();
    });
  });

  describe('setAuth', () => {
    it('should set user, tokens, and authenticated state', () => {
      const { setAuth } = useAuthStore.getState();
      act(() => { setAuth(mockUser, mockTokens); });
      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.tokens).toEqual(mockTokens);
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });

    it('should persist to localStorage', () => {
      const { setAuth } = useAuthStore.getState();
      act(() => { setAuth(mockUser, mockTokens); });
      expect(localStorageMock.setItem).toHaveBeenCalledWith('auth-storage', expect.stringContaining('"user"'));
    });
  });
describe('setUser', () => {
    it('should update user and authentication state', () => {
      const { setUser } = useAuthStore.getState();
      act(() => { setUser(mockUser); });
      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
    });

    it('should set authenticated to false when user is null', () => {
      act(() => { useAuthStore.getState().setUser(mockUser); });
      act(() => { useAuthStore.getState().setUser(null); });
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('setTokens', () => {
    it('should update tokens', () => {
      const { setTokens } = useAuthStore.getState();
      act(() => { setTokens(mockTokens); });
      const state = useAuthStore.getState();
      expect(state.tokens).toEqual(mockTokens);
    });

    it('should handle null tokens', () => {
      act(() => { useAuthStore.getState().setTokens(mockTokens); });
      act(() => { useAuthStore.getState().setTokens(null); });
      const state = useAuthStore.getState();
      expect(state.tokens).toBeNull();
    });
  });

  describe('setLoading', () => {
    it('should update loading state', () => {
      const { setLoading } = useAuthStore.getState();
      act(() => { setLoading(false); });
      expect(useAuthStore.getState().isLoading).toBe(false);
      act(() => { setLoading(true); });
      expect(useAuthStore.getState().isLoading).toBe(true);
    });
  });

  describe('setError', () => {
    it('should set error message', () => {
      const { setError } = useAuthStore.getState();
      act(() => { setError('Test error message'); });
      expect(useAuthStore.getState().error).toBe('Test error message');
    });

    it('should clear error when set to null', () => {
      act(() => { useAuthStore.getState().setError('Some error'); });
      act(() => { useAuthStore.getState().setError(null); });
      expect(useAuthStore.getState().error).toBeNull();
    });
  });
});
describe('logout', () => {
    it('should clear all auth state', () => {
      act(() => { useAuthStore.getState().setAuth(mockUser, mockTokens); });
      act(() => { useAuthStore.getState().logout(); });
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.tokens).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.error).toBeNull();
    });

    it('should clear localStorage', () => {
      act(() => { useAuthStore.getState().setAuth(mockUser, mockTokens); });
      act(() => { useAuthStore.getState().logout(); });
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth-storage');
    });
  });

  describe('updateUser', () => {
    it('should partially update user', () => {
      act(() => { useAuthStore.getState().setAuth(mockUser, mockTokens); });
      act(() => { useAuthStore.getState().updateUser({ display_name: 'Updated Name' }); });
      const state = useAuthStore.getState();
      expect(state.user?.display_name).toBe('Updated Name');
      expect(state.user?.email).toBe(mockUser.email);
    });

    it('should not update if no user exists', () => {
      act(() => { useAuthStore.getState().updateUser({ display_name: 'Updated Name' }); });
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
    });
  });

  describe('Persistence', () => {
    it('should persist user, tokens, and isAuthenticated', () => {
      act(() => { useAuthStore.getState().setAuth(mockUser, mockTokens); });
      const stored = localStorageMock.setItem.mock.calls[0][1];
      const parsed = JSON.parse(stored);
      expect(parsed.state.user).toEqual(mockUser);
      expect(parsed.state.tokens).toEqual(mockTokens);
      expect(parsed.state.isAuthenticated).toBe(true);
      expect(parsed.state.isLoading).toBeUndefined();
      expect(parsed.state.error).toBeUndefined();
    });
  });
});
});