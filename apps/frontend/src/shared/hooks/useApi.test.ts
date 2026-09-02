import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useLogin, useCurrentUser, useCreateItinerary, usePOISearch } from './useApi'
import { api } from '../utils/api'

// Mock the api
vi.mock('../utils/api', () => ({
  api: {
    auth: {
      login: vi.fn(),
    },
    users: {
      getMe: vi.fn(),
    },
    itineraries: {
      create: vi.fn(),
    },
    pois: {
      search: vi.fn(),
    },
  },
  queryKeys: {
    auth: { me: ['auth', 'me'] },
    users: { me: ['users', 'me'] },
    itineraries: { all: ['itineraries'] },
    pois: { search: (params: any) => ['pois', 'search', params] },
  },
}))

describe('useApi hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('useLogin', () => {
    it('should return login mutation', () => {
      const { result } = renderHook(() => useLogin())

      expect(result.current.mutate).toBeDefined()
      expect(result.current.mutateAsync).toBeDefined()
    })

    it('should call api.auth.login on mutate', async () => {
      const mockResponse = { user: { id: '1', email: 'test@test.com' }, token: 'abc123' }
      vi.mocked(api.auth.login).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useLogin())

      await act(async () => {
        await result.current.mutateAsync({ email: 'test@test.com', password: 'password' })
      })

      expect(api.auth.login).toHaveBeenCalledWith({ email: 'test@test.com', password: 'password' })
    })
  })

  describe('useCurrentUser', () => {
    it('should return user query', () => {
      const { result } = renderHook(() => useCurrentUser())

      expect(result.current.data).toBeDefined()
      expect(result.current.isLoading).toBeDefined()
      expect(result.current.error).toBeDefined()
    })

    it('should call api.users.getMe', async () => {
      const mockUser = { id: '1', email: 'test@test.com', name: 'Test User' }
      vi.mocked(api.users.getMe).mockResolvedValue(mockUser)

      const { result } = renderHook(() => useCurrentUser())

      // Wait for query to resolve
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })

      expect(api.users.getMe).toHaveBeenCalled()
    })
  })

  describe('useCreateItinerary', () => {
    it('should return create itinerary mutation', () => {
      const { result } = renderHook(() => useCreateItinerary())

      expect(result.current.mutate).toBeDefined()
      expect(result.current.mutateAsync).toBeDefined()
    })

    it('should call api.itineraries.create on mutate', async () => {
      const mockItinerary = { id: '1', title: 'Test Trip', status: 'draft' }
      vi.mocked(api.itineraries.create).mockResolvedValue(mockItinerary)

      const { result } = renderHook(() => useCreateItinerary())

      await act(async () => {
        await result.current.mutateAsync({ title: 'Test Trip', startDate: '2024-06-01', endDate: '2024-06-05' })
      })

      expect(api.itineraries.create).toHaveBeenCalledWith({ title: 'Test Trip', startDate: '2024-06-01', endDate: '2024-06-05' })
    })
  })

  describe('usePOISearch', () => {
    it('should return POI search query', () => {
      const { result } = renderHook(() => usePOISearch({ query: 'restaurant' }))

      expect(result.current.data).toBeDefined()
      expect(result.current.isLoading).toBeDefined()
      expect(result.current.error).toBeDefined()
    })

    it('should call api.pois.search with params', async () => {
      const mockResponse = { 
        items: [{ id: '1', name: 'Restaurant' }], 
        total: 1, 
        page: 1, 
        page_size: 10, 
        total_pages: 1, 
        has_next: false, 
        has_prev: false 
      }
      vi.mocked(api.pois.search).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => usePOISearch({ query: 'restaurant', page: 1 }))

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0))
      })

      expect(api.pois.search).toHaveBeenCalledWith({ query: 'restaurant', page: 1 })
    })
  })
})
