/**
 * Unit Tests for API Client
 * اختبارات وحدة لعميل API
 */

import { apiClient } from '@/lib/api/client'
import { API_CONFIG } from '@/lib/config/api'

// Mock fetch
global.fetch = jest.fn()

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
  })

  describe('GET requests', () => {
    it('should make GET request successfully', async () => {
      const mockData = { id: 1, name: 'Test' }
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      const result = await apiClient.get('/test')

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test'),
        expect.objectContaining({
          method: 'GET',
        })
      )
      expect(result).toEqual(mockData)
    })

    it('should handle GET request errors', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ detail: 'Resource not found' }),
      })

      await expect(apiClient.get('/test')).rejects.toThrow()
    })
  })

  describe('POST requests', () => {
    it('should make POST request successfully', async () => {
      const mockData = { id: 1, name: 'Created' }
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      const result = await apiClient.post('/test', { name: 'Test' })

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ name: 'Test' }),
        })
      )
      expect(result).toEqual(mockData)
    })
  })

  describe('Token management', () => {
    it('should include token in Authorization header when available', async () => {
      localStorage.setItem('auth_token', 'test-token')
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      })

      await apiClient.get('/test')

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      )
    })
  })

  describe('Error handling', () => {
    it('should retry on network failure', async () => {
      ;(fetch as jest.Mock)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({}),
        })

      await apiClient.get('/test')

      expect(fetch).toHaveBeenCalledTimes(2)
    })
  })
})

