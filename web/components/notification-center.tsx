"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Bell,
  CheckCircle,
  AlertTriangle,
  Info,
  XCircle,
  Package,
  Calendar,
  ShoppingCart,
  DollarSign,
  Truck,
  RotateCcw,
  X,
  CheckCheck,
} from "lucide-react"
import { useNotifications, type Notification, type NotificationType } from "@/lib/notifications/notification-context"
import { formatDistanceToNow } from "date-fns"
import { ar } from "date-fns/locale"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

const getNotificationIcon = (type: NotificationType, category: string) => {
  if (category === 'stock') return <Package className="h-4 w-4" />
  if (category === 'expiry') return <Calendar className="h-4 w-4" />
  if (category === 'order') return <ShoppingCart className="h-4 w-4" />
  if (category === 'payment') return <DollarSign className="h-4 w-4" />
  if (category === 'delivery') return <Truck className="h-4 w-4" />
  if (category === 'return') return <RotateCcw className="h-4 w-4" />
  
  switch (type) {
    case 'success':
      return <CheckCircle className="h-4 w-4" />
    case 'warning':
    case 'critical':
      return <AlertTriangle className="h-4 w-4" />
    case 'error':
      return <XCircle className="h-4 w-4" />
    default:
      return <Info className="h-4 w-4" />
  }
}

const getNotificationColor = (type: NotificationType) => {
  switch (type) {
    case 'success':
      return 'bg-green-50 border-green-200 text-green-900'
    case 'warning':
      return 'bg-yellow-50 border-yellow-200 text-yellow-900'
    case 'error':
    case 'critical':
      return 'bg-red-50 border-red-200 text-red-900'
    default:
      return 'bg-blue-50 border-blue-200 text-blue-900'
  }
}

export default function NotificationCenter() {
  const {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    removeNotification,
  } = useNotifications()
  
  const [filter, setFilter] = useState<'all' | 'unread' | 'read'>('all')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')

  const filteredNotifications = notifications.filter((n) => {
    if (filter === 'unread' && n.read) return false
    if (filter === 'read' && !n.read) return false
    if (categoryFilter !== 'all' && n.category !== categoryFilter) return false
    return true
  })

  const categories = Array.from(new Set(notifications.map((n) => n.category)))

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            مركز الإشعارات
            {unreadCount > 0 && (
              <Badge variant="destructive" className="mr-2">
                {unreadCount} غير مقروء
              </Badge>
            )}
          </CardTitle>
          <div className="flex gap-2">
            {unreadCount > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={markAllAsRead}
              >
                <CheckCheck className="h-4 w-4 ml-2" />
                تحديد الكل كمقروء
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs value={filter} onValueChange={(v) => setFilter(v as 'all' | 'unread' | 'read')}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="all">الكل ({notifications.length})</TabsTrigger>
            <TabsTrigger value="unread">غير مقروء ({unreadCount})</TabsTrigger>
            <TabsTrigger value="read">مقروء ({notifications.length - unreadCount})</TabsTrigger>
          </TabsList>
          
          <div className="mt-4 mb-4">
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full p-2 border rounded-md"
            >
              <option value="all">جميع الفئات</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat === 'stock' ? 'مخزون' :
                   cat === 'expiry' ? 'صلاحية' :
                   cat === 'order' ? 'طلبات' :
                   cat === 'payment' ? 'مدفوعات' :
                   cat === 'delivery' ? 'تسليم' :
                   cat === 'return' ? 'مرتجعات' :
                   cat === 'purchase' ? 'مشتريات' : cat}
                </option>
              ))}
            </select>
          </div>

          <TabsContent value={filter} className="mt-0">
            <ScrollArea className="h-[500px]">
              {filteredNotifications.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Bell className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p>لا توجد إشعارات</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredNotifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={`p-4 rounded-lg border transition-all ${
                        notification.read
                          ? 'bg-gray-50 border-gray-200'
                          : getNotificationColor(notification.type) + ' font-semibold'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-start gap-3 flex-1">
                          <div className={`mt-1 ${notification.read ? 'text-gray-400' : ''}`}>
                            {getNotificationIcon(notification.type, notification.category)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="font-semibold">{notification.title}</h4>
                              {!notification.read && (
                                <div className="h-2 w-2 bg-blue-600 rounded-full" />
                              )}
                            </div>
                            <p className="text-sm text-gray-600 mb-2">{notification.message}</p>
                            <p className="text-xs text-gray-500">
                              {formatDistanceToNow(notification.timestamp, {
                                addSuffix: true,
                                locale: ar,
                              })}
                            </p>
                          </div>
                        </div>
                        <div className="flex gap-1">
                          {!notification.read && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => markAsRead(notification.id)}
                              className="h-8 w-8 p-0"
                            >
                              <CheckCircle className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeNotification(notification.id)}
                            className="h-8 w-8 p-0"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

