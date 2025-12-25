"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Calendar, AlertTriangle, Clock, Package, Search, Filter, Bell, Trash2, RefreshCw } from "lucide-react"

export default function ExpiryTracking() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedStatus, setSelectedStatus] = useState("all")

  const expiryItems = [
    {
      id: 1,
      name: "زيت الزيتون البكر الممتاز",
      category: "مواد غذائية",
      sku: "FOOD-001",
      batch: "LOT-2024-001",
      expiryDate: "2024-02-15",
      daysLeft: 15,
      quantity: 45,
      warehouse: "المستودع الرئيسي",
      supplier: "شركة الزيوت المتميزة",
      status: "قريب الانتهاء",
      alertLevel: "تحذير",
    },
    {
      id: 2,
      name: "شامبو الأطفال اللطيف",
      category: "صحة وجمال",
      sku: "HEALTH-002",
      batch: "LOT-2024-002",
      expiryDate: "2024-01-25",
      daysLeft: 5,
      quantity: 12,
      warehouse: "مستودع الصحة",
      supplier: "مختبرات العناية",
      status: "منتهي الصلاحية قريباً",
      alertLevel: "حرج",
    },
    {
      id: 3,
      name: "شوكولاتة فاخرة بالبندق",
      category: "حلويات ومأكولات",
      sku: "SWEET-004",
      batch: "LOT-2024-003",
      expiryDate: "2024-01-22",
      daysLeft: 2,
      quantity: 67,
      warehouse: "مستودع الحلويات",
      supplier: "مصنع الحلويات الذهبية",
      status: "منتهي الصلاحية قريباً",
      alertLevel: "حرج",
    },
    {
      id: 4,
      name: "حليب الأطفال المدعم",
      category: "مواد غذائية",
      sku: "FOOD-005",
      batch: "LOT-2024-004",
      expiryDate: "2024-01-18",
      daysLeft: -2,
      quantity: 23,
      warehouse: "المستودع الرئيسي",
      supplier: "شركة منتجات الألبان",
      status: "منتهي الصلاحية",
      alertLevel: "منتهي",
    },
    {
      id: 5,
      name: "كريم الوجه المرطب",
      category: "صحة وجمال",
      sku: "HEALTH-006",
      batch: "LOT-2024-005",
      expiryDate: "2024-03-10",
      daysLeft: 50,
      quantity: 34,
      warehouse: "مستودع الصحة",
      supplier: "مختبرات العناية",
      status: "صالح",
      alertLevel: "عادي",
    },
    {
      id: 6,
      name: "عصير البرتقال الطبيعي",
      category: "مواد غذائية",
      sku: "FOOD-007",
      batch: "LOT-2024-006",
      expiryDate: "2024-02-01",
      daysLeft: 12,
      quantity: 89,
      warehouse: "المستودع الرئيسي",
      supplier: "مصنع العصائر الطبيعية",
      status: "قريب الانتهاء",
      alertLevel: "تحذير",
    },
  ]

  const getStatusColor = (alertLevel: string) => {
    switch (alertLevel) {
      case "منتهي":
        return "bg-red-100 text-red-800 border-red-200"
      case "حرج":
        return "bg-orange-100 text-orange-800 border-orange-200"
      case "تحذير":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "عادي":
        return "bg-green-100 text-green-800 border-green-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const getAlertIcon = (alertLevel: string) => {
    switch (alertLevel) {
      case "منتهي":
        return <Trash2 className="h-4 w-4 text-red-600" />
      case "حرج":
        return <AlertTriangle className="h-4 w-4 text-orange-600" />
      case "تحذير":
        return <Clock className="h-4 w-4 text-yellow-600" />
      default:
        return <Calendar className="h-4 w-4 text-green-600" />
    }
  }

  const getDaysLeftColor = (daysLeft: number) => {
    if (daysLeft < 0) return "text-red-600 font-bold"
    if (daysLeft <= 7) return "text-orange-600 font-bold"
    if (daysLeft <= 30) return "text-yellow-600 font-semibold"
    return "text-green-600"
  }

  const filteredItems = expiryItems.filter((item) => {
    const matchesSearch =
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.batch.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = selectedStatus === "all" || item.alertLevel === selectedStatus
    return matchesSearch && matchesStatus
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">تتبع انتهاء الصلاحية</h1>
          <p className="text-gray-600">مراقبة تواريخ انتهاء الصلاحية للمنتجات مع التنبيهات المبكرة</p>
        </div>
        <Button className="bg-orange-600 hover:bg-orange-700">
          <Bell className="h-4 w-4 ml-2" />
          إعداد التنبيهات
        </Button>
      </div>

      {/* البحث والفلترة */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder="البحث بالاسم، رمز المنتج، أو رقم الدفعة..."
            className="pr-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <Select value={selectedStatus} onValueChange={setSelectedStatus}>
          <SelectTrigger className="w-full md:w-48">
            <SelectValue placeholder="مستوى التنبيه" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">جميع المستويات</SelectItem>
            <SelectItem value="منتهي">منتهي الصلاحية</SelectItem>
            <SelectItem value="حرج">حرج</SelectItem>
            <SelectItem value="تحذير">تحذير</SelectItem>
            <SelectItem value="عادي">عادي</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="outline">
          <Filter className="h-4 w-4 ml-2" />
          فلاتر متقدمة
        </Button>
      </div>

      {/* ملخص التنبيهات */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">منتهي الصلاحية</p>
                <p className="text-2xl font-bold text-red-600">
                  {expiryItems.filter((item) => item.alertLevel === "منتهي").length}
                </p>
              </div>
              <div className="bg-red-100 p-2 rounded-lg">
                <Trash2 className="h-5 w-5 text-red-600" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">يتطلب إجراء فوري</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">حرج</p>
                <p className="text-2xl font-bold text-orange-600">
                  {expiryItems.filter((item) => item.alertLevel === "حرج").length}
                </p>
              </div>
              <div className="bg-orange-100 p-2 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-orange-600" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">أقل من أسبوع</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">تحذير</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {expiryItems.filter((item) => item.alertLevel === "تحذير").length}
                </p>
              </div>
              <div className="bg-yellow-100 p-2 rounded-lg">
                <Clock className="h-5 w-5 text-yellow-600" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">أقل من شهر</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">إجمالي المنتجات</p>
                <p className="text-2xl font-bold text-blue-600">{expiryItems.length}</p>
              </div>
              <div className="bg-blue-100 p-2 rounded-lg">
                <Package className="h-5 w-5 text-blue-600" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">تحت المراقبة</p>
          </CardContent>
        </Card>
      </div>

      {/* قائمة المنتجات */}
      <Card>
        <CardHeader>
          <CardTitle>المنتجات حسب تاريخ الانتهاء ({filteredItems.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredItems.map((item) => (
              <div key={item.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start gap-4 flex-1">
                    <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                      <Package className="h-6 w-6 text-gray-400" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg text-gray-900">{item.name}</h3>
                      <p className="text-sm text-gray-500">رمز المنتج: {item.sku}</p>
                      <p className="text-xs text-gray-400">رقم الدفعة: {item.batch}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant="outline" className="text-xs">
                          {item.category}
                        </Badge>
                        <Badge className={`text-xs ${getStatusColor(item.alertLevel)}`}>
                          {getAlertIcon(item.alertLevel)}
                          <span className="mr-1">{item.alertLevel}</span>
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <div className="text-left">
                    <p className="text-sm text-gray-600">تاريخ الانتهاء</p>
                    <p className="text-lg font-semibold">{item.expiryDate}</p>
                    <p className={`text-sm ${getDaysLeftColor(item.daysLeft)}`}>
                      {item.daysLeft < 0
                        ? `منتهي منذ ${Math.abs(item.daysLeft)} يوم`
                        : item.daysLeft === 0
                          ? "ينتهي اليوم"
                          : `${item.daysLeft} يوم متبقي`}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div>
                    <p className="text-xs text-gray-500">الكمية</p>
                    <p className="font-semibold">{item.quantity} قطعة</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">المستودع</p>
                    <p className="text-sm">{item.warehouse}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">المورد</p>
                    <p className="text-sm">{item.supplier}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">الحالة</p>
                    <p className="text-sm font-medium">{item.status}</p>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <div className="flex gap-2">
                    {item.alertLevel === "منتهي" ? (
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-red-600 border-red-200 hover:bg-red-50 bg-transparent"
                      >
                        <Trash2 className="h-4 w-4 ml-1" />
                        إزالة من المخزون
                      </Button>
                    ) : (
                      <Button size="sm" variant="outline">
                        <RefreshCw className="h-4 w-4 ml-1" />
                        تحديث التاريخ
                      </Button>
                    )}
                    <Button size="sm" variant="outline">
                      <Bell className="h-4 w-4 ml-1" />
                      إعداد تنبيه
                    </Button>
                  </div>
                  <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                    عرض التفاصيل
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
