"use client"

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api/client'
import { API_CONFIG } from '@/lib/config/api'

export type NotificationType = 'info' | 'success' | 'warning' | 'error' | 'critical'
export type NotificationCategory = 'stock' | 'expiry' | 'order' | 'payment' | 'delivery' | 'system' | 'purchase' | 'return'

export interface Notification {
  id: string
  type: NotificationType
  category: NotificationCategory
  title: string
  message: string
  timestamp: Date
  read: boolean
  actionUrl?: string
  metadata?: Record<string, any>
}

interface NotificationContextType {
  notifications: Notification[]
  unreadCount: number
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  removeNotification: (id: string) => void
  clearAll: () => void
  loadNotifications: () => Promise<void>
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const loadNotifications = useCallback(async () => {
    try {
      setIsLoading(true)
      // محاولة جلب الإشعارات من API
      const data = await apiClient.get<any>('/api/v1/notifications').catch(() => null)
      
      if (data && Array.isArray(data)) {
        const loadedNotifications = data.map((n: any) => ({
          id: n.id?.toString() || Date.now().toString(),
          type: n.type || 'info',
          category: n.category || 'system',
          title: n.title || 'إشعار',
          message: n.message || '',
          timestamp: new Date(n.timestamp || Date.now()),
          read: n.read || false,
          actionUrl: n.action_url,
          metadata: n.metadata,
        }))
        setNotifications(loadedNotifications)
      }
    } catch (error) {
      console.error('Failed to load notifications:', error)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadNotifications()
    
    // تحديث الإشعارات كل 30 ثانية
    const interval = setInterval(loadNotifications, 30000)
    return () => clearInterval(interval)
  }, [loadNotifications])

  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      timestamp: new Date(),
      read: false,
    }

    setNotifications((prev) => [newNotification, ...prev])

    // عرض toast notification
    const toastConfig = {
      info: { type: 'info' as const },
      success: { type: 'success' as const },
      warning: { type: 'warning' as const },
      error: { type: 'error' as const },
      critical: { type: 'error' as const, duration: 10000 },
    }

    const config = toastConfig[notification.type] || toastConfig.info
    const toastOptions: any = {
      description: notification.message,
    }
    if ('duration' in config && config.duration !== undefined) {
      toastOptions.duration = config.duration
    } else {
      toastOptions.duration = notification.type === 'critical' || notification.type === 'error' ? 0 : 5000
    }
    toast[config.type](notification.title, toastOptions)

    // حفظ في API إذا كان متاحاً
    apiClient.post('/api/v1/notifications', {
      type: notification.type,
      category: notification.category,
      title: notification.title,
      message: notification.message,
      action_url: notification.actionUrl,
      metadata: notification.metadata,
    }).catch(() => {
      // تجاهل الأخطاء في حفظ الإشعارات
    })
  }, [])

  const markAsRead = useCallback(async (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    )

    // تحديث في API
    await apiClient.put(`/api/v1/notifications/${id}/read`).catch(() => {})
  }, [])

  const markAllAsRead = useCallback(async () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))

    // تحديث في API
    await apiClient.put('/api/v1/notifications/read-all').catch(() => {})
  }, [])

  const removeNotification = useCallback(async (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))

    // حذف من API
    await apiClient.delete(`/api/v1/notifications/${id}`).catch(() => {})
  }, [])

  const clearAll = useCallback(() => {
    setNotifications([])
  }, [])

  const unreadCount = notifications.filter((n) => !n.read).length

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        addNotification,
        markAsRead,
        markAllAsRead,
        removeNotification,
        clearAll,
        loadNotifications,
      }}
    >
      {children}
    </NotificationContext.Provider>
  )
}

export function useNotifications() {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider')
  }
  return context
}

