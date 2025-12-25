"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import {
  Warehouse,
  Plus,
  Search,
  MapPin,
  Package,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Users,
  Truck,
  BarChart3,
} from "lucide-react"
import CreateWarehouse from "./create-warehouse"
import { fetchFromAPI } from "@/lib/db/client"
import { useEffect } from "react"

export default function WarehouseManagement() {
  const [searchTerm, setSearchTerm] = useState("")
  const [warehouses, setWarehouses] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const loadWarehouses = async () => {
    setLoading(true)
    const data = await fetchFromAPI('/warehouses')
    if (Array.isArray(data)) {
      // Map Backend API to UI Model
      const mapped = data.map((w: any) => ({
        id: w.id,
        name: w.name,
        location: w.city || w.address || "غير محدد",
        manager: w.manager_name || "غير محدد",
        phone: w.phone || "-",
        capacity: w.capacity,
        currentStock: w.current_utilization,
        categories: ["عام"], // Placeholder
        totalValue: 0, // Placeholder
        lowStockItems: 0, // Placeholder
        criticalItems: 0, // Placeholder
        status: w.status,
        lastInventory: w.updated_at ? new Date(w.updated_at).toLocaleDateString('en-US') : "-",
      }))
      setWarehouses(mapped)
    }
    setLoading(false)
  }

  useEffect(() => {
    loadWarehouses()
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case "نشط":
        return "bg-green-100 text-green-800"
      case "صيانة":
        return "bg-orange-100 text-orange-800"
      case "مغلق":
        return "bg-red-100 text-red-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const getCapacityColor = (percentage: number) => {
    if (percentage >= 90) return "text-red-600"
    if (percentage >= 75) return "text-orange-600"
    return "text-green-600"
  }

  const filteredWarehouses = warehouses.filter(
    (warehouse) =>
      warehouse.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      warehouse.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
      warehouse.manager.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">إدارة المستودعات</h1>
          <p className="text-gray-600">إدارة شاملة للمستودعات مع تتبع المخزون والسعة</p>
        </div>
        <CreateWarehouse onSaved={loadWarehouses} />
      </div>

      {/* البحث */}
      <div className="relative">
        <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
        <Input
          placeholder="البحث في المستودعات، المواقع، أو المديرين..."
          className="pr-10"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* ملخص المستودعات */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">إجمالي المستودعات</p>
                <p className="text-2xl font-bold text-blue-600">{warehouses.length}</p>
              </div>
              <div className="bg-blue-100 p-2 rounded-lg">
                <Warehouse className="h-5 w-5 text-blue-600" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">{warehouses.filter((w) => w.status === "نشط").length} نشط</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">إجمالي السعة</p>
                <p className="text-2xl font-bold text-green-600">
                  {warehouses.reduce((sum, w) => sum + w.capacity, 0).toLocaleString('en-US')}
                </p>
              </div>
              <div className="bg-green-100 p-2 rounded-lg">
                <Package className="h-5 w-5 text-green-600" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">قطعة</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">المخزون الحالي</p>
                <p className="text-2xl font-bold text-purple-600">
                  {warehouses.reduce((sum, w) => sum + w.currentStock, 0).toLocaleString('en-US')}
                </p>
              </div>
              <div className="bg-purple-100 p-2 rounded-lg">
                <BarChart3 className="h-5 w-5 text-purple-600" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">قطعة</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">إجمالي القيمة</p>
                <p className="text-2xl font-bold text-orange-600">
                  {warehouses.reduce((sum, w) => sum + w.totalValue, 0).toLocaleString('en-US')} ر.س
                </p>
              </div>
              <div className="bg-orange-100 p-2 rounded-lg">
                <TrendingUp className="h-5 w-5 text-orange-600" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">قيمة المخزون</p>
          </CardContent>
        </Card>
      </div>

      {/* قائمة المستودعات */}
      <div className="grid gap-6">
        {filteredWarehouses.map((warehouse) => {
          const capacityPercentage = (warehouse.currentStock / warehouse.capacity) * 100

          return (
            <Card key={warehouse.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="w-16 h-16 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Warehouse className="h-8 w-8 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900">{warehouse.name}</h3>
                      <div className="flex items-center gap-2 mt-1">
                        <MapPin className="h-4 w-4 text-gray-400" />
                        <span className="text-sm text-gray-600">{warehouse.location}</span>
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <Users className="h-4 w-4 text-gray-400" />
                        <span className="text-sm text-gray-600">{warehouse.manager}</span>
                        <span className="text-sm text-gray-400">({warehouse.phone})</span>
                      </div>
                    </div>
                  </div>
                  <Badge className={getStatusColor(warehouse.status)}>{warehouse.status}</Badge>
                </div>
              </CardHeader>

              <CardContent>
                {/* الفئات */}
                <div className="mb-4">
                  <p className="text-sm text-gray-600 mb-2">الفئات المخزنة:</p>
                  <div className="flex flex-wrap gap-2">
                    {warehouse.categories?.map((category: any, index: number) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {category}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* إحصائيات المستودع */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500">السعة الإجمالية</p>
                    <p className="text-lg font-semibold">{warehouse.capacity.toLocaleString()}</p>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500">المخزون الحالي</p>
                    <p className="text-lg font-semibold">{warehouse.currentStock.toLocaleString()}</p>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500">قيمة المخزون</p>
                    <p className="text-lg font-semibold">{warehouse.totalValue.toLocaleString()} ر.س</p>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500">آخر جرد</p>
                    <p className="text-lg font-semibold">{warehouse.lastInventory}</p>
                  </div>
                </div>

                {/* نسبة الامتلاء */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-2">
                    <span>نسبة الامتلاء</span>
                    <span className={`font-semibold ${getCapacityColor(capacityPercentage)}`}>
                      {capacityPercentage.toFixed(1)}%
                    </span>
                  </div>
                  <Progress value={capacityPercentage} className="h-3" />
                </div>

                {/* تنبيهات المخزون */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="flex items-center gap-2 p-3 bg-orange-50 rounded-lg">
                    <TrendingDown className="h-4 w-4 text-orange-600" />
                    <div>
                      <p className="text-sm font-medium text-orange-800">مخزون منخفض</p>
                      <p className="text-xs text-orange-600">{warehouse.lowStockItems} عنصر</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 p-3 bg-red-50 rounded-lg">
                    <AlertTriangle className="h-4 w-4 text-red-600" />
                    <div>
                      <p className="text-sm font-medium text-red-800">حرج</p>
                      <p className="text-xs text-red-600">{warehouse.criticalItems} عنصر</p>
                    </div>
                  </div>
                </div>

                {/* الإجراءات */}
                <div className="flex justify-between items-center">
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline">
                      <Package className="h-4 w-4 ml-1" />
                      عرض المخزون
                    </Button>
                    <Button size="sm" variant="outline">
                      <Truck className="h-4 w-4 ml-1" />
                      نقل البضائع
                    </Button>
                    <Button size="sm" variant="outline">
                      <BarChart3 className="h-4 w-4 ml-1" />
                      تقرير المستودع
                    </Button>
                  </div>
                  <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                    إدارة المستودع
                  </Button>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
