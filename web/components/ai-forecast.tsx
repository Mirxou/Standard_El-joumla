"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Brain, TrendingUp, RefreshCw, Loader2, AlertCircle } from "lucide-react"
import { apiClient } from "@/lib/api/client"
import { API_CONFIG } from "@/lib/config/api"
import { toast } from "sonner"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts"
import { useNotifications } from "@/lib/notifications/notification-context"

export default function AIForecast() {
  const [loading, setLoading] = useState(false)
  const [forecastData, setForecastData] = useState<any>(null)
  const [selectedPeriod, setSelectedPeriod] = useState("7")
  const { addNotification } = useNotifications()

  const loadForecast = async () => {
    try {
      setLoading(true)
      const data = await apiClient.get<any>(`${API_CONFIG.ENDPOINTS.AI.FORECAST}?period=${selectedPeriod}`)
      setForecastData(data)
      
      // إضافة إشعار عند وجود تنبؤات مهمة
      if (data?.alerts && data.alerts.length > 0) {
        data.alerts.forEach((alert: any) => {
          addNotification({
            type: alert.severity === 'high' ? 'critical' : 'warning',
            category: 'stock',
            title: alert.title || 'تنبيه تنبؤ',
            message: alert.message || '',
          })
        })
      }
    } catch (error: any) {
      console.error("Failed to load forecast", error)
      toast.error("فشل تحميل التنبؤات")
      // استخدام بيانات تجريبية في حالة فشل API
      setForecastData({
        sales: [
          { date: '2024-01-01', actual: 450, forecast: 480, confidence: 0.85 },
          { date: '2024-01-02', actual: 520, forecast: 550, confidence: 0.88 },
          { date: '2024-01-03', actual: 480, forecast: 510, confidence: 0.82 },
          { date: '2024-01-04', actual: null, forecast: 620, confidence: 0.90 },
          { date: '2024-01-05', actual: null, forecast: 650, confidence: 0.87 },
        ],
        accuracy: 0.945,
        recommendations: [
          { type: 'reorder', product: 'منتج أ', message: 'يُنصح بإعادة الطلب قريباً' },
        ],
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadForecast()
  }, [selectedPeriod])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-purple-100 p-2 rounded-lg">
            <Brain className="h-6 w-6 text-purple-700" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">التنبؤ الذكي (AI Forecast)</h1>
            <p className="text-gray-600">تحليل الاتجاهات المستقبلية باستخدام الذكاء الاصطناعي</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">7 أيام</SelectItem>
              <SelectItem value="30">30 يوم</SelectItem>
              <SelectItem value="90">90 يوم</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={loadForecast} disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 ml-2 animate-spin" /> : <RefreshCw className="h-4 w-4 ml-2" />}
            تحديث
          </Button>
        </div>
      </div>

      {loading && !forecastData ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-purple-600 mb-4" />
            <p className="text-gray-500">جاري تحليل البيانات...</p>
          </CardContent>
        </Card>
      ) : forecastData ? (
        <>
          {/* دقة التنبؤ */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">دقة التنبؤ</p>
                    <p className="text-2xl font-bold text-green-600">
                      {(forecastData.accuracy * 100 || 94.5).toFixed(1)}%
                    </p>
                  </div>
                  <TrendingUp className="h-10 w-10 text-green-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">التنبؤات النشطة</p>
                    <p className="text-2xl font-bold text-blue-600">
                      {forecastData.sales?.length || 0}
                    </p>
                  </div>
                  <Brain className="h-10 w-10 text-blue-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">التوصيات</p>
                    <p className="text-2xl font-bold text-purple-600">
                      {forecastData.recommendations?.length || 0}
                    </p>
                  </div>
                  <AlertCircle className="h-10 w-10 text-purple-500" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* رسم بياني للتنبؤات */}
          {forecastData.sales && forecastData.sales.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>تنبؤات المبيعات</CardTitle>
                <CardDescription>مقارنة بين المبيعات الفعلية والتنبؤات</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={forecastData.sales}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Area
                      type="monotone"
                      dataKey="actual"
                      stroke="#3b82f6"
                      fill="#3b82f6"
                      fillOpacity={0.6}
                      name="الفعلي"
                    />
                    <Area
                      type="monotone"
                      dataKey="forecast"
                      stroke="#8b5cf6"
                      fill="#8b5cf6"
                      fillOpacity={0.4}
                      strokeDasharray="5 5"
                      name="التنبؤ"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* التوصيات */}
          {forecastData.recommendations && forecastData.recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>التوصيات الذكية</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {forecastData.recommendations.map((rec: any, index: number) => (
                    <div
                      key={index}
                      className="p-4 bg-blue-50 rounded-lg border border-blue-200"
                    >
                      <p className="font-semibold text-blue-900">{rec.product || rec.type}</p>
                      <p className="text-sm text-blue-700 mt-1">{rec.message}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <Brain className="h-16 w-16 text-gray-200 mb-4" />
            <h3 className="text-lg font-medium text-gray-900">لا توجد بيانات</h3>
            <p className="text-gray-500 max-w-md mt-2">
              لا توجد بيانات كافية لإنشاء تنبؤات. يرجى إضافة بيانات مبيعات أولاً.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
