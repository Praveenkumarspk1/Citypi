import { apiClient } from '@shared/utils/api';
import type { User, AuthTokens } from '../types/user';

export const userApi = {
  getProfile: async (): Promise<User> => {
    const { data } = await apiClient.get('/users/me');
    return data;
  },

  updateProfile: async (updates: Partial<User>): Promise<User> => {
    const { data } = await apiClient.put('/users/me', updates);
    return data;
  },

  getPreferences: async (): Promise<unknown> => {
    const { data } = await apiClient.get('/users/me/preferences');
    return data;
  },

  updatePreferences: async (preferences: unknown): Promise<unknown> => {
    const { data } = await apiClient.put('/users/me/preferences', preferences);
    return data;
  },

  login: async (credentials: { email: string; password: string }): Promise<{ user: User; tokens: AuthTokens }> => {
    const { data } = await apiClient.post('/users/login', credentials);
    return data;
  },

  register: async (userData: { email: string; password: string; display_name?: string }): Promise<{ user: User; tokens: AuthTokens }> => {
    const { data } = await apiClient.post('/users/register', userData);
    return data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/users/logout');
  },

  refreshToken: async (refreshToken: string): Promise<AuthTokens> => {
    const { data } = await apiClient.post('/users/refresh', { refresh_token: refreshToken });
    return data;
  },
};
