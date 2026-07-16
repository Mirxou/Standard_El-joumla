"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Users,
  Package,
  ShoppingCart,
  DollarSign,
  Calendar,
  Clock,
  AlertCircle,
  CheckCircle,
  XCircle,
} from "lucide-react"
import { LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts"

export default function ActivityLog() {
  const [selectedPeriod, setSelectedPeriod] = useState("today")

  const salesData = [
    { time: "08:00", amount: 1200 },
    { time: "10:00", amount: 2400 },
    { time: "12:00", amount: 3800 },
    { time: "14:00", amount: 2900 },
    { time: "16:00", amount: 4200 },
    { time: "18:00", amount: 3100 },
  ]

  const userActivityData = [
    { user: "أحمد", actions: 45 },
    { user: "فاطمة", actions: 38 },
    { user: "خالد", actions: 32 },
    { user: "نورا", actions: 28 },
  ]

  const activityTypeData = [
    { name: "مبيعات", value: 145, color: "#10b981" },
    { name: "مخزون", value: 89, color: "#3b82f6" },
    { name: "تقارير", value: 67, color: "#f59e0b" },
    { name: "إعدادات", value: 34, color: "#8b5cf6" },
  ]

  const recentActivities = [
    {
      id: 1,
      type: "sale",
      user: "أحمد محمد",
      action: "إنشاء فاتورة جديدة",
      details: "فاتورة #INV-2024-1523 بقيمة 2,450 ر.س",
      time: "منذ دقيقتين",
      status: "success",
    },
    {
      id: 2,
      type: "inventory",
      user: "خالد عبدالله",
      action: "تحديث مخزون منتج",
      details: "تحديث كمية منتج #PRD-458 من 50 إلى 120 قطعة",
      time: "منذ 5 دقائق",
      status: "success",
    },
    {
      id: 3,
      type: "report",
      user: "فاطمة سالم",
      action: "تصدير تقرير المبيعات",
      details: "تقرير المبيعات الشهري - أكتوبر 2024",
      time: "منذ 12 دقيقة",
      status: "success",
    },
    {
      id: 4,
      type: "user",
      user: "نورا أحمد",
      action: "محاولة تسجيل دخول فاشلة",
      details: "كلمة مرور غير صحيحة",
      time: "منذ 15 دقيقة",
      status: "error",
    },
    {
      id: 5,
      type: "inventory",
      user: "خالد عبدالله",
      action: "تنبيه مخزون منخفض",
      details: "منتج #PRD-125 وصل للحد الأدنى (5 قطع)",
      time: "منذ 18 دقيقة",
      status: "warning",
    },
    {
      id: 6,
      type: "sale",
      user: "أحمد محمد",
      action: "إنشاء فاتورة جديدة",
      details: "فاتورة #INV-2024-1522 بقيمة 3,780 ر.س",
      time: "منذ 25 دقيقة",
      status: "success",
    },
    {
      id: 7,
      type: "settings",
      user: "أحمد محمد",
      action: "تحديث إعدادات النظام",
      details: "تغيير إعدادات التنبيهات",
      time: "منذ 30 دقيقة",
      status: "success",
    },
    {
      id: 8,
      type: "inventory",
      user: "خالد عبدالله",
      action: "إضافة منتج جديد",
      details: "منتج #PRD-890 - لابتوب HP",
      time: "منذ ساعة",
      status: "success",
    },
  ]

  const getActivityIcon = (type: string) => {
    switch (type) {
      case "sale":
        return <ShoppingCart className="h-5 w-5 text-green-600" />
      case "inventory":
        return <Package className="h-5 w-5 text-blue-600" />
      case "report":
        return <Activity className="h-5 w-5 text-orange-600" />
      case "user":
        return <Users className="h-5 w-5 text-purple-600" />
      case "settings":
        return <AlertCircle className="h-5 w-5 text-gray-600" />
      default:
        return <Activity className="h-5 w-5 text-gray-600" />
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "error":
        return <XCircle className="h-4 w-4 text-red-600" />
      case "warning":
        return <AlertCircle className="h-4 w-4 text-orange-600" />
      default:
        return <CheckCircle className="h-4 w-4 text-gray-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "success":
        return "bg-green-100 text-green-800"
      case "error":
        return "bg-red-100 text-red-800"
      case "warning":
        return "bg-orange-100 text-orange-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">سجل النشاطات</h1>
          <p className="text-gray-600">مراقبة جميع الأنشطة والعمليات في النظام</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={selectedPeriod === "today" ? "default" : "outline"}
            onClick={() => setSelectedPeriod("today")}
          >
            اليوم
          </Button>
          <Button
            variant={selectedPeriod === "week" ? "default" : "outline"}
            onClick={() => setSelectedPeriod("week")}
          >
            الأسبوع
          </Button>
          <Button
            variant={selectedPeriod === "month" ? "default" : "outline"}
            onClick={() => setSelectedPeriod("month")}
          >
            الشهر
          </Button>
        </div>
      </div>

      {/* إحصائيات */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">إجمالي النشاطات</p>
                <p className="text-2xl font-bold text-blue-600">335</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="h-3 w-3 text-green-600" />
                  <span className="text-xs text-green-600">+12%</span>
                </div>
              </div>
              <div className="bg-blue-100 p-3 rounded-lg">
                <Activity className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">عمليات ناجحة</p>
                <p className="text-2xl font-bold text-green-600">289</p>
                <div className="flex items-center gap-1 mt-1">
                  <span className="text-xs text-gray-600">86.3%</span>
                </div>
              </div>
              <div className="bg-green-100 p-3 rounded-lg">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">تحذيرات</p>
                <p className="text-2xl font-bold text-orange-600">34</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingDown className="h-3 w-3 text-green-600" />
                  <span className="text-xs text-green-600">-5%</span>
                </div>
              </div>
              <div className="bg-orange-100 p-3 rounded-lg">
                <AlertCircle className="h-6 w-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">أخطاء</p>
                <p className="text-2xl font-bold text-red-600">12</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingDown className="h-3 w-3 text-green-600" />
                  <span className="text-xs text-green-600">-8%</span>
                </div>
              </div>
              <div className="bg-red-100 p-3 rounded-lg">
                <XCircle className="h-6 w-6 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* الرسوم البيانية */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">نشاط المبيعات اليومي</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={salesData}>
                <defs>
                  <linearGradient id="colorAmount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Area type="monotone" dataKey="amount" stroke="#10b981" fill="url(#colorAmount)" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">نشاط المستخدمين</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={userActivityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="user" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="actions" fill="#3b82f6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* توزيع الأنشطة */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">توزيع أنواع النشاطات</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={activityTypeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry: any) => entry.name}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {activityTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="col-span-2">
          <CardHeader>
            <CardTitle className="text-base">أداء النظام</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">نسبة النجاح</span>
                <span className="font-semibold text-green-600">86.3%</span>
              </div>
              <Progress value={86.3} className="h-2" />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">استخدام النظام</span>
                <span className="font-semibold text-blue-600">72.5%</span>
              </div>
              <Progress value={72.5} className="h-2" />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">سرعة الاستجابة</span>
                <span className="font-semibold text-purple-600">94.8%</span>
              </div>
              <Progress value={94.8} className="h-2" />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">الأمان والحماية</span>
                <span className="font-semibold text-orange-600">98.2%</span>
              </div>
              <Progress value={98.2} className="h-2" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* قائمة النشاطات */}
      <Card>
        <CardHeader>
          <CardTitle>آخر النشاطات</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recentActivities.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start gap-4 p-4 border rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="flex-shrink-0 mt-1">{getActivityIcon(activity.type)}</div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-semibold text-gray-900">{activity.action}</h4>
                    {getStatusIcon(activity.status)}
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{activity.details}</p>
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Users className="h-3 w-3" />
                      {activity.user}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {activity.time}
                    </span>
                  </div>
                </div>
                <Badge className={getStatusColor(activity.status)}>
                  {activity.status === "success" && "نجح"}
                  {activity.status === "error" && "فشل"}
                  {activity.status === "warning" && "تحذير"}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
