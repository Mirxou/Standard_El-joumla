"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Progress } from "@/components/ui/progress"
import { TrendingUp, TrendingDown, DollarSign, BarChart3, Target, Download } from "lucide-react"

export default function ProfitReports() {
  const [selectedPeriod, setSelectedPeriod] = useState("month")
  const [selectedCategory, setSelectedCategory] = useState("all")

  const profitData = {
    totalRevenue: 245800,
    totalCost: 147480,
    totalProfit: 98320,
    profitMargin: 40.0,
    previousPeriodProfit: 89650,
    profitGrowth: 9.7,
  }

  const categoryProfits = [
    {
      name: "المواد الغذائية",
      revenue: 89500,
      cost: 53700,
      profit: 35800,
      margin: 40.0,
      growth: 12.5,
      color: "bg-green-500",
    },
    {
      name: "صحة وجمال",
      revenue: 67200,
      cost: 40320,
      profit: 26880,
      margin: 40.0,
      growth: 8.3,
      color: "bg-blue-500",
    },
    {
      name: "إلكترونيات",
      revenue: 45600,
      cost: 27360,
      profit: 18240,
      margin: 40.0,
      growth: 15.2,
      color: "bg-purple-500",
    },
    {
      name: "منتجات النظافة",
      revenue: 28900,
      cost: 17340,
      profit: 11560,
      margin: 40.0,
      growth: 5.7,
      color: "bg-orange-500",
    },
    {
      name: "حلويات ومأكولات",
      revenue: 14600,
      cost: 8760,
      profit: 5840,
      margin: 40.0,
      growth: 22.1,
      color: "bg-pink-500",
    },
  ]

  const topProducts = [
    {
      name: "زيت الزيتون البكر",
      revenue: 12250,
      profit: 4900,
      margin: 40.0,
      units: 245,
      trend: "up",
    },
    {
      name: "سماعات بلوتوث",
      revenue: 8990,
      profit: 3596,
      margin: 40.0,
      units: 156,
      trend: "up",
    },
    {
      name: "شامبو الأطفال",
      revenue: 7650,
      profit: 3060,
      margin: 40.0,
      units: 189,
      trend: "down",
    },
    {
      name: "شوكولاتة فاخرة",
      revenue: 6700,
      profit: 2680,
      margin: 40.0,
      units: 134,
      trend: "up",
    },
  ]

  const monthlyData = [
    { month: "يناير", revenue: 185000, profit: 74000 },
    { month: "فبراير", revenue: 223000, profit: 89200 },
    { month: "مارس", revenue: 245800, profit: 98320 },
    { month: "أبريل", revenue: 212000, profit: 84800 },
    { month: "مايو", revenue: 268000, profit: 107200 },
    { month: "يونيو", revenue: 245800, profit: 98320 },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">تقارير الأرباح</h1>
          <p className="text-gray-600">تحليل شامل للربحية والأداء المالي مع إحصائيات مفصلة</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="day">اليوم</SelectItem>
              <SelectItem value="week">الأسبوع</SelectItem>
              <SelectItem value="month">الشهر</SelectItem>
              <SelectItem value="quarter">الربع</SelectItem>
              <SelectItem value="year">السنة</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline">
            <Download className="h-4 w-4 ml-2" />
            تصدير
          </Button>
        </div>
      </div>

      {/* المؤشرات الرئيسية */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">إجمالي الإيرادات</p>
                <p className="text-2xl font-bold text-green-600">{profitData.totalRevenue.toLocaleString('en-US')} ر.س</p>
              </div>
              <div className="bg-green-100 p-2 rounded-lg">
                <DollarSign className="h-5 w-5 text-green-600" />
              </div>
            </div>
            <div className="flex items-center mt-2">
              <TrendingUp className="h-3 w-3 text-green-500 ml-1" />
              <span className="text-xs text-green-500">+12.5% من الشهر الماضي</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">إجمالي الأرباح</p>
                <p className="text-2xl font-bold text-blue-600">{profitData.totalProfit.toLocaleString('en-US')} ر.س</p>
              </div>
              <div className="bg-blue-100 p-2 rounded-lg">
                <Target className="h-5 w-5 text-blue-600" />
              </div>
            </div>
            <div className="flex items-center mt-2">
              <TrendingUp className="h-3 w-3 text-green-500 ml-1" />
              <span className="text-xs text-green-500">+{profitData.profitGrowth}% من الشهر الماضي</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">هامش الربح</p>
                <p className="text-2xl font-bold text-purple-600">{profitData.profitMargin}%</p>
              </div>
              <div className="bg-purple-100 p-2 rounded-lg">
                <BarChart3 className="h-5 w-5 text-purple-600" />
              </div>
            </div>
            <div className="flex items-center mt-2">
              <TrendingUp className="h-3 w-3 text-green-500 ml-1" />
              <span className="text-xs text-green-500">+2.1% من الشهر الماضي</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">إجمالي التكلفة</p>
                <p className="text-2xl font-bold text-orange-600">{profitData.totalCost.toLocaleString('en-US')} ر.س</p>
              </div>
              <div className="bg-orange-100 p-2 rounded-lg">
                <TrendingDown className="h-5 w-5 text-orange-600" />
              </div>
            </div>
            <div className="flex items-center mt-2">
              <TrendingDown className="h-3 w-3 text-green-500 ml-1" />
              <span className="text-xs text-green-500">-3.2% من الشهر الماضي</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* الأداء الشهري */}
      <Card>
        <CardHeader>
          <CardTitle>الأداء الشهري</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {monthlyData.map((data, index) => (
              <div key={data.month} className="flex items-center justify-between">
                <div className="flex items-center gap-4 flex-1">
                  <div className="w-16 text-sm font-medium text-gray-600">{data.month}</div>
                  <div className="flex-1">
                    <div className="flex justify-between text-sm mb-1">
                      <span>الإيرادات: {data.revenue.toLocaleString('en-US')} ر.س</span>
                      <span>الأرباح: {data.profit.toLocaleString('en-US')} ر.س</span>
                    </div>
                    <Progress value={(data.profit / data.revenue) * 100} className="h-3" />
                  </div>
                </div>
                <div className="text-left">
                  <p className="text-sm font-medium">{((data.profit / data.revenue) * 100).toFixed(1)}%</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* الربحية حسب الفئات */}
      <Card>
        <CardHeader>
          <CardTitle>الربحية حسب الفئات</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {categoryProfits.map((category, index) => (
              <div key={category.name} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-4 h-4 rounded ${category.color}`}></div>
                    <h3 className="font-medium text-gray-900">{category.name}</h3>
                  </div>
                  <div className="text-left">
                    <p className="font-semibold text-lg">{category.profit.toLocaleString('en-US')} ر.س</p>
                    <p className="text-sm text-gray-500">{category.margin}% هامش ربح</p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 mb-3">
                  <div>
                    <p className="text-xs text-gray-500">الإيرادات</p>
                    <p className="font-medium">{category.revenue.toLocaleString('en-US')} ر.س</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">التكلفة</p>
                    <p className="font-medium">{category.cost.toLocaleString('en-US')} ر.س</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">النمو</p>
                    <div className="flex items-center gap-1">
                      <TrendingUp className="h-3 w-3 text-green-500" />
                      <span className="text-sm text-green-500">+{category.growth}%</span>
                    </div>
                  </div>
                </div>

                <Progress value={category.margin} className="h-2" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* المنتجات الأكثر ربحية */}
      <Card>
        <CardHeader>
          <CardTitle>المنتجات الأكثر ربحية</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {topProducts.map((product, index) => (
              <div key={product.name} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-sm font-bold text-blue-600">#{index + 1}</span>
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">{product.name}</h3>
                    <p className="text-sm text-gray-500">{product.units} قطعة مباعة</p>
                  </div>
                </div>

                <div className="text-left">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-lg font-semibold">{product.profit.toLocaleString('en-US')} ر.س</span>
                    {product.trend === "up" ? (
                      <TrendingUp className="h-4 w-4 text-green-500" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-red-500" />
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      {product.margin}% هامش ربح
                    </Badge>
                    <span className="text-sm text-gray-500">{product.revenue.toLocaleString('en-US')} ر.س إيرادات</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* أهداف الربح */}
      <Card>
        <CardHeader>
          <CardTitle>أهداف الربح الشهرية</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>هدف الإيرادات</span>
                <span>{profitData.totalRevenue.toLocaleString('en-US')} / 300,000 ر.س</span>
              </div>
              <Progress value={(profitData.totalRevenue / 300000) * 100} className="h-3" />
              <p className="text-xs text-gray-500 mt-1">
                {((profitData.totalRevenue / 300000) * 100).toFixed(1)}% من الهدف الشهري
              </p>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>هدف الأرباح</span>
                <span>{profitData.totalProfit.toLocaleString('en-US')} / 120,000 ر.س</span>
              </div>
              <Progress value={(profitData.totalProfit / 120000) * 100} className="h-3" />
              <p className="text-xs text-gray-500 mt-1">
                {((profitData.totalProfit / 120000) * 100).toFixed(1)}% من الهدف الشهري
              </p>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>هدف هامش الربح</span>
                <span>{profitData.profitMargin}% / 45%</span>
              </div>
              <Progress value={(profitData.profitMargin / 45) * 100} className="h-3" />
              <p className="text-xs text-gray-500 mt-1">
                {((profitData.profitMargin / 45) * 100).toFixed(1)}% من الهدف المطلوب
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
