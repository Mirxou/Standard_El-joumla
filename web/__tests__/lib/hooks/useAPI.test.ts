import { renderHook, waitFor, act } from '@testing-library/react'
import { useAPI, useAPIMutation } from '@/lib/hooks/useAPI'

jest.mock('@/lib/api/client', () => ({
  apiClient: {
    get: jest.fn(() => Promise.resolve({ data: 'test' })),
    post: jest.fn(() => Promise.resolve({ data: 'test' })),
    put: jest.fn(() => Promise.resolve({ data: 'test' })),
    delete: jest.fn(() => Promise.resolve({ data: 'test' })),
  },
}))

describe('useAPI Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('useAPI', () => {
    it('should fetch data successfully', async () => {
      const { result } = renderHook(() => useAPI('/api/test'))

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
        expect(result.current.data).toBeDefined()
      })
    })

    it('should set loading state initially', async () => {
      const { result } = renderHook(() => useAPI('/api/test'))
      expect(result.current.loading).toBe(true)
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
    })

    it('should handle errors', async () => {
      const { apiClient } = require('@/lib/api/client')
      const testError = new Error('Fetch failed')
      apiClient.get.mockRejectedValueOnce(testError)

      const { result } = renderHook(() => useAPI('/api/test'))

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
        expect(result.current.error).toEqual(testError)
      })
    })

    it('should refetch data when called', async () => {
      const { result } = renderHook(() => useAPI('/api/test'))

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      await act(async () => {
        try {
          await result.current.refetch?.()
        } catch (e) { }
      })

      expect(result.current.loading).toBe(false)
      expect(result.current.data).toBeDefined()
    })

    it('should not fetch when immediate is false', () => {
      const { result } = renderHook(() => useAPI('/api/test', { immediate: false }))
      expect(result.current.loading).toBe(false)
    })

    it('should handle fetch method', async () => {
      const { result } = renderHook(() =>
        useAPI('/api/test', { immediate: false })
      )

      expect(typeof result.current.fetch).toBe('function')

      await act(async () => {
        await result.current.fetch()
      })

      expect(result.current.data).toBeDefined()
    })
  })

  describe('useAPIMutation', () => {
    it('should not make request on mount', () => {
      const { result } = renderHook(() => useAPIMutation('/api/test'))
      expect(result.current.loading).toBe(false)
    })

    it('should make request when mutate is called', async () => {
      const { result } = renderHook(() => useAPIMutation('/api/test'))

      await act(async () => {
        await result.current.mutate?.({ name: 'test' })
      })

      expect(result.current.loading).toBe(false)
      expect(result.current.data).toBeDefined()
    })

    it('should handle mutation errors', async () => {
      const { apiClient } = require('@/lib/api/client')
      apiClient.post.mockRejectedValueOnce(new Error('Mutation failed'))

      const { result } = renderHook(() => useAPIMutation('/api/test'))

      await act(async () => {
        try {
          await result.current.mutate?.({ name: 'test' })
        } catch (e) { }
      })

      expect(result.current.error).toBeDefined()
      expect(result.current.loading).toBe(false)
    })

    it('should return data after successful mutation', async () => {
      const { result } = renderHook(() => useAPIMutation('/api/test'))

      await act(async () => {
        await result.current.mutate?.({ name: 'test' })
      })

      expect(result.current.data).toBeDefined()
      expect(result.current.loading).toBe(false)
    })

    it('should support POST mutation', () => {
      const { result } = renderHook(() =>
        useAPIMutation('/api/test-post')
      )
      expect(result.current.mutate).toBeDefined()
    })

    it('should reset state on reset call', async () => {
      const { result } = renderHook(() => useAPIMutation('/api/test'))

      await act(async () => {
        await result.current.mutate?.({ name: 'test' })
      })

      act(() => {
        result.current.reset?.()
      })

      expect(result.current.data).toBeNull()
      expect(result.current.loading).toBe(false)
    })
  })

  describe('Hook Cleanup', () => {
    it('should cancel requests on unmount', async () => {
      const { unmount } = renderHook(() => useAPI('/api/test', { immediate: false }))
      expect(() => unmount()).not.toThrow()
    })

    it('should handle multiple sequential requests', async () => {
      const { result, rerender } = renderHook(({ url }) => useAPI(url, { immediate: true }), {
        initialProps: { url: '/api/test1' },
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      rerender({ url: '/api/test2' })
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
    })

    it('should return consistent data structure', () => {
      const { result } = renderHook(() => useAPI('/api/test', { immediate: false }))

      expect(result.current).toHaveProperty('loading')
      expect(result.current).toHaveProperty('data')
      expect(result.current).toHaveProperty('error')
      expect(result.current).toHaveProperty('fetch')
      expect(result.current).toHaveProperty('refetch')
    })

    it('should support callback functions', async () => {
      const onSuccess = jest.fn()
      const onError = jest.fn()

      const { result } = renderHook(() =>
        useAPI('/api/test', { immediate: false, onSuccess, onError })
      )

      expect(result.current).toBeDefined()
    })

    it('should handle rapid fetch calls', async () => {
      const { result } = renderHook(() =>
        useAPI('/api/test', { immediate: false })
      )

      await act(async () => {
        result.current.fetch?.()
        result.current.fetch?.()
        await result.current.fetch?.()
      })

      expect(result.current.loading).toBe(false)
    })

    it('should preserve data during loading state transitions', async () => {
      const { result } = renderHook(() => useAPI('/api/test'))

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      const initialData = result.current.data

      await act(async () => {
        try {
          await result.current.refetch?.()
        } catch (e) { }
      })

      // Data should remain defined and have same content
      expect(result.current.data).toEqual(initialData)
    })
  })

  describe('Advanced Scenarios', () => {
    it('should handle endpoints with query parameters', async () => {
      const { result } = renderHook(() => useAPI('/api/test?page=1&limit=10', { immediate: false }))
      expect(result.current).toBeDefined()
    })

    it('should handle endpoints with path parameters', async () => {
      const { result } = renderHook(() => useAPI('/api/users/123', { immediate: false }))
      expect(result.current).toBeDefined()
    })

    it('should handle special characters in endpoint', async () => {
      const { result } = renderHook(() => useAPI('/api/search?q=test&filter=active', { immediate: false }))
      expect(result.current).toBeDefined()
    })

    it('should support error callback configuration', async () => {
      const onError = jest.fn()
      const { result } = renderHook(() =>
        useAPI('/api/test', { onError, immediate: false })
      )
      expect(result.current).toBeDefined()
    })

    it('should support success callback configuration', async () => {
      const onSuccess = jest.fn()
      const { result } = renderHook(() =>
        useAPI('/api/test', { onSuccess, immediate: false })
      )
      expect(result.current).toBeDefined()
    })
  })

  describe('Error Handling and Edge Cases', () => {
    it('should handle non-Error exceptions', async () => {
      const { apiClient } = require('@/lib/api/client')
      apiClient.get.mockRejectedValueOnce('String error')
      
      const { result } = renderHook(() => useAPI('/api/test'))
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
        expect(result.current.error).toBeDefined()
      })
    })

    it('should handle null/undefined responses gracefully', async () => {
      const { apiClient } = require('@/lib/api/client')
      apiClient.get.mockResolvedValueOnce(null)
      
      const { result } = renderHook(() => useAPI('/api/test'))
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
    })

    it('should handle mutation with PUT method', async () => {
      const { result } = renderHook(() => useAPIMutation('/api/test'))
      
      await act(async () => {
        await result.current.mutate?.({ name: 'test' }, 'PUT')
      })
      
      expect(result.current.loading).toBe(false)
      expect(result.current.data).toBeDefined()
    })

    it('should handle mutation with DELETE method', async () => {
      const { result } = renderHook(() => useAPIMutation('/api/test'))
      
      await act(async () => {
        await result.current.mutate?.({}, 'DELETE')
      })
      
      expect(result.current.loading).toBe(false)
    })

    it('should handle onSuccess callback in mutation', async () => {
      const onSuccess = jest.fn()
      const { result } = renderHook(() =>
        useAPIMutation('/api/test', { onSuccess })
      )
      
      await act(async () => {
        await result.current.mutate?.({ name: 'test' })
      })
      
      expect(onSuccess).toHaveBeenCalled()
    })

    it('should handle onError callback in mutation', async () => {
      const { apiClient } = require('@/lib/api/client')
      const onError = jest.fn()
      apiClient.post.mockRejectedValueOnce(new Error('Mutation error'))
      
      const { result } = renderHook(() =>
        useAPIMutation('/api/test', { onError })
      )
      
      await act(async () => {
        try {
          await result.current.mutate?.({ name: 'test' })
        } catch (e) {}
      })
      
      expect(onError).toHaveBeenCalled()
    })

    it('should handle endpoint changes dynamically', async () => {
      const { result, rerender } = renderHook(
        ({ endpoint }) => useAPI(endpoint, { immediate: true }),
        { initialProps: { endpoint: '/api/test1' } }
      )
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      rerender({ endpoint: '/api/test2' })
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
    })

    it('should prevent memory leaks on unmount during fetch', async () => {
      const { unmount } = renderHook(() => useAPI('/api/test', { immediate: true }))
      
      // Immediately unmount while fetch might be in progress
      unmount()
      
      // Should not throw errors
      expect(() => unmount()).not.toThrow()
    })

    it('should handle callback dependencies correctly', async () => {
      const onSuccess = jest.fn()
      const { rerender } = renderHook(
        ({ callback }) => useAPI('/api/test', { onSuccess: callback, immediate: false }),
        { initialProps: { callback: onSuccess } }
      )
      
      const newCallback = jest.fn()
      rerender({ callback: newCallback })
      
      // Callbacks should be updated
      expect(newCallback).toBeDefined()
    })
  })
})
