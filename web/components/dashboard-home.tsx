"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Input } from "@/components/ui/input"
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
  Users,
  Warehouse,
  Calendar,
  Settings,
  FolderTree,
  Loader2,
} from "lucide-react"
import { apiClient } from "@/lib/api/client"
import { API_CONFIG } from "@/lib/config/api"
import { toast } from "sonner"
import type { Product, Category } from "@/lib/database/types"

interface DashboardHomeProps {
  setActiveView?: (view: string) => void
}

export default function DashboardHome({ setActiveView }: DashboardHomeProps = {}) {
  const [loading, setLoading] = useState(true)
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
  const [categoryStats, setCategoryStats] = useState<Array<{
    id: string
    name_ar: string
    productCount: number
    totalStock: number
    totalValue: number
    percentage: number
  }>>([])
  const [searchQuery, setSearchQuery] = useState("")

  // جلب البيانات الحقيقية
  useEffect(() => {
    fetchDashboardData()
    const interval = setInterval(() => {
      fetchDashboardData()
    }, 30000) // تحديث كل 30 ثانية

    return () => clearInterval(interval)
  }, [])

  const handleGlobalSearch = (query: string) => {
    if (!query.trim()) return

    // البحث في الفئات
    const categoryMatch = categoryStats.some(cat =>
      cat.name_ar.toLowerCase().includes(query.toLowerCase())
    )

    if (categoryMatch || query.length > 2) {
      // الانتقال لصفحة المنتجات مع البحث
      setActiveView?.("products")
      toast.info(`البحث عن: ${query}`)
    }
  }

  async function fetchDashboardData() {
    try {
      setLoading(true)

      // جلب الإحصائيات العامة
      const statsData = await apiClient.get<any>(API_CONFIG.ENDPOINTS.DASHBOARD.STATS).catch(() => ({}));

      // جلب المنتجات (لإحصائيات الفئات)
      const productsResponse = await apiClient.get<any>(`${API_CONFIG.ENDPOINTS.PRODUCTS}?page_size=100`).catch(() => ({ products: [] }));
      const products = productsResponse.products || productsResponse.data || (Array.isArray(productsResponse) ? productsResponse : []);

      // جلب الفئات
      const categories = await apiClient.get<Category[]>(API_CONFIG.ENDPOINTS.CATEGORIES).catch(() => []);

      // حساب إحصائيات الفئات
      const categoryStatsMap = new Map<string, {
        name_ar: string
        productCount: number
        totalStock: number
        totalValue: number
      }>()

      products.forEach((product: any) => {
        // توحيد category_id إلى number
        const categoryId = product.category_id ? Number(product.category_id) : 0
        const categoryName = product.category_name || 'غير مصنف'

        if (!categoryStatsMap.has(categoryId)) {
          categoryStatsMap.set(categoryId, {
            name_ar: categoryName,
            productCount: 0,
            totalStock: 0,
            totalValue: 0,
          })
        }

        const stats = categoryStatsMap.get(categoryId)!
        stats.productCount++
        stats.totalStock += product.current_stock || 0
        stats.totalValue += (product.current_stock || 0) * (product.cost_price || 0)
      })

      const totalCategoryValue = Array.from(categoryStatsMap.values()).reduce((sum, cat) => sum + cat.totalValue, 0)

      const categoryStatsArray = Array.from(categoryStatsMap.entries()).map(([id, stats]) => ({
        id,
        ...stats,
        percentage: totalCategoryValue > 0 ? (stats.totalValue / totalCategoryValue) * 100 : 0,
      })).sort((a, b) => b.totalValue - a.totalValue).slice(0, 5)

      setCategoryStats(categoryStatsArray)
      setRealTimeData({
        totalRevenue: statsData.total_revenue || 0,
        totalProducts: statsData.products_count || products.length,
        lowStockAlerts: statsData.low_stock_count || 0,
        profitMargin: statsData.profit_margin || 0,
        todaySales: statsData.today_sales || 0,
        pendingOrders: statsData.pending_orders || 0,
        expiringItems: statsData.expiring_items_count || 0,
        activeSuppliers: statsData.suppliers_count || 0,
      })
    } catch (error: any) {
      console.error('[dashboard] Error fetching data:', error)
      toast.error("فشل تحميل بيانات Dashboard")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* شريط البحث المتقدم */}
      <div className="relative">
        <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
        <Input
          placeholder="البحث المتقدم في المنتجات، الفئات، الطلبات..."
          className="pr-12 h-12 bg-white shadow-sm border-gray-300 focus:border-blue-500 focus:ring-blue-500"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && searchQuery.trim()) {
              handleGlobalSearch(searchQuery)
            }
          }}
        />
        {searchQuery && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="absolute left-3 top-1/2 transform -translate-y-1/2"
            onClick={() => {
              handleGlobalSearch(searchQuery)
            }}
          >
            بحث
          </Button>
        )}
      </div>

      {/* مؤشرات الأداء الرئيسية */}
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
              <span className="text-sm text-green-600 font-medium">
                {realTimeData.totalProducts > 0 ? `${realTimeData.totalProducts} منتج` : "لا توجد منتجات"}
              </span>
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
              <span className="text-sm text-blue-600 font-medium">
                {realTimeData.lowStockAlerts > 0 ? `${realTimeData.lowStockAlerts} تنبيه` : "مخزون صحي"}
              </span>
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

      {/* الإجراءات السريعة */}
      <Card className="shadow-lg border-0">
        <CardHeader>
          <CardTitle className="text-xl flex items-center gap-2">
            <Settings className="h-5 w-5 text-blue-600" />
            الإجراءات السريعة
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <Button
              variant="outline"
              className="h-20 flex-col gap-2 bg-gradient-to-br from-blue-50 to-blue-100 hover:from-blue-100 hover:to-blue-200 border-blue-200"
              onClick={() => setActiveView?.("products")}
              type="button"
            >
              <Package className="h-6 w-6 text-blue-600" />
              <span className="text-sm font-medium">إضافة منتج</span>
            </Button>
            <Button
              variant="outline"
              className="h-20 flex-col gap-2 bg-gradient-to-br from-purple-50 to-purple-100 hover:from-purple-100 hover:to-purple-200 border-purple-200"
              onClick={() => setActiveView?.("categories")}
              type="button"
            >
              <FolderTree className="h-6 w-6 text-purple-600" />
              <span className="text-sm font-medium">إدارة الفئات</span>
            </Button>
            <Button
              variant="outline"
              className="h-20 flex-col gap-2 bg-gradient-to-br from-green-50 to-green-100 hover:from-green-100 hover:to-green-200 border-green-200"
              onClick={() => setActiveView?.("sales")}
            >
              <ShoppingCart className="h-6 w-6 text-green-600" />
              <span className="text-sm font-medium">فاتورة جديدة</span>
            </Button>
            <Button
              variant="outline"
              className="h-20 flex-col gap-2 bg-gradient-to-br from-purple-50 to-purple-100 hover:from-purple-100 hover:to-purple-200 border-purple-200"
              onClick={() => setActiveView?.("reports")}
            >
              <BarChart3 className="h-6 w-6 text-purple-600" />
              <span className="text-sm font-medium">تقارير الأرباح</span>
            </Button>
            <Button
              variant="outline"
              className="h-20 flex-col gap-2 bg-gradient-to-br from-orange-50 to-orange-100 hover:from-orange-100 hover:to-orange-200 border-orange-200"
              onClick={() => setActiveView?.("warehouses")}
            >
              <Warehouse className="h-6 w-6 text-orange-600" />
              <span className="text-sm font-medium">إدارة المستودعات</span>
            </Button>
            <Button
              variant="outline"
              className="h-20 flex-col gap-2 bg-gradient-to-br from-red-50 to-red-100 hover:from-red-100 hover:to-red-200 border-red-200"
              onClick={() => setActiveView?.("expiry")}
            >
              <Calendar className="h-6 w-6 text-red-600" />
              <span className="text-sm font-medium">تتبع الصلاحية</span>
            </Button>
            <Button
              variant="outline"
              className="h-20 flex-col gap-2 bg-gradient-to-br from-indigo-50 to-indigo-100 hover:from-indigo-100 hover:to-indigo-200 border-indigo-200"
              onClick={() => setActiveView?.("suppliers")}
            >
              <Users className="h-6 w-6 text-indigo-600" />
              <span className="text-sm font-medium">إدارة الموردين</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* الأنشطة المباشرة والمؤشرات */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* الأنشطة المباشرة */}
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

        {/* مؤشرات الأداء */}
        <Card className="shadow-lg border-0">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-purple-600" />
              مؤشرات الأداء
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

      {/* أداء الفئات */}
      <Card className="shadow-lg border-0">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl flex items-center gap-2">
              <FolderTree className="h-5 w-5 text-blue-600" />
              أداء الفئات
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setActiveView?.("categories")}
              type="button"
            >
              عرض الكل
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : categoryStats.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <FolderTree className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>لا توجد فئات بعد</p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={() => setActiveView?.("categories")}
                type="button"
              >
                إضافة فئة جديدة
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              {categoryStats.map((category, index) => {
                const colors = [
                  "bg-green-500",
                  "bg-blue-500",
                  "bg-purple-500",
                  "bg-orange-500",
                  "bg-pink-500",
                ]
                const color = colors[index % colors.length]

                return (
                  <div key={category.id} className="p-4 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl border hover:shadow-md transition-shadow cursor-pointer" onClick={() => setActiveView?.("products")}>
                    <div className="text-center mb-3">
                      <h3 className="font-semibold text-gray-900 text-sm">{category.name_ar}</h3>
                      <p className="text-xs text-gray-600 mt-1">
                        {category.productCount} منتج
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {category.totalStock.toLocaleString('en-US')} وحدة
                      </p>
                    </div>
                    <div className="relative">
                      <Progress value={category.percentage} className="h-3" />
                      <div className="text-center mt-2">
                        <span className="text-sm font-bold text-gray-700">{category.percentage.toFixed(1)}%</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1 text-center">
                        {category.totalValue.toLocaleString('en-US')} ر.س
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
