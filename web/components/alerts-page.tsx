"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  AlertTriangle, 
  AlertCircle, 
  Info, 
  CheckCircle, 
  Search,
  Filter,
  Bell,
  Clock,
  Package,
  Calendar,
  TrendingDown,
  XCircle
} from 'lucide-react'
import { useNotifications } from "@/lib/notifications/notification-context"
import NotificationCenter from "@/components/notification-center"

export default function AlertsPage() {
  const { notifications, unreadCount } = useNotifications()
  const [searchTerm, setSearchTerm] = useState("")
  const [activeTab, setActiveTab] = useState("all")

  const alerts = [
    {
      id: 1,
      type: "critical",
      category: "stock",
      title: "مخزون حرج",
      message: "سماعات بلوتوث لاسلكية - متبقي 8 وحدات فقط",
      product: "سماعات بلوتوث",
      timestamp: "منذ 5 دقائق",
      read: false
    },
    {
      id: 2,
      type: "warning",
      category: "expiry",
      title: "قرب انتهاء الصلاحية",
      message: "شوكولاتة فاخرة - تنتهي في 2024-08-20 (3 أيام)",
      product: "شوكولاتة فاخرة",
      timestamp: "منذ 15 دقيقة",
      read: false
    },
    {
      id: 3,
      type: "info",
      category: "order",
      title: "طلبية جديدة",
      message: "فاتورة #1234 - بقيمة 450 ر.س",
      timestamp: "منذ 30 دقيقة",
      read: false
    },
    {
      id: 4,
      type: "warning",
      category: "stock",
      title: "مخزون منخفض",
      message: "شامبو الأطفال - متبقي 12 وحدة (الحد الأدنى: 25)",
      product: "شامبو الأطفال",
      timestamp: "منذ ساعة",
      read: true
    },
    {
      id: 5,
      type: "critical",
      category: "expiry",
      title: "منتج منتهي الصلاحية",
      message: "حليب الأطفال - انتهت الصلاحية في 2024-07-10",
      product: "حليب الأطفال",
      timestamp: "منذ ساعتين",
      read: false
    },
    {
      id: 6,
      type: "success",
      category: "delivery",
      title: "تم استلام الشحنة",
      message: "شحنة من المورد - شركة الزيوت المتميزة",
      timestamp: "منذ 3 ساعات",
      read: true
    },
    {
      id: 7,
      type: "info",
      category: "payment",
      title: "دفعة جديدة",
      message: "تم استلام دفعة بقيمة 1,250 ر.س من العميل أحمد محمد",
      timestamp: "منذ 4 ساعات",
      read: true
    },
    {
      id: 8,
      type: "warning",
      category: "stock",
      title: "طلب إعادة الطلب",
      message: "زيت الزيتون - وصل للحد الأدنى (20 وحدة)",
      product: "زيت الزيتون",
      timestamp: "منذ 5 ساعات",
      read: true
    }
  ]

  const getAlertIcon = (type: string) => {
    switch (type) {
      case "critical":
        return <XCircle className="h-5 w-5 text-red-500" />
      case "warning":
        return <AlertTriangle className="h-5 w-5 text-orange-500" />
      case "info":
        return <Info className="h-5 w-5 text-blue-500" />
      case "success":
        return <CheckCircle className="h-5 w-5 text-green-500" />
      default:
        return <AlertCircle className="h-5 w-5 text-gray-500" />
    }
  }

  const getAlertColor = (type: string) => {
    switch (type) {
      case "critical":
        return "border-l-4 border-red-500 bg-red-50"
      case "warning":
        return "border-l-4 border-orange-500 bg-orange-50"
      case "info":
        return "border-l-4 border-blue-500 bg-blue-50"
      case "success":
        return "border-l-4 border-green-500 bg-green-50"
      default:
        return "border-l-4 border-gray-500 bg-gray-50"
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "stock":
        return <Package className="h-4 w-4" />
      case "expiry":
        return <Calendar className="h-4 w-4" />
      case "order":
        return <TrendingDown className="h-4 w-4" />
      default:
        return <Bell className="h-4 w-4" />
    }
  }

  const filteredAlerts = alerts.filter(alert => {
    const matchesSearch = alert.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         alert.title.toLowerCase().includes(searchTerm.toLowerCase())
    
    if (activeTab === "all") return matchesSearch
    if (activeTab === "unread") return matchesSearch && !alert.read
    if (activeTab === "critical") return matchesSearch && alert.type === "critical"
    if (activeTab === "stock") return matchesSearch && alert.category === "stock"
    if (activeTab === "expiry") return matchesSearch && alert.category === "expiry"
    
    return matchesSearch
  })

  const stats = {
    total: alerts.length,
    unread: alerts.filter(a => !a.read).length,
    critical: alerts.filter(a => a.type === "critical").length,
    warning: alerts.filter(a => a.type === "warning").length
  }

  return (
    <div className="space-y-6">
      {/* العنوان */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">التنبيهات والإشعارات</h1>
          <p className="text-gray-600">مركز إدارة جميع التنبيهات والإشعارات</p>
        </div>
      </div>

      {/* Notification Center */}
      <NotificationCenter />

      {/* الإحصائيات */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">إجمالي التنبيهات</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
              </div>
              <Bell className="h-10 w-10 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">غير مقروء</p>
                <p className="text-2xl font-bold text-blue-600">{stats.unread}</p>
              </div>
              <AlertCircle className="h-10 w-10 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">حرجة</p>
                <p className="text-2xl font-bold text-red-600">{stats.critical}</p>
              </div>
              <XCircle className="h-10 w-10 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">تحذيرات</p>
                <p className="text-2xl font-bold text-orange-600">{stats.warning}</p>
              </div>
              <AlertTriangle className="h-10 w-10 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* البحث والفلترة */}
      <Card>
        <CardContent className="p-4">
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="البحث في التنبيهات..."
                className="pr-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Button variant="outline">
              <Filter className="h-4 w-4 ml-2" />
              فلترة
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* قائمة التنبيهات */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="all">الكل ({alerts.length})</TabsTrigger>
          <TabsTrigger value="unread">غير مقروء ({stats.unread})</TabsTrigger>
          <TabsTrigger value="critical">حرجة ({stats.critical})</TabsTrigger>
          <TabsTrigger value="stock">المخزون</TabsTrigger>
          <TabsTrigger value="expiry">الصلاحية</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-3 mt-4">
          {filteredAlerts.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <Bell className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">لا توجد تنبيهات</p>
              </CardContent>
            </Card>
          ) : (
            filteredAlerts.map((alert) => (
              <Card key={alert.id} className={`${getAlertColor(alert.type)} transition-all hover:shadow-md`}>
                <CardContent className="p-4">
                  <div className="flex items-start gap-4">
                    <div className="mt-1">
                      {getAlertIcon(alert.type)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="font-semibold text-gray-900">{alert.title}</h3>
                          <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                        </div>
                        {!alert.read && (
                          <Badge className="bg-blue-500 text-white">جديد</Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                        <div className="flex items-center gap-1">
                          {getCategoryIcon(alert.category)}
                          <span className="capitalize">{alert.category}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          <span>{alert.timestamp}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="ghost" size="sm">
                        عرض
                      </Button>
                      <Button variant="ghost" size="sm" className="text-gray-400">
                        <XCircle className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
