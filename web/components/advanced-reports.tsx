"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Progress } from "@/components/ui/progress"
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Download,
  Printer,
  FileText,
  Calendar,
  Filter,
  Eye,
  Share2,
  PieChart,
  LineChart,
  Activity,
} from "lucide-react"

export default function AdvancedReports() {
  const [selectedPeriod, setSelectedPeriod] = useState("month")
  const [selectedReport, setSelectedReport] = useState("comprehensive")

  const reportData = {
    comprehensive: {
      title: "التقرير الشامل",
      description: "تحليل شامل لجميع جوانب العمل",
      metrics: [
        { name: "إجمالي الإيرادات", value: "2,458,000 ر.س", change: "+12.5%", trend: "up" },
        { name: "صافي الأرباح", value: "983,200 ر.س", change: "+8.3%", trend: "up" },
        { name: "هامش الربح", value: "40.0%", change: "+2.1%", trend: "up" },
        { name: "عدد الطلبات", value: "1,247", change: "+15.2%", trend: "up" },
      ],
    },
    inventory: {
      title: "تقرير المخزون المتقدم",
      description: "تحليل مفصل لحالة المخزون والحركة",
      metrics: [
        { name: "قيمة المخزون", value: "1,250,000 ر.س", change: "+5.7%", trend: "up" },
        { name: "معدل دوران المخزون", value: "4.2x", change: "+0.3", trend: "up" },
        { name: "المنتجات النشطة", value: "1,247", change: "+23", trend: "up" },
        { name: "المنتجات البطيئة", value: "45", change: "-8", trend: "down" },
      ],
    },
    sales: {
      title: "تقرير المبيعات التفصيلي",
      description: "تحليل شامل لأداء المبيعات والعملاء",
      metrics: [
        { name: "مبيعات الشهر", value: "456,800 ر.س", change: "+18.2%", trend: "up" },
        { name: "متوسط قيمة الطلب", value: "367 ر.س", change: "+12.1%", trend: "up" },
        { name: "عدد العملاء الجدد", value: "89", change: "+25", trend: "up" },
        { name: "معدل العائدات", value: "2.3%", change: "-0.5%", trend: "down" },
      ],
    },
    suppliers: {
      title: "تقرير أداء الموردين",
      description: "تقييم شامل لأداء الموردين والتوريد",
      metrics: [
        { name: "عدد الموردين النشطين", value: "45", change: "+3", trend: "up" },
        { name: "متوسط وقت التسليم", value: "3.2 يوم", change: "-0.5", trend: "down" },
        { name: "معدل الجودة", value: "94.5%", change: "+2.1%", trend: "up" },
        { name: "توفير التكلفة", value: "8.7%", change: "+1.2%", trend: "up" },
      ],
    },
  }

  const categoryPerformance = [
    { name: "المواد الغذائية", revenue: 895000, profit: 358000, margin: 40.0, growth: 12.5 },
    { name: "صحة وجمال", revenue: 672000, profit: 268800, margin: 40.0, growth: 8.3 },
    { name: "الإلكترونيات", revenue: 456000, profit: 182400, margin: 40.0, growth: 15.2 },
    { name: "منتجات النظافة", revenue: 289000, profit: 115600, margin: 40.0, growth: 5.7 },
    { name: "الحلويات", revenue: 146000, profit: 58400, margin: 40.0, growth: 22.1 },
  ]

  const monthlyTrends = [
    { month: "يناير", sales: 385000, profit: 154000, orders: 1156 },
    { month: "فبراير", sales: 423000, profit: 169200, orders: 1289 },
    { month: "مارس", sales: 456800, profit: 182720, orders: 1347 },
    { month: "أبريل", sales: 398000, profit: 159200, orders: 1198 },
    { month: "مايو", sales: 512000, profit: 204800, orders: 1456 },
    { month: "يونيو", sales: 456800, profit: 182720, orders: 1347 },
  ]

  const currentReport = reportData[selectedReport as keyof typeof reportData]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">التقارير والإحصائيات المتقدمة</h1>
          <p className="text-gray-600">تحليلات شاملة ومرئية لجميع جوانب العمل مع إمكانية التصدير</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Share2 className="h-4 w-4 ml-2" />
            مشاركة
          </Button>
          <Button variant="outline">
            <Printer className="h-4 w-4 ml-2" />
            طباعة
          </Button>
          <Button className="bg-green-600 hover:bg-green-700">
            <Download className="h-4 w-4 ml-2" />
            تصدير Excel
          </Button>
        </div>
      </div>

      {/* فلاتر التقارير */}
      <div className="flex flex-col md:flex-row gap-4">
        <Select value={selectedReport} onValueChange={setSelectedReport}>
          <SelectTrigger className="w-full md:w-64">
            <SelectValue placeholder="نوع التقرير" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="comprehensive">التقرير الشامل</SelectItem>
            <SelectItem value="inventory">تقرير المخزون</SelectItem>
            <SelectItem value="sales">تقرير المبيعات</SelectItem>
            <SelectItem value="suppliers">تقرير الموردين</SelectItem>
          </SelectContent>
        </Select>

        <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
          <SelectTrigger className="w-full md:w-32">
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
          <Filter className="h-4 w-4 ml-2" />
          فلاتر متقدمة
        </Button>
      </div>

      {/* عنوان التقرير الحالي */}
      <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl text-blue-900">{currentReport.title}</CardTitle>
              <p className="text-blue-700 mt-1">{currentReport.description}</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge className="bg-blue-100 text-blue-800">
                <Calendar className="h-3 w-3 ml-1" />
                {selectedPeriod === "month" ? "شهري" : selectedPeriod === "week" ? "أسبوعي" : "يومي"}
              </Badge>
              <Badge className="bg-green-100 text-green-800">
                <Activity className="h-3 w-3 ml-1" />
                مباشر
              </Badge>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* المؤشرات الرئيسية للتقرير */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {currentReport.metrics.map((metric, index) => (
          <Card key={index} className="hover:shadow-lg transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 font-medium">{metric.name}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{metric.value}</p>
                </div>
                <div className={`p-3 rounded-xl ${metric.trend === "up" ? "bg-green-100" : "bg-red-100"}`}>
                  {metric.trend === "up" ? (
                    <TrendingUp className="h-6 w-6 text-green-600" />
                  ) : (
                    <TrendingDown className="h-6 w-6 text-red-600" />
                  )}
                </div>
              </div>
              <div className="flex items-center mt-3">
                {metric.trend === "up" ? (
                  <TrendingUp className="h-4 w-4 text-green-500 ml-1" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-500 ml-1" />
                )}
                <span className={`text-sm font-medium ${metric.trend === "up" ? "text-green-600" : "text-red-600"}`}>
                  {metric.change}
                </span>
                <span className="text-sm text-gray-500 mr-1">من الفترة السابقة</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* الاتجاهات الشهرية */}
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <LineChart className="h-5 w-5 text-blue-600" />
            الاتجاهات الشهرية
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {monthlyTrends.map((trend, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-4 flex-1">
                  <div className="w-16 text-sm font-medium text-gray-700">{trend.month}</div>
                  <div className="flex-1">
                    <div className="grid grid-cols-3 gap-4 text-sm mb-2">
                      <span>المبيعات: {trend.sales.toLocaleString('en-US')} ر.س</span>
                      <span>الأرباح: {trend.profit.toLocaleString('en-US')} ر.س</span>
                      <span>الطلبات: {trend.orders}</span>
                    </div>
                    <Progress value={(trend.profit / trend.sales) * 100} className="h-3" />
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{((trend.profit / trend.sales) * 100).toFixed(1)}%</p>
                  <p className="text-xs text-gray-500">هامش الربح</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* أداء الفئات */}
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PieChart className="h-5 w-5 text-purple-600" />
            أداء الفئات التفصيلي
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {categoryPerformance.map((category, index) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-4 h-4 rounded bg-gradient-to-r ${
                        index === 0
                          ? "from-green-400 to-green-600"
                          : index === 1
                            ? "from-blue-400 to-blue-600"
                            : index === 2
                              ? "from-purple-400 to-purple-600"
                              : index === 3
                                ? "from-orange-400 to-orange-600"
                                : "from-pink-400 to-pink-600"
                      }`}
                    ></div>
                    <h3 className="font-semibold text-gray-900">{category.name}</h3>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-lg">{category.profit.toLocaleString('en-US')} ر.س</p>
                    <p className="text-sm text-gray-500">{category.margin}% هامش ربح</p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 mb-3">
                  <div>
                    <p className="text-xs text-gray-500">الإيرادات</p>
                    <p className="font-semibold">{category.revenue.toLocaleString('en-US')} ر.س</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">النمو</p>
                    <div className="flex items-center gap-1">
                      <TrendingUp className="h-3 w-3 text-green-500" />
                      <span className="text-sm text-green-600 font-medium">+{category.growth}%</span>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">الحصة السوقية</p>
                    <p className="font-semibold">
                      {((category.revenue / categoryPerformance.reduce((sum, c) => sum + c.revenue, 0)) * 100).toFixed(
                        1,
                      )}
                      %
                    </p>
                  </div>
                </div>

                <Progress value={category.margin} className="h-2" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* تقارير قابلة للتخصيص */}
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-indigo-600" />
            تقارير قابلة للتخصيص
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="p-4 border rounded-lg hover:shadow-md transition-shadow cursor-pointer">
              <div className="flex items-center gap-3 mb-3">
                <div className="bg-blue-100 p-2 rounded-lg">
                  <FileText className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold">تقرير المبيعات اليومي</h3>
                  <p className="text-sm text-gray-500">تحديث تلقائي كل ساعة</p>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <Badge className="bg-green-100 text-green-800">جاهز</Badge>
                <Button size="sm" variant="outline">
                  <Eye className="h-4 w-4 ml-1" />
                  عرض
                </Button>
              </div>
            </div>

            <div className="p-4 border rounded-lg hover:shadow-md transition-shadow cursor-pointer">
              <div className="flex items-center gap-3 mb-3">
                <div className="bg-purple-100 p-2 rounded-lg">
                  <BarChart3 className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-semibold">تحليل الربحية</h3>
                  <p className="text-sm text-gray-500">تحديث أسبوعي</p>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <Badge className="bg-orange-100 text-orange-800">قيد المعالجة</Badge>
                <Button size="sm" variant="outline">
                  <Eye className="h-4 w-4 ml-1" />
                  عرض
                </Button>
              </div>
            </div>

            <div className="p-4 border rounded-lg hover:shadow-md transition-shadow cursor-pointer">
              <div className="flex items-center gap-3 mb-3">
                <div className="bg-green-100 p-2 rounded-lg">
                  <TrendingUp className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <h3 className="font-semibold">تقرير الأداء الشامل</h3>
                  <p className="text-sm text-gray-500">تحديث شهري</p>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <Badge className="bg-blue-100 text-blue-800">مجدول</Badge>
                <Button size="sm" variant="outline">
                  <Eye className="h-4 w-4 ml-1" />
                  عرض
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* خيارات التصدير المتقدمة */}
      <Card className="shadow-lg bg-gradient-to-r from-gray-50 to-blue-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="h-5 w-5 text-blue-600" />
            خيارات التصدير المتقدمة
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button className="h-16 flex-col gap-2 bg-green-600 hover:bg-green-700">
              <FileText className="h-6 w-6" />
              <span className="text-sm">تصدير PDF</span>
            </Button>
            <Button className="h-16 flex-col gap-2 bg-blue-600 hover:bg-blue-700">
              <BarChart3 className="h-6 w-6" />
              <span className="text-sm">تصدير Excel</span>
            </Button>
            <Button className="h-16 flex-col gap-2 bg-purple-600 hover:bg-purple-700">
              <Share2 className="h-6 w-6" />
              <span className="text-sm">مشاركة التقرير</span>
            </Button>
            <Button className="h-16 flex-col gap-2 bg-orange-600 hover:bg-orange-700">
              <Printer className="h-6 w-6" />
              <span className="text-sm">طباعة مباشرة</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
