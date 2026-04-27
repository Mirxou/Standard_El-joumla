"use client"

import { useState } from "react"
import "./supplier-management.css"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Users,
  Plus,
  Search,
  Filter,
  Phone,
  Mail,
  MapPin,
  Package,
  Star,
  Calendar,
  FileText,
  Edit,
  Trash2,
  MoreVertical,
} from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { useEffect } from "react"
import { apiClient } from "@/lib/api/client"
import { API_CONFIG } from "@/lib/config/api"
import CreateSupplier from "./create-supplier"

// Utility function to calculate progress width
const getProgressBarWidth = (value: number): string => {
  return `progress-bar-${Math.round(value)}`
}

export default function SupplierManagement() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedCategory, setSelectedCategory] = useState("all")
  const [selectedStatus, setSelectedStatus] = useState("all")

  const [suppliers, setSuppliers] = useState<any[]>([])

  const loadSuppliers = async () => {
    try {
      const data = await apiClient.get<any[]>(API_CONFIG.ENDPOINTS.SUPPLIERS)
      const suppliersArray = Array.isArray(data) ? data : (data as any)?.items || (data as any)?.suppliers || []
      
      const mapped = suppliersArray.map((s: any) => ({
        id: s.id,
        name: s.name,
        category: "عام", // Placeholder
        contactPerson: s.contact_person || "-",
        phone: s.phone || "-",
        email: s.email || "-",
        address: s.address || "-",
        rating: 5.0, // Placeholder
        totalOrders: s.purchases_count || 0,
        totalValue: s.total_purchases || 0,
        lastOrder: "-", // Placeholder
        paymentTerms: "-", // Placeholder
        deliveryTime: "-", // Placeholder
        status: s.is_active ? "نشط" : "معلق",
        products: [], // Placeholder
        performance: {
          onTimeDelivery: 100,
          qualityRating: 5.0,
          priceCompetitiveness: 5.0,
        },
      }))
      setSuppliers(mapped)
    } catch (error: any) {
      console.error("Error loading suppliers:", error)
      setSuppliers([])
    }
  }

  useEffect(() => {
    loadSuppliers();
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case "نشط":
        return "bg-green-100 text-green-800"
      case "مؤقت":
        return "bg-orange-100 text-orange-800"
      case "معلق":
        return "bg-red-100 text-red-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const getRatingColor = (rating: number) => {
    if (rating >= 4.5) return "text-green-600"
    if (rating >= 4.0) return "text-blue-600"
    if (rating >= 3.5) return "text-orange-600"
    return "text-red-600"
  }

  const filteredSuppliers = suppliers.filter((supplier) => {
    const matchesSearch =
      supplier.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      supplier.contactPerson.toLowerCase().includes(searchTerm.toLowerCase()) ||
      supplier.phone.includes(searchTerm) ||
      supplier.email.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesCategory = selectedCategory === "all" || supplier.category === selectedCategory
    const matchesStatus = selectedStatus === "all" || supplier.status === selectedStatus

    return matchesSearch && matchesCategory && matchesStatus
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">إدارة الموردين المتقدمة</h1>
          <p className="text-gray-600">إدارة شاملة للموردين مع تقييم الأداء وتتبع الطلبات</p>
        </div>
        <CreateSupplier onSaved={loadSuppliers} />
      </div>

      {/* البحث والفلترة المتقدمة */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder="البحث بالاسم، جهة الاتصال، الهاتف، أو البريد الإلكتروني..."
            className="pr-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <Select value={selectedCategory} onValueChange={setSelectedCategory}>
          <SelectTrigger className="w-full md:w-48">
            <SelectValue placeholder="اختر الفئة" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">جميع الفئات</SelectItem>
            <SelectItem value="مواد غذائية">مواد غذائية</SelectItem>
            <SelectItem value="صحة وجمال">صحة وجمال</SelectItem>
            <SelectItem value="إلكترونيات">إلكترونيات</SelectItem>
            <SelectItem value="حلويات ومأكولات">حلويات ومأكولات</SelectItem>
            <SelectItem value="منتجات النظافة">منتجات النظافة</SelectItem>
          </SelectContent>
        </Select>
        <Select value={selectedStatus} onValueChange={setSelectedStatus}>
          <SelectTrigger className="w-full md:w-32">
            <SelectValue placeholder="الحالة" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">جميع الحالات</SelectItem>
            <SelectItem value="نشط">نشط</SelectItem>
            <SelectItem value="مؤقت">مؤقت</SelectItem>
            <SelectItem value="معلق">معلق</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="outline">
          <Filter className="h-4 w-4 ml-2" />
          فلاتر متقدمة
        </Button>
      </div>

      {/* ملخص الموردين */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-sm text-gray-600">إجمالي الموردين</p>
            <p className="text-2xl font-bold text-blue-600">{suppliers.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-sm text-gray-600">موردين نشطين</p>
            <p className="text-2xl font-bold text-green-600">{suppliers.filter((s) => s.status === "نشط").length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-sm text-gray-600">إجمالي الطلبات</p>
            <p className="text-2xl font-bold text-purple-600">{suppliers.reduce((sum, s) => sum + s.totalOrders, 0)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-sm text-gray-600">إجمالي القيمة</p>
            <p className="text-2xl font-bold text-orange-600">
              {suppliers.reduce((sum, s) => sum + s.totalValue, 0).toLocaleString('en-US')} ر.س
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-sm text-gray-600">متوسط التقييم</p>
            <p className="text-2xl font-bold text-yellow-600">
              {(suppliers.reduce((sum, s) => sum + s.rating, 0) / suppliers.length).toFixed(1)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* قائمة الموردين */}
      <div className="grid gap-6">
        {filteredSuppliers.map((supplier) => (
          <Card key={supplier.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="w-16 h-16 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Users className="h-8 w-8 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900">{supplier.name}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline" className="text-xs">
                        {supplier.category}
                      </Badge>
                      <Badge className={getStatusColor(supplier.status)}>{supplier.status}</Badge>
                    </div>
                    <div className="flex items-center gap-1 mt-2">
                      <Star className={`h-4 w-4 ${getRatingColor(supplier.rating)}`} fill="currentColor" />
                      <span className={`font-semibold ${getRatingColor(supplier.rating)}`}>{supplier.rating}</span>
                      <span className="text-sm text-gray-500">({supplier.totalOrders} طلب)</span>
                    </div>
                  </div>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem>
                      <Edit className="h-4 w-4 ml-2" />
                      تعديل
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <FileText className="h-4 w-4 ml-2" />
                      عرض التقارير
                    </DropdownMenuItem>
                    <DropdownMenuItem className="text-red-600">
                      <Trash2 className="h-4 w-4 ml-2" />
                      حذف
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardHeader>

            <CardContent>
              {/* معلومات الاتصال */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-gray-400" />
                  <div>
                    <p className="text-xs text-gray-500">جهة الاتصال</p>
                    <p className="font-medium">{supplier.contactPerson}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Phone className="h-4 w-4 text-gray-400" />
                  <div>
                    <p className="text-xs text-gray-500">الهاتف</p>
                    <p className="font-medium">{supplier.phone}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Mail className="h-4 w-4 text-gray-400" />
                  <div>
                    <p className="text-xs text-gray-500">البريد الإلكتروني</p>
                    <p className="font-medium text-sm">{supplier.email}</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 mb-4">
                <MapPin className="h-4 w-4 text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">العنوان</p>
                  <p className="font-medium">{supplier.address}</p>
                </div>
              </div>

              {/* المنتجات */}
              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-2">المنتجات المتوفرة:</p>
                <div className="flex flex-wrap gap-2">
                  {supplier.products?.map((product: any, index: number) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {product}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* إحصائيات الأداء */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">إجمالي الطلبات</p>
                  <p className="text-lg font-semibold">{supplier.totalOrders}</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">إجمالي القيمة</p>
                  <p className="text-lg font-semibold">{supplier.totalValue.toLocaleString()} ر.س</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">شروط الدفع</p>
                  <p className="text-lg font-semibold">{supplier.paymentTerms}</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">وقت التسليم</p>
                  <p className="text-lg font-semibold">{supplier.deliveryTime}</p>
                </div>
              </div>

              {/* مؤشرات الأداء */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>التسليم في الوقت المحدد</span>
                    <span className="font-semibold">{supplier.performance.onTimeDelivery}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full progress-bar"
                      // eslint-disable-next-line react/style-prop-object
                      style={{ width: `${supplier.performance.onTimeDelivery}%` }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>تقييم الجودة</span>
                    <span className="font-semibold">{supplier.performance.qualityRating}/5</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full progress-bar"
                      // eslint-disable-next-line react/style-prop-object
                      style={{ width: `${(supplier.performance.qualityRating / 5) * 100}%` }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>تنافسية الأسعار</span>
                    <span className="font-semibold">{supplier.performance.priceCompetitiveness}/5</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-purple-500 h-2 rounded-full progress-bar"
                      // eslint-disable-next-line react/style-prop-object
                      style={{ width: `${(supplier.performance.priceCompetitiveness / 5) * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              {/* الإجراءات */}
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Calendar className="h-4 w-4" />
                  <span>آخر طلب: {supplier.lastOrder}</span>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline">
                    <Package className="h-4 w-4 ml-1" />
                    طلب جديد
                  </Button>
                  <Button size="sm" variant="outline">
                    <FileText className="h-4 w-4 ml-1" />
                    عرض التقارير
                  </Button>
                  <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                    <Edit className="h-4 w-4 ml-1" />
                    إدارة المورد
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
