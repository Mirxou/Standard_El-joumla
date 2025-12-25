"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Package,
  ShoppingCart,
  Users,
  BarChart3,
  Download,
  Calendar,
  Filter,
  FileText,
  PieChart,
  Activity,
} from "lucide-react"
import { BarChart, Bar, LineChart, Line, PieChart as RePieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from "recharts"

export default function AdvancedReportsPage() {
  const [dateRange, setDateRange] = useState("month")
  const [reportType, setReportType] = useState("sales")

  // بيانات تقارير المبيعات
  const salesData = [
    { month: "يناير", sales: 45000, profit: 12000, orders: 234 },
    { month: "فبراير", sales: 52000, profit: 15600, orders: 267 },
    { month: "مارس", sales: 48000, profit: 13440, orders: 245 },
    { month: "أبريل", sales: 61000, profit: 18300, orders: 298 },
    { month: "مايو", sales: 55000, profit: 16500, orders: 276 },
    { month: "يونيو", sales: 67000, profit: 20100, orders: 312 },
  ]

  // بيانات المنتجات الأكثر مبيعاً
  const topProducts = [
    { name: "زيت الزيتون", sales: 12500, units: 450, category: "مواد غذائية" },
    { name: "شامبو الأطفال", sales: 8900, units: 320, category: "صحة وجمال" },
    { name: "سماعات بلوتوث", sales: 15600, units: 180, category: "إلكترونيات" },
    { name: "شوكولاتة فاخرة", sales: 6700, units: 560, category: "حلويات" },
    { name: "منظف الأطباق", sales: 5400, units: 290, category: "منتجات النظافة" },
  ]

  // بيانات توزيع المبيعات حسب الفئة
  const categoryData = [
    { name: "مواد غذائية", value: 35, amount: 23450 },
    { name: "صحة وجمال", value: 25, amount: 16750 },
    { name: "إلكترونيات", value: 20, amount: 13400 },
    { name: "حلويات", value: 12, amount: 8040 },
    { name: "منتجات النظافة", value: 8, amount: 5360 },
  ]

  // بيانات الأرباح اليومية
  const dailyProfitData = [
    { day: "السبت", revenue: 8500, cost: 5100, profit: 3400 },
    { day: "الأحد", revenue: 9200, cost: 5520, profit: 3680 },
    { day: "الاثنين", revenue: 7800, cost: 4680, profit: 3120 },
    { day: "الثلاثاء", revenue: 10500, cost: 6300, profit: 4200 },
    { day: "الأربعاء", revenue: 9800, cost: 5880, profit: 3920 },
    { day: "الخميس", revenue: 11200, cost: 6720, profit: 4480 },
    { day: "الجمعة", revenue: 6900, cost: 4140, profit: 2760 },
  ]

  // بيانات المخزون
  const inventoryData = [
    { category: "متوفر", count: 450, percentage: 65, color: "#22c55e" },
    { category: "منخفض", count: 120, percentage: 17, color: "#f59e0b" },
    { category: "حرج", count: 80, percentage: 12, color: "#ef4444" },
    { category: "نفد", count: 42, percentage: 6, color: "#6b7280" },
  ]

  const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">التقارير المتقدمة</h1>
          <p className="text-gray-600">تحليلات شاملة ومفصلة للمبيعات والأرباح والمخزون</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline">
            <Download className="h-4 w-4 ml-2" />
            تصدير PDF
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 ml-2" />
            تصدير Excel
          </Button>
        </div>
      </div>

      {/* الفلاتر */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-48">
              <Select value={reportType} onValueChange={setReportType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sales">تقرير المبيعات</SelectItem>
                  <SelectItem value="profit">تقرير الأرباح</SelectItem>
                  <SelectItem value="inventory">تقرير المخزون</SelectItem>
                  <SelectItem value="products">تقرير المنتجات</SelectItem>
                  <SelectItem value="customers">تقرير العملاء</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex-1 min-w-48">
              <Select value={dateRange} onValueChange={setDateRange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="today">اليوم</SelectItem>
                  <SelectItem value="week">هذا الأسبوع</SelectItem>
                  <SelectItem value="month">هذا الشهر</SelectItem>
                  <SelectItem value="quarter">هذا الربع</SelectItem>
                  <SelectItem value="year">هذا العام</SelectItem>
                  <SelectItem value="custom">تخصيص</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button>
              <Filter className="h-4 w-4 ml-2" />
              تطبيق الفلاتر
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* الإحصائيات الرئيسية */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">إجمالي المبيعات</p>
                <p className="text-2xl font-bold text-blue-600">328,000 ر.س</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="h-3 w-3 text-green-600" />
                  <span className="text-xs text-green-600">+12.5%</span>
                </div>
              </div>
              <div className="bg-blue-100 p-3 rounded-lg">
                <DollarSign className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">إجمالي الأرباح</p>
                <p className="text-2xl font-bold text-green-600">95,940 ر.س</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="h-3 w-3 text-green-600" />
                  <span className="text-xs text-green-600">+15.3%</span>
                </div>
              </div>
              <div className="bg-green-100 p-3 rounded-lg">
                <TrendingUp className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">عدد الطلبات</p>
                <p className="text-2xl font-bold text-purple-600">1,632</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="h-3 w-3 text-green-600" />
                  <span className="text-xs text-green-600">+8.7%</span>
                </div>
              </div>
              <div className="bg-purple-100 p-3 rounded-lg">
                <ShoppingCart className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">هامش الربح</p>
                <p className="text-2xl font-bold text-orange-600">29.3%</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingDown className="h-3 w-3 text-red-600" />
                  <span className="text-xs text-red-600">-2.1%</span>
                </div>
              </div>
              <div className="bg-orange-100 p-3 rounded-lg">
                <Activity className="h-6 w-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* التقارير التفصيلية */}
      <Tabs defaultValue="sales" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="sales">المبيعات</TabsTrigger>
          <TabsTrigger value="profit">الأرباح</TabsTrigger>
          <TabsTrigger value="products">المنتجات</TabsTrigger>
          <TabsTrigger value="inventory">المخزون</TabsTrigger>
        </TabsList>

        {/* تبويب المبيعات */}
        <TabsContent value="sales" className="space-y-4">
          <div className="grid lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-blue-600" />
                  المبيعات الشهرية
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={salesData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="sales" fill="#3b82f6" name="المبيعات" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="h-5 w-5 text-green-600" />
                  توزيع المبيعات حسب الفئة
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RePieChart>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={(entry: any) => `${entry.name}: ${entry.value}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </RePieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* تبويب الأرباح */}
        <TabsContent value="profit" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-600" />
                الأرباح اليومية (آخر أسبوع)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={dailyProfitData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area type="monotone" dataKey="revenue" stackId="1" stroke="#3b82f6" fill="#3b82f6" name="الإيرادات" />
                  <Area type="monotone" dataKey="cost" stackId="2" stroke="#ef4444" fill="#ef4444" name="التكاليف" />
                  <Area type="monotone" dataKey="profit" stackId="3" stroke="#10b981" fill="#10b981" name="الأرباح" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>ملخص الأرباح</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {dailyProfitData.map((day, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Calendar className="h-5 w-5 text-gray-400" />
                      <span className="font-medium">{day.day}</span>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-left">
                        <p className="text-xs text-gray-500">إيرادات</p>
                        <p className="text-sm font-semibold text-blue-600">{day.revenue.toLocaleString('en-US')} ر.س</p>
                      </div>
                      <div className="text-left">
                        <p className="text-xs text-gray-500">تكاليف</p>
                        <p className="text-sm font-semibold text-red-600">{day.cost.toLocaleString('en-US')} ر.س</p>
                      </div>
                      <div className="text-left">
                        <p className="text-xs text-gray-500">صافي الربح</p>
                        <p className="text-sm font-semibold text-green-600">{day.profit.toLocaleString('en-US')} ر.س</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* تبويب المنتجات */}
        <TabsContent value="products" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5 text-purple-600" />
                أفضل 5 منتجات مبيعاً
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topProducts.map((product, index) => (
                  <div key={index} className="flex items-center justify-between p-4 border rounded-lg hover:shadow-md transition-shadow">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center font-bold text-purple-600">
                        {index + 1}
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900">{product.name}</h4>
                        <Badge variant="outline" className="mt-1">
                          {product.category}
                        </Badge>
                      </div>
                    </div>
                    <div className="text-left">
                      <p className="text-lg font-bold text-green-600">{product.sales.toLocaleString('en-US')} ر.س</p>
                      <p className="text-sm text-gray-500">{product.units} وحدة مباعة</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* تبويب المخزون */}
        <TabsContent value="inventory" className="space-y-4">
          <div className="grid lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-5 w-5 text-orange-600" />
                  حالة المخزون
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RePieChart>
                    <Pie
                      data={inventoryData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={(entry: any) => `${entry.category}: ${entry.percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                    >
                      {inventoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </RePieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>ملخص المخزون</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {inventoryData.map((item, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-4 h-4 rounded-full"
                            style={{ backgroundColor: item.color }}
                          />
                          <span className="font-medium">{item.category}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-sm text-gray-600">{item.count} منتج</span>
                          <Badge style={{ backgroundColor: item.color, color: "white" }}>
                            {item.percentage}%
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-900">
                    <strong>إجمالي المنتجات:</strong> {inventoryData.reduce((sum, item) => sum + item.count, 0)} منتج
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
