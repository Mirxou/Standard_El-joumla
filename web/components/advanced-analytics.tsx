"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { BarChart3, TrendingUp, DollarSign, Package, Download, Loader2 } from 'lucide-react'
import { getSalesAnalytics, getInventoryAnalytics } from "@/lib/actions/dashboard"

export default function AdvancedAnalytics() {
  const [period, setPeriod] = useState<'week' | 'month' | 'year'>('month')
  const [salesData, setSalesData] = useState<any>(null)
  const [inventoryData, setInventoryData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  const loadAnalytics = async () => {
    setLoading(true)
    try {
      const [sales, inventory] = await Promise.all([
        getSalesAnalytics(period),
        getInventoryAnalytics()
      ])
      setSalesData(sales)
      setInventoryData(inventory)
    } catch (error) {
      console.error('[v0] Error loading analytics:', error)
    }
    setLoading(false)
  }

  useEffect(() => {
    loadAnalytics()
  }, [period])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">التحليلات المتقدمة</h2>
          <p className="text-sm text-gray-600">تقارير مفصلة عن الأداء والمبيعات</p>
        </div>
        <div className="flex gap-3">
          <Select value={period} onValueChange={(val: any) => setPeriod(val)}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="week">أسبوع</SelectItem>
              <SelectItem value="month">شهر</SelectItem>
              <SelectItem value="year">سنة</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" className="gap-2">
            <Download className="h-4 w-4" />
            تصدير PDF
          </Button>
        </div>
      </div>

      <Tabs defaultValue="sales" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="sales">تحليل المبيعات</TabsTrigger>
          <TabsTrigger value="inventory">تحليل المخزون</TabsTrigger>
          <TabsTrigger value="profit">تحليل الأرباح</TabsTrigger>
        </TabsList>

        <TabsContent value="sales" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  إجمالي المبيعات
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">
                  {salesData?.salesByDay?.reduce((sum: number, d: any) => sum + Number(d.total_sales || 0), 0).toLocaleString('en-US')} ر.س
                </p>
                <p className="text-sm text-green-600 mt-1">+18% من الفترة السابقة</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  عدد الفواتير
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">
                  {salesData?.salesByDay?.reduce((sum: number, d: any) => sum + Number(d.invoice_count || 0), 0)}
                </p>
                <p className="text-sm text-blue-600 mt-1">+12% من الفترة السابقة</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  متوسط الفاتورة
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">
                  {salesData?.salesByDay?.length > 0 
                    ? Math.round(
                        salesData.salesByDay.reduce((sum: number, d: any) => sum + Number(d.total_sales || 0), 0) /
                        salesData.salesByDay.reduce((sum: number, d: any) => sum + Number(d.invoice_count || 0), 0)
                      ).toLocaleString('en-US')
                    : 0} ر.س
                </p>
                <p className="text-sm text-purple-600 mt-1">+5% من الفترة السابقة</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>المبيعات حسب الفئة</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {salesData?.salesByCategory?.map((cat: any, index: number) => (
                  <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <p className="font-semibold">{cat.category}</p>
                      <p className="text-sm text-gray-600">{cat.invoice_count} فاتورة</p>
                    </div>
                    <div className="text-left">
                              <p className="text-lg font-bold text-green-600">{Number(cat.total_sales).toLocaleString('en-US')} ر.س</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="inventory" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">قيمة المخزون الإجمالية</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold text-blue-600">
                  {Number(inventoryData?.stockValue?.total_value || 0).toLocaleString('en-US')} ر.س
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">التكلفة الإجمالية</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold text-orange-600">
                  {Number(inventoryData?.stockValue?.total_cost || 0).toLocaleString('en-US')} ر.س
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">عدد المنتجات</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold text-purple-600">
                  {inventoryData?.stockValue?.total_products || 0}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">تنبيهات المخزون</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold text-red-600">
                  {inventoryData?.stockValue?.low_stock_count || 0}
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>توزيع المخزون حسب الفئة</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {inventoryData?.categoryDistribution?.map((cat: any, index: number) => (
                  <div key={index} className="p-4 bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg border">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold">{cat.category}</h3>
                      <Badge>{cat.product_count} منتج</Badge>
                    </div>
                    <p className="text-sm text-gray-600">{Number(cat.total_quantity).toLocaleString('en-US')} وحدة</p>
                    <p className="text-lg font-bold text-blue-600 mt-1">
                      {Number(cat.total_value).toLocaleString()} ر.س
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="profit" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>هوامش الربح حسب المنتج</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {salesData?.profitMargins?.map((prod: any, index: number) => (
                  <div key={index} className="p-4 bg-gradient-to-r from-green-50 to-green-100 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-gray-900">{prod.product}</h3>
                      <Badge className="bg-green-600 text-white">
                        {prod.profit_margin}% هامش ربح
                      </Badge>
                    </div>
                    <div className="grid grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-gray-600">الكمية</p>
                        <p className="font-bold">{prod.quantity_sold}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">الإيرادات</p>
                        <p className="font-bold text-blue-600">{Number(prod.revenue).toLocaleString()} ر.س</p>
                      </div>
                      <div>
                        <p className="text-gray-600">التكلفة</p>
                        <p className="font-bold text-orange-600">{Number(prod.cost).toLocaleString()} ر.س</p>
                      </div>
                      <div>
                        <p className="text-gray-600">الربح</p>
                        <p className="font-bold text-green-600">{Number(prod.profit).toLocaleString()} ر.س</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
