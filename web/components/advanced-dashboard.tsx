"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  Package,
  ShoppingCart,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  DollarSign,
  BarChart3,
  Bell,
  Search,
  Plus,
  Menu,
  Users,
  Warehouse,
  Calendar,
  Settings,
  Download,
} from "lucide-react"
import { Input } from "@/components/ui/input"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import Navigation from "@/components/navigation"
import InventoryManagement from "@/components/inventory-management"
import SalesManagement from "@/components/sales-management"
import ProfitReports from "@/components/profit-reports"
import WarehouseManagement from "@/components/warehouse-management"
import ExpiryTracking from "@/components/expiry-tracking"
import SupplierManagement from "@/components/supplier-management"
import AdvancedReports from "@/components/advanced-reports"

export default function AdvancedDashboard() {
  const [activeView, setActiveView] = useState("dashboard")
  const [realTimeData, setRealTimeData] = useState({
    totalRevenue: 0,
    totalProducts: 0,
    lowStockAlerts: 0,
    profitMargin: 0,
    todaySales: 0,
    pendingOrders: 0,
    expiringItems: 0,
    activeSuppliers: 0,
  })

  // Simulate real-time data updates
  useEffect(() => {
    const interval = setInterval(() => {
      setRealTimeData((prev) => ({
        totalRevenue: prev.totalRevenue + Math.random() * 1000,
        totalProducts: 1247 + Math.floor(Math.random() * 10),
        lowStockAlerts: 23 + Math.floor(Math.random() * 5),
        profitMargin: 32.4 + (Math.random() - 0.5) * 2,
        todaySales: prev.todaySales + Math.random() * 500,
        pendingOrders: 8 + Math.floor(Math.random() * 3),
        expiringItems: 15 + Math.floor(Math.random() * 5),
        activeSuppliers: 45 + Math.floor(Math.random() * 3),
      }))
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const renderContent = () => {
    switch (activeView) {
      case "inventory":
        return <InventoryManagement />
      case "sales":
        return <SalesManagement />
      case "reports":
        return <ProfitReports />
      case "warehouses":
        return <WarehouseManagement />
      case "expiry":
        return <ExpiryTracking />
      case "suppliers":
        return <SupplierManagement />
      case "advanced-reports":
        return <AdvancedReports />
      default:
        return <AdvancedDashboardContent realTimeData={realTimeData} />
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50" dir="rtl">
      {/* Professional Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-lg backdrop-blur-sm bg-white/95">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-4">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="md:hidden">
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-64 p-0">
                <Navigation activeView={activeView} setActiveView={setActiveView} />
              </SheetContent>
            </Sheet>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-green-600 rounded-lg flex items-center justify-center">
                <Package className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Standard</h1>
                <p className="text-xs text-blue-600 font-semibold">شعارنا للأبد</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-5 w-5" />
              <Badge className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs bg-red-500">
                {realTimeData.lowStockAlerts}
              </Badge>
            </Button>
            <Button
              size="sm"
              className="bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700"
            >
              <Plus className="h-4 w-4 ml-1" />
              إضافة جديد
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 ml-1" />
              تصدير
            </Button>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Professional Sidebar */}
        <div className="hidden md:block w-64 bg-white border-l border-gray-200 min-h-screen shadow-lg">
          <Navigation activeView={activeView} setActiveView={setActiveView} />
        </div>

        {/* Main Content */}
        <main className="flex-1 p-6">{renderContent()}</main>
      </div>
    </div>
  )
}

function AdvancedDashboardContent({ realTimeData }: { realTimeData: any }) {
  return (
    <div className="space-y-6">
      {/* Professional Search Bar */}
      <div className="relative">
        <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
        <Input
          placeholder="البحث المتقدم في المنتجات، الطلبات، العملاء، أو الموردين..."
          className="pr-12 h-12 bg-white shadow-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      {/* Real-time KPI Dashboard */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="hover:shadow-xl transition-all duration-300 border-0 shadow-lg bg-gradient-to-br from-green-50 to-green-100">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-700 font-medium">إجمالي الإيرادات</p>
                <p className="text-3xl font-bold text-green-800">{realTimeData.totalRevenue.toLocaleString('en-US')} ر.س</p>
              </div>
              <div className="bg-green-200 p-3 rounded-xl">
                <DollarSign className="h-6 w-6 text-green-700" />
              </div>
            </div>
            <div className="flex items-center mt-3">
              <TrendingUp className="h-4 w-4 text-green-600 ml-1" />
              <span className="text-sm text-green-600 font-medium">+12.5% من الشهر الماضي</span>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-xl transition-all duration-300 border-0 shadow-lg bg-gradient-to-br from-blue-50 to-blue-100">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-700 font-medium">إجمالي المنتجات</p>
                <p className="text-3xl font-bold text-blue-800">{realTimeData.totalProducts.toLocaleString('en-US')}</p>
              </div>
              <div className="bg-blue-200 p-3 rounded-xl">
                <Package className="h-6 w-6 text-blue-700" />
              </div>
            </div>
            <div className="flex items-center mt-3">
              <TrendingUp className="h-4 w-4 text-blue-600 ml-1" />
              <span className="text-sm text-blue-600 font-medium">+8.2% نمو المخزون</span>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-xl transition-all duration-300 border-0 shadow-lg bg-gradient-to-br from-orange-50 to-orange-100">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-orange-700 font-medium">تنبيهات المخزون</p>
                <p className="text-3xl font-bold text-orange-800">{realTimeData.lowStockAlerts}</p>
              </div>
              <div className="bg-orange-200 p-3 rounded-xl">
                <AlertTriangle className="h-6 w-6 text-orange-700" />
              </div>
            </div>
            <div className="flex items-center mt-3">
              <TrendingDown className="h-4 w-4 text-orange-600 ml-1" />
              <span className="text-sm text-orange-600 font-medium">يتطلب إجراء فوري</span>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-xl transition-all duration-300 border-0 shadow-lg bg-gradient-to-br from-purple-50 to-purple-100">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-700 font-medium">هامش الربح</p>
                <p className="text-3xl font-bold text-purple-800">{realTimeData.profitMargin.toFixed(1)}%</p>
              </div>
              <div className="bg-purple-200 p-3 rounded-xl">
                <BarChart3 className="h-6 w-6 text-purple-700" />
              </div>
            </div>
            <div className="flex items-center mt-3">
              <TrendingUp className="h-4 w-4 text-purple-600 ml-1" />
              <span className="text-sm text-purple-600 font-medium">+2.1% تحسن</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Professional Quick Actions */}
      <Card className="shadow-lg border-0">
        <CardHeader>
          <CardTitle className="text-xl flex items-center gap-2">
            <Settings className="h-5 w-5 text-blue-600" />
            الإجراءات السريعة المتقدمة
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <Button
              variant="outline"
              className="h-20 flex-col gap-2 bg-gradient-to-br from-blue-50 to-blue-100 hover:from-blue-100 hover:to-blue-200 border-blue-200"
            >
              <Package className="h-6 w-6 text-blue-600" />
              <span className="text-sm font-medium">إضافة منتج</span>
            </Button>
            <Button
              variant="outline"
              className="h-20 flex-col gap-2 bg-gradient-to-br from-green-50 to-green-100 hover:from-green-100 hover:to-green-200 border-green-200"
            >
              <ShoppingCart className="h-6 w-6 text-green-600" />
              <span className="text-sm font-medium">فاتورة جديدة</span>
            </Button>
            <Button
              variant="outline"
              className="h-20 flex-col gap-2 bg-gradient-to-br from-purple-50 to-purple-100 hover:from-purple-100 hover:to-purple-200 border-purple-200"
            >
              <BarChart3 className="h-6 w-6 text-purple-600" />
              <span className="text-sm font-medium">تقارير الأرباح</span>
            </Button>
            <Button
              variant="outline"
              className="h-20 flex-col gap-2 bg-gradient-to-br from-orange-50 to-orange-100 hover:from-orange-100 hover:to-orange-200 border-orange-200"
            >
              <Warehouse className="h-6 w-6 text-orange-600" />
              <span className="text-sm font-medium">إدارة المستودعات</span>
            </Button>
            <Button
              variant="outline"
              className="h-20 flex-col gap-2 bg-gradient-to-br from-red-50 to-red-100 hover:from-red-100 hover:to-red-200 border-red-200"
            >
              <Calendar className="h-6 w-6 text-red-600" />
              <span className="text-sm font-medium">تتبع الصلاحية</span>
            </Button>
            <Button
              variant="outline"
              className="h-20 flex-col gap-2 bg-gradient-to-br from-indigo-50 to-indigo-100 hover:from-indigo-100 hover:to-indigo-200 border-indigo-200"
            >
              <Users className="h-6 w-6 text-indigo-600" />
              <span className="text-sm font-medium">إدارة الموردين</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Advanced Analytics Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Real-time Activity Feed */}
        <Card className="shadow-lg border-0">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <Bell className="h-5 w-5 text-blue-600" />
                الأنشطة المباشرة
              </CardTitle>
              <Badge className="bg-green-100 text-green-800">مباشر</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gradient-to-r from-green-50 to-green-100 rounded-xl border border-green-200">
                <div className="flex items-center gap-3">
                  <div className="bg-green-200 p-2 rounded-lg">
                    <Package className="h-5 w-5 text-green-700" />
                  </div>
                  <div>
                    <p className="font-semibold text-green-900">وصول مخزون جديد</p>
                    <p className="text-sm text-green-700">إلكترونيات - 50 قطعة</p>
                  </div>
                </div>
                <span className="text-xs text-green-600 font-medium">الآن</span>
              </div>

              <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-blue-100 rounded-xl border border-blue-200">
                <div className="flex items-center gap-3">
                  <div className="bg-blue-200 p-2 rounded-lg">
                    <DollarSign className="h-5 w-5 text-blue-700" />
                  </div>
                  <div>
                    <p className="font-semibold text-blue-900">عملية بيع مكتملة</p>
                    <p className="text-sm text-blue-700">طلب #1248 - 450 ر.س</p>
                  </div>
                </div>
                <span className="text-xs text-blue-600 font-medium">منذ دقيقة</span>
              </div>

              <div className="flex items-center justify-between p-4 bg-gradient-to-r from-orange-50 to-orange-100 rounded-xl border border-orange-200">
                <div className="flex items-center gap-3">
                  <div className="bg-orange-200 p-2 rounded-lg">
                    <AlertTriangle className="h-5 w-5 text-orange-700" />
                  </div>
                  <div>
                    <p className="font-semibold text-orange-900">تنبيه مخزون منخفض</p>
                    <p className="text-sm text-orange-700">سماعات بلوتوث - 3 متبقية</p>
                  </div>
                </div>
                <span className="text-xs text-orange-600 font-medium">منذ 3 دقائق</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Advanced Performance Metrics */}
        <Card className="shadow-lg border-0">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-purple-600" />
              مؤشرات الأداء المتقدمة
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="font-medium">كفاءة المخزون</span>
                  <span className="font-bold text-green-600">92%</span>
                </div>
                <Progress value={92} className="h-3 bg-gray-200" />
                <p className="text-xs text-gray-600 mt-1">معدل دوران المخزون ممتاز</p>
              </div>

              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="font-medium">رضا العملاء</span>
                  <span className="font-bold text-blue-600">88%</span>
                </div>
                <Progress value={88} className="h-3 bg-gray-200" />
                <p className="text-xs text-gray-600 mt-1">تقييم ممتاز من العملاء</p>
              </div>

              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="font-medium">كفاءة الموردين</span>
                  <span className="font-bold text-purple-600">85%</span>
                </div>
                <Progress value={85} className="h-3 bg-gray-200" />
                <p className="text-xs text-gray-600 mt-1">أداء جيد للموردين</p>
              </div>

              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="font-medium">نمو المبيعات</span>
                  <span className="font-bold text-orange-600">76%</span>
                </div>
                <Progress value={76} className="h-3 bg-gray-200" />
                <p className="text-xs text-gray-600 mt-1">نمو مستمر في المبيعات</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Professional Category Performance */}
      <Card className="shadow-lg border-0">
        <CardHeader>
          <CardTitle className="text-xl flex items-center gap-2">
            <Package className="h-5 w-5 text-blue-600" />
            أداء الفئات المتخصصة
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {[
              { name: "المواد الغذائية", value: 85, color: "bg-green-500", sales: "89,500 ر.س" },
              { name: "صحة وجمال", value: 72, color: "bg-blue-500", sales: "67,200 ر.س" },
              { name: "منتجات النظافة", value: 68, color: "bg-purple-500", sales: "45,600 ر.س" },
              { name: "الإلكترونيات", value: 91, color: "bg-orange-500", sales: "78,900 ر.س" },
              { name: "الحلويات", value: 94, color: "bg-pink-500", sales: "34,200 ر.س" },
            ].map((category, index) => (
              <div key={index} className="p-4 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl border">
                <div className="text-center mb-3">
                  <h3 className="font-semibold text-gray-900 text-sm">{category.name}</h3>
                  <p className="text-xs text-gray-600 mt-1">{category.sales}</p>
                </div>
                <div className="relative">
                  <Progress value={category.value} className="h-3" />
                  <div className="text-center mt-2">
                    <span className="text-sm font-bold text-gray-700">{category.value}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
