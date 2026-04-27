"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { TrendingUp, Package, AlertCircle, ShoppingCart, Brain } from 'lucide-react'
import { Badge } from "@/components/ui/badge"

export default function AIForecastDashboard() {
  const [selectedProduct, setSelectedProduct] = useState("all")
  const [forecastData, setForecastData] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  // Fetch forecast data from API
  useEffect(() => {
    const fetchForecastData = async () => {
      try {
        setLoading(true)
        const response = await apiClient.get(API_CONFIG.ENDPOINTS.AI.FORECAST)
        setForecastData(response)
      } catch (e) {
        console.error("Error fetching forecast data:", e)
        setForecastData(null)
      } finally {
        setLoading(false)
      }
    }
    fetchForecastData()
  }, [selectedProduct])

  return (
    <div className="space-y-6" dir="rtl">
      {/* العنوان */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">لوحة الذكاء الاصطناعي</h2>
          <p className="text-gray-500 mt-1">تنبؤات ذكية وتحليلات متقدمة لتحسين الأداء</p>
        </div>
        <Badge className="bg-purple-600 text-white px-4 py-2">
          <Brain className="h-4 w-4 ml-2" />
          مدعوم بالذكاء الاصطناعي
        </Badge>
      </div>

      {/* المقاييس الرئيسية */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">دقة التنبؤ</p>
                <p className="text-2xl font-bold text-green-600">94.5%</p>
                <p className="text-xs text-gray-400 mt-1">آخر 30 يوم</p>
              </div>
              <TrendingUp className="h-10 w-10 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">توفير متوقع</p>
                <p className="text-2xl font-bold text-blue-600">45,280 ر.س</p>
                <p className="text-xs text-gray-400 mt-1">من تحسين المخزون</p>
              </div>
              <Package className="h-10 w-10 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">تحذيرات نشطة</p>
                <p className="text-2xl font-bold text-orange-600">8</p>
                <p className="text-xs text-gray-400 mt-1">تحتاج اهتمام</p>
              </div>
              <AlertCircle className="h-10 w-10 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">الطلب المتوقع</p>
                <p className="text-2xl font-bold text-purple-600">1,245</p>
                <p className="text-xs text-gray-400 mt-1">الأسبوع القادم</p>
              </div>
              <ShoppingCart className="h-10 w-10 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* التنبؤ بالطلب */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>التنبؤ بالطلب - الأسبوع القادم</CardTitle>
            <Select value={selectedProduct} onValueChange={setSelectedProduct}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="اختر منتج" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">جميع المنتجات</SelectItem>
                <SelectItem value="1">منتج 1</SelectItem>
                <SelectItem value="2">منتج 2</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={mockForecastData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip
                labelStyle={{ direction: 'rtl', fontFamily: 'Cairo' }}
                contentStyle={{ direction: 'rtl', fontFamily: 'Cairo' }}
              />
              <Legend
                wrapperStyle={{ direction: 'rtl', fontFamily: 'Cairo' }}
              />
              <Area
                type="monotone"
                dataKey="upper"
                stackId="1"
                stroke="#93c5fd"
                fill="#dbeafe"
                name="الحد الأعلى"
              />
              <Area
                type="monotone"
                dataKey="lower"
                stackId="1"
                stroke="#93c5fd"
                fill="#eff6ff"
                name="الحد الأدنى"
              />
              <Line
                type="monotone"
                dataKey="actual"
                stroke="#10b981"
                strokeWidth={2}
                dot={{ r: 4 }}
                name="الطلب الفعلي"
              />
              <Line
                type="monotone"
                dataKey="forecast"
                stroke="#3b82f6"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ r: 4 }}
                name="التنبؤ"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* تحليل ABC */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>تحليل ABC - تصنيف المنتجات</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg border-r-4 border-green-600">
                <div>
                  <h4 className="font-bold text-green-900">الفئة A</h4>
                  <p className="text-sm text-green-700">منتجات عالية القيمة</p>
                  <p className="text-xs text-green-600 mt-1">{abcAnalysis.A.count} منتج</p>
                </div>
                <div className="text-left">
                  <p className="text-2xl font-bold text-green-900">{abcAnalysis.A.percent}%</p>
                  <p className="text-sm text-green-700">{(abcAnalysis.A.revenue / 1000).toFixed(0)}K ر.س</p>
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border-r-4 border-blue-600">
                <div>
                  <h4 className="font-bold text-blue-900">الفئة B</h4>
                  <p className="text-sm text-blue-700">منتجات متوسطة القيمة</p>
                  <p className="text-xs text-blue-600 mt-1">{abcAnalysis.B.count} منتج</p>
                </div>
                <div className="text-left">
                  <p className="text-2xl font-bold text-blue-900">{abcAnalysis.B.percent}%</p>
                  <p className="text-sm text-blue-700">{(abcAnalysis.B.revenue / 1000).toFixed(0)}K ر.س</p>
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border-r-4 border-gray-600">
                <div>
                  <h4 className="font-bold text-gray-900">الفئة C</h4>
                  <p className="text-sm text-gray-700">منتجات منخفضة القيمة</p>
                  <p className="text-xs text-gray-600 mt-1">{abcAnalysis.C.count} منتج</p>
                </div>
                <div className="text-left">
                  <p className="text-2xl font-bold text-gray-900">{abcAnalysis.C.percent}%</p>
                  <p className="text-sm text-gray-700">{(abcAnalysis.C.revenue / 1000).toFixed(0)}K ر.س</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* تحسين المخزون */}
        <Card>
          <CardHeader>
            <CardTitle>توصيات تحسين المخزون</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stockOptimization.map((item, index) => (
                <div key={index} className="p-3 border rounded-lg hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-gray-900">{item.product}</h4>
                    <Badge variant={
                      item.status === 'critical' ? 'destructive' :
                      item.status === 'low' ? 'secondary' :
                      item.status === 'high' ? 'default' : 'outline'
                    }>
                      {item.status === 'critical' ? 'حرج' :
                       item.status === 'low' ? 'منخفض' :
                       item.status === 'high' ? 'مرتفع' : 'مثالي'}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div>
                      <p className="text-gray-500">المخزون الحالي</p>
                      <p className="font-semibold">{item.current}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">المخزون المثالي</p>
                      <p className="font-semibold text-blue-600">{item.optimal}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">كمية الطلب</p>
                      <p className="font-semibold text-green-600">{item.eoq}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* التوصيات الذكية */}
      <Card>
        <CardHeader>
          <CardTitle>التوصيات الذكية</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-4 bg-red-50 border-r-4 border-red-500 rounded-lg">
              <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-red-900">تحذير: منتجات قريبة من النفاذ</h4>
                <p className="text-sm text-red-700">4 منتجات تحتاج طلب فوري لتجنب نفاذ المخزون</p>
                <Button size="sm" variant="outline" className="mt-2">عرض المنتجات</Button>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 bg-blue-50 border-r-4 border-blue-500 rounded-lg">
              <TrendingUp className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-blue-900">فرصة: زيادة متوقعة في الطلب</h4>
                <p className="text-sm text-blue-700">12 منتج متوقع زيادة طلبها بنسبة 25% الأسبوع القادم</p>
                <Button size="sm" variant="outline" className="mt-2">الاستعداد الآن</Button>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 bg-green-50 border-r-4 border-green-500 rounded-lg">
              <Package className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-green-900">توفير: تحسين كميات الطلب</h4>
                <p className="text-sm text-green-700">يمكن توفير 12,500 ر.س شهرياً بتحسين نقاط إعادة الطلب</p>
                <Button size="sm" variant="outline" className="mt-2">تطبيق التوصيات</Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
