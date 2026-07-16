"use client"

import { useState, useEffect } from "react"
import {
  Search, Plus, MoreHorizontal, Filter,
  Edit, Trash2, Package, ArrowUpDown, RefreshCw, CheckSquare, Square
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
import { Checkbox } from "@/components/ui/checkbox"
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
  const [selectedProducts, setSelectedProducts] = useState<Set<number>>(new Set())
  const [isBulkDeleteDialogOpen, setIsBulkDeleteDialogOpen] = useState(false)
  const [sortField, setSortField] = useState<"name" | "price" | "stock" | "sku">("name")
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc")

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
  const filteredProducts = products
    .filter((product) => {
      const matchesSearch =
        (product.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (product.sku || '').toLowerCase().includes(searchTerm.toLowerCase())

      const categoryName = typeof product.category === 'string' ? product.category : product.category?.name
      const matchesCategory = categoryFilter === "all" || categoryName === categoryFilter
      
      const matchesStatus = statusFilter === "all" || 
        (statusFilter === "active" && product.stock > 0) ||
        (statusFilter === "out_of_stock" && product.stock === 0) ||
        (statusFilter === "low_stock" && product.stock > 0 && product.stock <= (product.min_stock_level || 10))

      return matchesSearch && matchesCategory && matchesStatus
    })
    .sort((a, b) => {
      let aValue: any, bValue: any
      
      switch (sortField) {
        case "name":
          aValue = a.name?.toLowerCase() || ""
          bValue = b.name?.toLowerCase() || ""
          break
        case "price":
          aValue = a.price || 0
          bValue = b.price || 0
          break
        case "stock":
          aValue = a.stock || 0
          bValue = b.stock || 0
          break
        case "sku":
          aValue = a.sku?.toLowerCase() || ""
          bValue = b.sku?.toLowerCase() || ""
          break
        default:
          return 0
      }
      
      if (aValue < bValue) return sortDirection === "asc" ? -1 : 1
      if (aValue > bValue) return sortDirection === "asc" ? 1 : -1
      return 0
    })

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedProducts(new Set(filteredProducts.map(p => p.id)))
    } else {
      setSelectedProducts(new Set())
    }
  }

  const handleSelectProduct = (productId: number, checked: boolean) => {
    const newSelected = new Set(selectedProducts)
    if (checked) {
      newSelected.add(productId)
    } else {
      newSelected.delete(productId)
    }
    setSelectedProducts(newSelected)
  }

  const handleBulkDelete = async () => {
    if (selectedProducts.size === 0) return
    
    try {
      const deletePromises = Array.from(selectedProducts).map(id =>
        apiClient.delete(`${API_CONFIG.ENDPOINTS.PRODUCTS}/${id}`)
      )
      
      await Promise.all(deletePromises)
      toast.success(`تم حذف ${selectedProducts.size} منتج بنجاح`)
      setSelectedProducts(new Set())
      await loadProducts()
    } catch (error: any) {
      console.error("فشل حذف المنتجات:", error)
      toast.error("فشل حذف بعض المنتجات")
    } finally {
      setIsBulkDeleteDialogOpen(false)
    }
  }

  return (
    <div className="space-y-6" dir="rtl">
      {/* رأس الصفحة */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">إدارة المنتجات</h1>
          <p className="text-gray-500">مراقبة المخزون، تعديل الأسعار، وإدارة الأصناف</p>
        </div>
        <div className="flex gap-2">
          {selectedProducts.size > 0 && (
            <>
              <Button 
                variant="destructive" 
                onClick={() => setIsBulkDeleteDialogOpen(true)}
              >
                <Trash2 className="h-4 w-4 ml-2" /> حذف المحدد ({selectedProducts.size})
              </Button>
              <Button 
                variant="outline" 
                onClick={() => setSelectedProducts(new Set())}
              >
                إلغاء التحديد
              </Button>
            </>
          )}
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
            
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="حالة المخزون" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">جميع الحالات</SelectItem>
                <SelectItem value="active">متوفر</SelectItem>
                <SelectItem value="out_of_stock">نفذت الكمية</SelectItem>
                <SelectItem value="low_stock">مخزون منخفض</SelectItem>
              </SelectContent>
            </Select>

            <Select value={`${sortField}-${sortDirection}`} onValueChange={(value) => {
              const [field, direction] = value.split('-')
              setSortField(field as "name" | "price" | "stock" | "sku")
              setSortDirection(direction as "asc" | "desc")
            }}>
              <SelectTrigger className="w-[180px]">
                <ArrowUpDown className="ml-2 h-4 w-4" />
                <SelectValue placeholder="ترتيب" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="name-asc">الاسم (أ-ي)</SelectItem>
                <SelectItem value="name-desc">الاسم (ي-أ)</SelectItem>
                <SelectItem value="price-asc">السعر (منخفض-عالي)</SelectItem>
                <SelectItem value="price-desc">السعر (عالي-منخفض)</SelectItem>
                <SelectItem value="stock-asc">المخزون (قليل-كثير)</SelectItem>
                <SelectItem value="stock-desc">المخزون (كثير-قليل)</SelectItem>
                <SelectItem value="sku-asc">SKU (أ-ي)</SelectItem>
                <SelectItem value="sku-desc">SKU (ي-أ)</SelectItem>
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
                <TableHead className="w-12">
                  <Checkbox
                    checked={selectedProducts.size > 0 && selectedProducts.size === filteredProducts.length}
                    onCheckedChange={handleSelectAll}
                  />
                </TableHead>
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
                  <TableCell colSpan={8} className="h-24 text-center">
                    جاري تحميل المنتجات من المخزن...
                  </TableCell>
                </TableRow>
              ) : filteredProducts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="h-24 text-center text-gray-500">
                    لا توجد منتجات مطابقة للبحث
                  </TableCell>
                </TableRow>
              ) : (
                filteredProducts.map((product) => (
                  <TableRow key={product.id} className="hover:bg-gray-50/50 transition-colors">
                    <TableCell>
                      <Checkbox
                        checked={selectedProducts.has(product.id)}
                        onCheckedChange={(checked) => handleSelectProduct(product.id, checked as boolean)}
                      />
                    </TableCell>
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

      {/* حوار تأكيد الحذف المتعدد */}
      <AlertDialog open={isBulkDeleteDialogOpen} onOpenChange={setIsBulkDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>هل أنت متأكد من حذف المنتجات المحددة؟</AlertDialogTitle>
            <AlertDialogDescription>
              سيتم حذف {selectedProducts.size} منتج نهائياً من النظام. هذا الإجراء لا يمكن التراجع عنه.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>إلغاء</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleBulkDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              حذف المحدد
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
