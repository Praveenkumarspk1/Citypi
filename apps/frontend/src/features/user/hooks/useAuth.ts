import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@shared/stores/authStore';

export function useAuth() {
  const { user, tokens, isAuthenticated, logout, setAuth } = useAuthStore();
  const queryClient = useQueryClient();

  const loginMutation = useMutation({
    mutationFn: async (credentials: { email: string; password: string }) => {
      const { apiClient } = await import('@shared/utils/api');
      const { data } = await apiClient.post('/users/login', credentials);
      return data;
    },
    onSuccess: (data) => {
      setAuth(data.user, data.tokens);
    },
  });

  const logoutHandler = () => {
    logout();
    queryClient.clear();
  };

  return {
    user,
    tokens,
    isAuthenticated,
    login: loginMutation.mutateAsync,
    logout: logoutHandler,
    isLoading: loginMutation.isPending,
  };
}
