"use client"

import { useState, useEffect } from "react"
import { Search, Plus, MoreHorizontal, Filter, Edit, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { apiClient } from "@/lib/api/client"
import { API_CONFIG } from "@/lib/config/api"
import { toast } from "sonner"
import CategoryForm from "./category-form"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

// تعريف واجهة البيانات (مرن ليتقبل البيانات من البايثون)
interface Category {
  id: number | string
  name: string
  description?: string
  productCount?: number
  status: string
}

export default function CategoriesManagement() {
  const [categories, setCategories] = useState<Category[]>([])
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all") // ✅ القيمة الافتراضية ليست فارغة
  const [isLoading, setIsLoading] = useState(true)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [categoryToDelete, setCategoryToDelete] = useState<number | string | null>(null)
  const [editingCategory, setEditingCategory] = useState<any | null>(null)

  // دالة لجلب البيانات من السيرفر
  const loadCategories = async () => {
    setIsLoading(true)
    try {
      // جلب القائمة من Python API
      const response = await apiClient.get<any>(API_CONFIG.ENDPOINTS.CATEGORIES)

      let formattedCategories: Category[] = []

      // التحقق وتنسيق البيانات - الـ API قد يعيد قائمة أو مصفوفة من `CategoryResponse`
      const rawData = Array.isArray(response) ? response : (response?.categories || (response as any)?.items || [])

      if (Array.isArray(rawData)) {
        formattedCategories = rawData.map((item: any, index: number) => {
          return {
            id: item.id || index,
            name: item.name || item.category || "بدون اسم",
            description: item.description || "-",
            productCount: item.product_count || item.count || 0,
            status: item.is_active !== false ? "active" : "archived"
          }
        })
      }

      setCategories(formattedCategories)
    } catch (error) {
      console.error("❌ Failed to load categories:", error)
      toast.error("فشل تحميل الفئات")
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteCategory = async (id: number | string) => {
    try {
      await apiClient.delete(`/api/v1/categories/${id}`)
      toast.success("تم حذف الفئة بنجاح")
      loadCategories()
    } catch (error) {
      console.error("فشل حذف الفئة:", error)
      toast.error("فشل حذف الفئة")
    } finally {
      setIsDeleteDialogOpen(false)
      setCategoryToDelete(null)
    }
  }

  // تشغيل عند فتح الصفحة
  useEffect(() => {
    loadCategories()
  }, [])

  // منطق الفلترة الآمن
  const filteredCategories = categories.filter((category) => {
    // 1. حماية ضد القيم الفارغة والبحث الآمن
    const name = category.name || ''
    const matchesSearch = name.toLowerCase().includes(searchTerm.toLowerCase())

    // 2. فلترة الحالة
    const matchesStatus = statusFilter === "all" || category.status === statusFilter

    return matchesSearch && matchesStatus
  })

  return (
    <div className="space-y-6" dir="rtl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">إدارة الفئات</h1>
          <p className="text-gray-500">تصنيف وتنظيم المنتجات</p>
        </div>
        <CategoryForm
          category={editingCategory}
          onSaved={() => {
            loadCategories();
            setEditingCategory(null);
          }}
        />
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle>قائمة الفئات</CardTitle>
          <CardDescription>عرض وإدارة جميع فئات المنتجات في النظام</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute right-3 top-2.5 h-4 w-4 text-gray-400" />
              <Input
                placeholder="بحث عن فئة..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pr-10"
              />
            </div>

            {/* ✅ تم إصلاح القيم الفارغة في القائمة المنسدلة */}
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <Filter className="ml-2 h-4 w-4" />
                <SelectValue placeholder="تصفية حسب الحالة" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">جميع الحالات</SelectItem>
                <SelectItem value="active">نشط</SelectItem>
                <SelectItem value="archived">مؤرشف</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">اسم الفئة</TableHead>
                  <TableHead className="text-right">الوصف</TableHead>
                  <TableHead className="text-center">عدد المنتجات</TableHead>
                  <TableHead className="text-center">الحالة</TableHead>
                  <TableHead className="text-left">إجراءات</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8">جاري التحميل...</TableCell>
                  </TableRow>
                ) : filteredCategories.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-gray-500">لا توجد فئات مطابقة</TableCell>
                  </TableRow>
                ) : (
                  filteredCategories.map((category) => (
                    <TableRow key={category.id}>
                      <TableCell className="font-medium">{category.name}</TableCell>
                      <TableCell>{category.description}</TableCell>
                      <TableCell className="text-center">{category.productCount}</TableCell>
                      <TableCell className="text-center">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${category.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                          {category.status === 'active' ? 'نشط' : 'مؤرشف'}
                        </span>
                      </TableCell>
                      <TableCell className="text-left">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>الإجراءات</DropdownMenuLabel>
                            <DropdownMenuItem onClick={() => setEditingCategory(category)}>
                              <Edit className="ml-2 h-4 w-4" /> تعديل
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              className="text-red-600"
                              onClick={() => {
                                setCategoryToDelete(category.id)
                                setIsDeleteDialogOpen(true)
                              }}
                            >
                              <Trash2 className="ml-2 h-4 w-4" /> حذف
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* حوار تأكيد الحذف */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>هل أنت متأكد من حذف الفئة؟</AlertDialogTitle>
            <AlertDialogDescription>
              سيتم حذف الفئة نهائياً. تأكد من عدم وجود منتجات تابعة لهذه الفئة.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setCategoryToDelete(null)}>إلغاء</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => categoryToDelete && handleDeleteCategory(categoryToDelete)}
              className="bg-red-600 hover:bg-red-700"
            >
              حذف
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
