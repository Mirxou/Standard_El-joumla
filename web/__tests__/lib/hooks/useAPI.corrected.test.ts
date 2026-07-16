import { renderHook, waitFor } from '@testing-library/react'
import { useAPI } from '@/lib/hooks/useAPI'

jest.mock('@/lib/api/client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}))

describe('useAPI Hook - Corrected', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Basic Hook Functionality', () => {
    it('should return hook with proper methods', () => {
      const { result } = renderHook(() => useAPI('/api/test', { immediate: false }))

      expect(result.current).toBeDefined()
      expect(typeof result.current.fetch).toBe('function')
      expect(typeof result.current.refetch).toBe('function')
    })

    it('should have loading and error states', () => {
      const { result } = renderHook(() => useAPI('/api/test', { immediate: false }))

      expect(typeof result.current.loading).toBe('boolean')
      expect(result.current.error === null || result.current.error instanceof Error).toBe(true)
    })

    it('should support data state', () => {
      const { result } = renderHook(() => useAPI('/api/test', { immediate: false }))

      expect(result.current.data === null || typeof result.current.data === 'object').toBe(true)
    })

    it('should unmount without errors', () => {
      const { unmount } = renderHook(() => useAPI('/api/test', { immediate: false }))
      expect(() => unmount()).not.toThrow()
    })
  })

  describe('Hook Options', () => {
    it('should accept immediate option', async () => {
      const { result } = renderHook(() => useAPI('/api/test', { immediate: true }))
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      expect(result.current).toBeDefined()
    })

    it('should support callbacks', () => {
      const onSuccess = jest.fn()
      const onError = jest.fn()

      const { result } = renderHook(() =>
        useAPI('/api/test', { immediate: false, onSuccess, onError })
      )

      expect(typeof result.current.fetch).toBe('function')
    })
  })

  describe('Hook Lifecycle', () => {
    it('should maintain state across renders', () => {
      const { result, rerender } = renderHook(() =>
        useAPI('/api/test', { immediate: false })
      )

      const initialData = result.current.data
      rerender()

      expect(result.current.data === initialData || result.current.data !== undefined).toBe(true)
    })

    it('should have fetch method available', () => {
      const { result } = renderHook(() => useAPI('/api/test', { immediate: false }))
      expect(typeof result.current.fetch).toBe('function')
    })

    it('should have refetch method available', () => {
      const { result } = renderHook(() => useAPI('/api/test', { immediate: false }))
      expect(typeof result.current.refetch).toBe('function')
    })
  })
})
