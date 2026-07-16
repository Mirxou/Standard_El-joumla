/**
 * Hook مخصص للـ API requests مع loading و error handling
 */

import { useState, useCallback, useEffect } from 'react'
import { apiClient } from '@/lib/api/client'

export interface UseAPIOptions {
  immediate?: boolean
  onSuccess?: (data: any) => void
  onError?: (error: Error) => void
}

export function useAPI<T = any>(
  endpoint: string,
  options: UseAPIOptions = {}
) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const { immediate = true, onSuccess, onError } = options

  const fetch = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await apiClient.get<T>(endpoint)
      setData(result)
      onSuccess?.(result)
      return result
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      setError(error)
      onError?.(error)
      throw error
    } finally {
      setLoading(false)
    }
  }, [endpoint, onSuccess, onError])

  useEffect(() => {
    if (immediate) {
      fetch().catch(() => {
        // Error is already handled within fetch() via setError
      })
    }
  }, [endpoint, immediate, fetch])

  return { data, loading, error, fetch, refetch: fetch }
}

/**
 * Hook للـ POST requests
 */
export function useAPIMutation<T = any>(
  endpoint: string,
  options: UseAPIOptions = {}
) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const { onSuccess, onError } = options

  const mutate = useCallback(
    async (payload: any, method: 'POST' | 'PUT' | 'DELETE' = 'POST') => {
      try {
        setLoading(true)
        setError(null)

        let result: T
        switch (method) {
          case 'POST':
            result = await apiClient.post<T>(endpoint, payload)
            break
          case 'PUT':
            result = await apiClient.put<T>(endpoint, payload)
            break
          case 'DELETE':
            result = await apiClient.delete<T>(endpoint)
            break
        }

        setData(result)
        onSuccess?.(result)
        return result
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err))
        setError(error)
        onError?.(error)
        throw error
      } finally {
        setLoading(false)
      }
    },
    [endpoint, onSuccess, onError]
  )

  return { data, loading, error, mutate, reset: () => setData(null) }
}
