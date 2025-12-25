"use client"

import { useState, useEffect } from "react"
import {
  Search, Plus, MoreHorizontal, Filter,
  Edit, Trash2, Package, ArrowUpDown, RefreshCw
} from "lucide-react"
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
import { Badge } from "@/components/ui/badge"
import { apiClient } from "@/lib/api/client"
import { API_CONFIG } from "@/lib/config/api"
import { toast } from "sonner"
import ProductForm from "./product-form"
import type { Product } from "@/lib/types"
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

export default function ProductsManagement() {
  const [products, setProducts] = useState<Product[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("all")
  const [statusFilter, setStatusFilter] = useState("all")
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [productToDelete, setProductToDelete] = useState<number | null>(null)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)

  // دالة جلب المنتجات
  const loadProducts = async () => {
    setIsLoading(true)
    try {
      // طلب البيانات من السيرفر
      const response = await apiClient.get<any>(API_CONFIG.ENDPOINTS.PRODUCTS)

      // التحقق مما إذا كانت البيانات مصفوفة أو كائن يحتوي على مصفوفة (Pagination)
      const productsData = Array.isArray(response) ? response : (response?.products || response?.items || response?.data || [])

      if (Array.isArray(productsData)) {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/44969d06-4743-4a0b-9eea-995f46b96ce5', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            location: 'products-management.tsx:71',
            message: 'loadProducts BEFORE mapping',
            data: {
              products_count: productsData.length,
              first_product_keys: productsData[0] ? Object.keys(productsData[0]) : [],
              first_product_sample: productsData[0] ? Object.fromEntries(Object.entries(productsData[0]).slice(0, 8)) : {}
            },
            timestamp: Date.now(),
            sessionId: 'debug-session',
            runId: 'run1',
            hypothesisId: 'D'
          })
        }).catch(() => {});
        // #endregion
        // تنسيق البيانات لتناسب الواجهة
        const formattedProducts = productsData.map((item: any) => ({
          id: item.id,
          name: item.name || item.name_ar || "منتج بدون اسم",
          name_ar: item.name_ar,
          sku: item.sku || item.barcode || `SKU-${item.id}`,
          category_id: item.category_id,
          category: item.category,
          price: Number(item.selling_price || item.price || 0),
          selling_price: Number(item.selling_price || item.price || 0),
          cost: Number(item.cost || 0),
          stock: Number(item.current_stock || item.stock || 0),
          current_stock: Number(item.current_stock || item.stock || 0),
          min_stock_level: item.min_stock_level || item.min_stock || 0,
          status: (item.current_stock > 0 || item.stock > 0 ? 'active' : 'draft') as 'active' | 'draft' | 'archived',
          is_active: item.is_active !== false,
          created_at: item.created_at,
          updated_at: item.updated_at,
        } as Product))
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/44969d06-4743-4a0b-9eea-995f46b96ce5', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            location: 'products-management.tsx:91',
            message: 'loadProducts AFTER mapping',
            data: {
              products_count: formattedProducts.length,
              first_product_keys: formattedProducts[0] ? Object.keys(formattedProducts[0]) : [],
              first_product_sample: formattedProducts[0] ? Object.fromEntries(Object.entries(formattedProducts[0]).slice(0, 8)) : {}
            },
            timestamp: Date.now(),
            sessionId: 'debug-session',
            runId: 'run1',
            hypothesisId: 'D'
          })
        }).catch(() => {});
        // #endregion
        setProducts(formattedProducts)
      }
    } catch (error) {
      console.error("فشل تحميل المنتجات:", error)
      toast.error("فشل تحميل المنتجات من الخادم")
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteProduct = async (id: number) => {
    try {
      await apiClient.delete(`${API_CONFIG.ENDPOINTS.PRODUCTS}/${id}`)

      toast.success("تم حذف المنتج بنجاح")
      loadProducts()
    } catch (error) {
      console.error("فشل حذف المنتج:", error)
      toast.error("فشل حذف المنتج")
    } finally {
      setIsDeleteDialogOpen(false)
      setProductToDelete(null)
    }
  }

  // تحميل عند الفتح
  useEffect(() => {
    loadProducts()
  }, [])

  // منطق الفلترة والبحث
  const filteredProducts = products.filter((product) => {
    const matchesSearch =
      (product.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (product.sku || '').toLowerCase().includes(searchTerm.toLowerCase())

    const categoryName = typeof product.category === 'string' ? product.category : product.category?.name
    const matchesCategory = categoryFilter === "all" || categoryName === categoryFilter
    // const matchesStatus = statusFilter === "all" || product.status === statusFilter

    return matchesSearch && matchesCategory
  })

  return (
    <div className="space-y-6" dir="rtl">
      {/* رأس الصفحة */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">إدارة المنتجات</h1>
          <p className="text-gray-500">مراقبة المخزون، تعديل الأسعار، وإدارة الأصناف</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={loadProducts}>
            <RefreshCw className="h-4 w-4 ml-2" /> تحديث
          </Button>
          <ProductForm
            product={editingProduct}
            onSaved={() => {
              loadProducts();
              setEditingProduct(null);
            }}
          />
        </div>
      </div>

      {/* أدوات البحث والفلترة */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute right-3 top-2.5 h-4 w-4 text-gray-400" />
              <Input
                placeholder="بحث باسم المنتج أو الرمز (SKU)..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pr-10"
              />
            </div>

            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-[180px]">
                <Filter className="ml-2 h-4 w-4" />
                <SelectValue placeholder="الفئة" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">جميع الفئات</SelectItem>
                {/* استخراج الفئات الفريدة من المنتجات الحالية */}
                {Array.from(new Set(
                  products
                    .map(p => typeof p.category === 'string' ? p.category : p.category?.name)
                    .filter((cat): cat is string => cat !== undefined)
                )).map(cat => (
                  <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* جدول المنتجات */}
      <Card className="overflow-hidden">
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50/50">
                <TableHead className="text-right">المنتج</TableHead>
                <TableHead className="text-right">الرمز (SKU)</TableHead>
                <TableHead className="text-center">الفئة</TableHead>
                <TableHead className="text-center">السعر</TableHead>
                <TableHead className="text-center">المخزون</TableHead>
                <TableHead className="text-center">الحالة</TableHead>
                <TableHead className="text-left">إجراءات</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-24 text-center">
                    جاري تحميل المنتجات من المخزن...
                  </TableCell>
                </TableRow>
              ) : filteredProducts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-24 text-center text-gray-500">
                    لا توجد منتجات مطابقة للبحث
                  </TableCell>
                </TableRow>
              ) : (
                filteredProducts.map((product) => (
                  <TableRow key={product.id} className="hover:bg-gray-50/50 transition-colors">
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded bg-blue-100 flex items-center justify-center text-blue-600">
                          <Package className="h-4 w-4" />
                        </div>
                        {product.name}
                      </div>
                    </TableCell>
                    <TableCell className="text-gray-500 font-mono text-xs">{product.sku}</TableCell>
                    <TableCell className="text-center">
                      <Badge variant="outline">
                        {typeof product.category === 'string' ? product.category : product.category?.name || 'بدون فئة'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center font-bold text-green-700">
                      {product.price.toLocaleString()} د.ج
                    </TableCell>
                    <TableCell className="text-center">
                      <span className={`font-bold ${product.stock <= 10 ? 'text-red-600' : 'text-gray-700'}`}>
                        {product.stock}
                      </span>
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant={product.stock > 0 ? "default" : "destructive"}>
                        {product.stock > 0 ? 'متوفر' : 'نفذت الكمية'}
                      </Badge>
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
                          <DropdownMenuItem onClick={() => setEditingProduct(product)}>
                            <Edit className="ml-2 h-4 w-4" /> تعديل المنتج
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Package className="ml-2 h-4 w-4" /> تعديل المخزون
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-red-600"
                            onClick={() => {
                              setProductToDelete(product.id)
                              setIsDeleteDialogOpen(true)
                            }}
                          >
                            <Trash2 className="ml-2 h-4 w-4" /> حذف المنتج
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
      </Card>

      {/* حوار تأكيد الحذف */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>هل أنت متأكد من حذف المنتج؟</AlertDialogTitle>
            <AlertDialogDescription>
              سيتم حذف المنتج نهائياً من النظام. هذا الإجراء لا يمكن التراجع عنه.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setProductToDelete(null)}>إلغاء</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => productToDelete && handleDeleteProduct(productToDelete)}
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
