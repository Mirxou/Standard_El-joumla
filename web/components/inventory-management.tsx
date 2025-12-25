"use client"

import { useEffect, useMemo, useState } from "react"
import { Search, Pencil, RefreshCcw, Activity, Download, Filter, ChevronRight, ChevronLeft, Loader2 } from "lucide-react"

import type { Product, StockMovement, Category } from "@/lib/database/types"
import { supabase } from "@/lib/supabase"
import { toast } from "sonner"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

type EditorState = {
  name_ar: string
  sku: string
  selling_price: string
  min_stock_level: string
  reorder_point: string
  current_stock: string
  notes: string
}

const emptyEditorState: EditorState = {
  name_ar: "",
  sku: "",
  selling_price: "",
  min_stock_level: "",
  reorder_point: "",
  current_stock: "",
  notes: "",
}

export default function InventoryManagement() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")
  const [stockFilter, setStockFilter] = useState<string>("all")
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [editorOpen, setEditorOpen] = useState(false)
  const [editorState, setEditorState] = useState<EditorState>(emptyEditorState)
  const [saveLoading, setSaveLoading] = useState(false)
  const [movements, setMovements] = useState<StockMovement[]>([])
  const [movementsLoading, setMovementsLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(10)
  const [categoryFilter, setCategoryFilter] = useState<string>("all")
  const [categories, setCategories] = useState<Category[]>([])

  useEffect(() => {
    loadProducts()
    fetchCategories()
  }, [])

  async function fetchCategories() {
    try {
      const { data, error } = await supabase
        .from('categories')
        .select('*')
        .eq('is_active', true)

      if (error) throw error
      setCategories(Array.isArray(data) ? data : (data?.categories || []))
    } catch (error) {
      console.error('[inventory] Error fetching categories:', error)
    }
  }

  useEffect(() => {
    if (!selectedProduct) return
    setEditorState({
      name_ar: selectedProduct.name_ar ?? selectedProduct.name ?? "",
      sku: selectedProduct.sku ?? "",
      selling_price: selectedProduct.selling_price?.toString() ?? "",
      min_stock_level: selectedProduct.min_stock_level?.toString() ?? "0",
      reorder_point: selectedProduct.reorder_point?.toString() ?? "0",
      current_stock: selectedProduct.current_stock?.toString() ?? "0",
      notes: "",
    })
    loadMovements(selectedProduct.id)
  }, [selectedProduct])

  // دالة تصدير Excel
  function exportToExcel() {
    if (filteredProducts.length === 0) {
      toast.error("لا توجد منتجات للتصدير")
      return
    }

    const headers = [
      "SKU",
      "اسم المنتج",
      "الكمية الحالية",
      "الحد الأدنى",
      "نقطة إعادة الطلب",
      "سعر التكلفة",
      "سعر البيع",
      "قيمة المخزون",
      "الحالة"
    ]

    const csvRows = [
      headers.join(","),
      ...filteredProducts.map(product => {
        const stockValue = (product.current_stock || 0) * (product.cost_price || 0)
        const stockStatus = product.current_stock === 0 ? 'نفد' :
          (product.current_stock || 0) <= (product.min_stock_level || 0) ? 'منخفض' : 'جيد'

        return [
          product.sku,
          `"${product.name_ar || product.name}"`,
          product.current_stock || 0,
          product.min_stock_level || 0,
          product.reorder_point || 0,
          (product.cost_price || 0).toFixed(2),
          (product.selling_price || 0).toFixed(2),
          stockValue.toFixed(2),
          stockStatus
        ].join(",")
      })
    ]

    const csvContent = csvRows.join("\n")
    const BOM = "\uFEFF"
    const blob = new Blob([BOM + csvContent], { type: "text/csv;charset=utf-8;" })
    const link = document.createElement("a")
    link.href = URL.createObjectURL(blob)
    link.download = `inventory_export_${new Date().toISOString().split('T')[0]}.csv`
    link.click()
    toast.success(`تم تصدير ${filteredProducts.length} منتج بنجاح`)
  }

  const filteredProducts = useMemo(() => {
    let filtered = products

    // فلترة البحث
    if (searchTerm.trim()) {
      filtered = filtered.filter((product) => {
        const target = `${product.name_ar} ${product.name} ${product.sku}`.toLowerCase()
        return target.includes(searchTerm.toLowerCase())
      })
    }

    // فلترة المخزون
    if (stockFilter === "out") {
      filtered = filtered.filter(p => (p.current_stock || 0) === 0)
    } else if (stockFilter === "low") {
      filtered = filtered.filter(p => (p.current_stock || 0) > 0 && (p.current_stock || 0) <= (p.min_stock_level || 0))
    } else if (stockFilter === "healthy") {
      filtered = filtered.filter(p => (p.current_stock || 0) > (p.min_stock_level || 0))
    }

    // فلترة الفئة
    if (categoryFilter !== "all") {
      filtered = filtered.filter(p => p.category_id === categoryFilter)
    }

    return filtered
  }, [products, searchTerm, stockFilter, categoryFilter])

  // Pagination
  const totalPages = Math.ceil(filteredProducts.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const paginatedProducts = filteredProducts.slice(startIndex, endIndex)

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1)
  }, [searchTerm, stockFilter, categoryFilter])

  const stats = useMemo(() => {
    const count = products.length
    const totalStock = products.reduce((sum, product) => sum + (product.current_stock || 0), 0)
    const totalValue = products.reduce(
      (sum, product) => sum + (product.current_stock || 0) * (product.cost_price || 0),
      0
    )
    const alerts = products.filter((product) => (product.current_stock || 0) <= (product.min_stock_level || 0)).length
    return { count, totalStock, totalValue, alerts }
  }, [products])

  async function loadProducts() {
    setLoading(true)
    try {
      const { data, error } = await supabase.from("products").select("*")
      if (error) throw error

      const rawProducts = Array.isArray(data) ? data : (data?.products || [])

      if (!rawProducts || rawProducts.length === 0) {
        setProducts([])
        toast.info("لا توجد منتجات مسجلة")
      } else {
        const mappedProducts = rawProducts.map((p: any) => ({
          ...p,
          name_ar: p.name_ar || p.name,
          min_stock_level: p.min_stock_level || p.min_stock || 0,
          current_stock: p.current_stock || p.stock || 0
        }))
        setProducts(mappedProducts)
      }
    } catch (error) {
      console.error("[inventory] failed to load products", error)
      toast.error(error instanceof Error ? error.message : "تعذر تحميل المخزون")
    } finally {
      setLoading(false)
    }
  }

  async function loadMovements(productId: string | number) {
    setMovementsLoading(true)
    try {
      const { data, error } = await supabase
        .from("stock_movements")
        .select("*")
        .eq("product_id", productId)
        .order("created_at", { ascending: false })
        .limit(8)
      if (error) throw error
      setMovements(data ?? [])
    } catch (error) {
      console.error("[inventory] failed to load movements", error)
      setMovements([])
    } finally {
      setMovementsLoading(false)
    }
  }

  const handleFieldChange = (field: keyof EditorState, value: string) => {
    setEditorState((prev) => ({ ...prev, [field]: value }))
  }

  const openEditor = (product: Product) => {
    setSelectedProduct(product)
    setEditorOpen(true)
  }

  const closeEditor = () => {
    setEditorOpen(false)
    setSelectedProduct(null)
    setEditorState(emptyEditorState)
    setMovements([])
  }

  const handleSave = async () => {
    if (!selectedProduct) return
    setSaveLoading(true)
    const nextStock = Number(editorState.current_stock) || 0
    const payload = {
      name: editorState.name_ar.trim(),
      barcode: editorState.sku.trim(),
      selling_price: Number(editorState.selling_price) || 0,
      min_stock: Number(editorState.min_stock_level) || 0,
      reorder_point: Number(editorState.reorder_point) || 0,
      current_stock: nextStock,
    }
    try {
      const { error } = await supabase.from("products").update(payload).eq("id", selectedProduct.id)
      if (error) throw error

      const diff = nextStock - (selectedProduct.current_stock || 0)
      if (diff !== 0) {
        await supabase.from("stock_movements").insert({
          product_id: selectedProduct.id,
          movement_type: diff > 0 ? "in" : "out",
          quantity: Math.abs(diff),
          notes: editorState.notes || "تعديل مباشر من شاشة حركات المخزون",
        })
      }

      setProducts((prev) =>
        prev.map((product) =>
          product.id === selectedProduct.id ? ({ ...product, ...payload } as Product) : product
        )
      )

      setSelectedProduct((prev) => (prev ? ({ ...prev, ...payload } as Product) : prev))
      toast.success("تم حفظ التعديلات\nتم تحديث بيانات المنتج وحركة المخزون.")
      loadMovements(selectedProduct.id)
      setEditorOpen(false)
    } catch (error) {
      console.error("[inventory] failed to save", error)
      toast.error("فشل حفظ التعديلات", {
        description: error instanceof Error ? error.message : "تحقق من الاتصال بقاعدة البيانات",
      })
    } finally {
      setSaveLoading(false)
    }
  }

  const renderStatus = (product: Product) => {
    if ((product.current_stock || 0) <= 0) {
      return <Badge className="bg-red-100 text-red-700 border-0">نفد</Badge>
    }
    if ((product.current_stock || 0) <= (product.min_stock_level || 0)) {
      return <Badge className="bg-orange-100 text-orange-700 border-0">منخفض</Badge>
    }
    return <Badge className="bg-green-100 text-green-700 border-0">جيد</Badge>
  }

  return (
    <div className="space-y-6" dir="rtl">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">حركات المخزون</h1>
          <p className="text-sm text-gray-500">راجع المخزون وعدّل تفاصيل المنتجات مباشرة من هنا.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={loadProducts} type="button">
            <RefreshCcw className="h-4 w-4 ml-1" />
            تحديث القائمة
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-sm text-gray-500">عدد المنتجات</p>
            <p className="text-2xl font-bold text-gray-900">{stats.count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-sm text-gray-500">إجمالي الوحدات</p>
            <p className="text-2xl font-bold text-gray-900">{stats.totalStock.toLocaleString("en-US")}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-sm text-gray-500">قيمة تقديرية</p>
            <p className="text-2xl font-bold text-gray-900">{stats.totalValue.toLocaleString("en-US")} ر.س</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-sm text-gray-500">حالات حرجة</p>
            <p className="text-2xl font-bold text-red-600">{stats.alerts}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <CardTitle>
              سجل المخزون
              {filteredProducts.length !== products.length && (
                <span className="text-blue-600 font-semibold mr-2 text-sm">
                  ({filteredProducts.length} من {products.length})
                </span>
              )}
            </CardTitle>
            <Button variant="outline" onClick={exportToExcel} type="button">
              <Download className="h-4 w-4 ml-2" />
              تصدير Excel
            </Button>
          </div>
          <div className="flex flex-col sm:flex-row gap-2">
            <div className="relative flex-1">
              <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <Input
                placeholder="بحث باسم المنتج أو رمز SKU..."
                className="pr-10"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
              />
            </div>
            <Select value={stockFilter} onValueChange={setStockFilter}>
              <SelectTrigger className="w-full sm:w-[180px]">
                <Filter className="h-4 w-4 ml-2" />
                <SelectValue placeholder="حالة المخزون" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">جميع الحالات</SelectItem>
                <SelectItem value="healthy">مخزون صحي</SelectItem>
                <SelectItem value="low">مخزون منخفض</SelectItem>
                <SelectItem value="out">نفد من المخزون</SelectItem>
              </SelectContent>
            </Select>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-full sm:w-[180px]">
                <SelectValue placeholder="الفئة" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">جميع الفئات</SelectItem>
                {categories.map(cat => (
                  <SelectItem key={cat.id} value={cat.id?.toString()}>{cat.name_ar || cat.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="py-10 text-center text-sm text-gray-500">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
              جارٍ تحميل بيانات المخزون...
            </div>
          ) : filteredProducts.length === 0 ? (
            <div className="py-10 text-center text-sm text-gray-500">
              {products.length === 0 ? (
                <div>
                  <p className="mb-2">لا توجد منتجات</p>
                  <p className="text-xs text-gray-400">ابدأ بإضافة منتج جديد</p>
                </div>
              ) : (
                <div>
                  <p className="mb-2">لا توجد منتجات مطابقة للبحث</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSearchTerm("")
                      setStockFilter("all")
                      setCategoryFilter("all")
                    }}
                    type="button"
                  >
                    إعادة تعيين الفلاتر
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50 text-xs text-gray-500">
                      <th className="px-3 py-2 text-right font-medium">المنتج</th>
                      <th className="px-3 py-2 text-right font-medium">SKU</th>
                      <th className="px-3 py-2 text-right font-medium">الفئة</th>
                      <th className="px-3 py-2 text-right font-medium">الكمية</th>
                      <th className="px-3 py-2 text-right font-medium">الحد الأدنى</th>
                      <th className="px-3 py-2 text-right font-medium">سعر البيع</th>
                      <th className="px-3 py-2 text-right font-medium">الحالة</th>
                      <th className="px-3 py-2 text-right font-medium">إجراءات</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedProducts.map((product) => {
                      const category = categories.find(c => c.id === product.category_id)
                      return (
                        <tr key={product.id} className="border-b">
                          <td className="px-3 py-2 font-medium text-gray-900">{product.name_ar || product.name}</td>
                          <td className="px-3 py-2 text-gray-600">{product.sku}</td>
                          <td className="px-3 py-2">
                            {category ? (
                              <Badge variant="outline" className="text-xs">
                                {category.name_ar}
                              </Badge>
                            ) : (
                              <span className="text-gray-400 text-xs">-</span>
                            )}
                          </td>
                          <td className="px-3 py-2">
                            <span className="font-semibold text-gray-900">{product.current_stock ?? 0}</span>
                          </td>
                          <td className="px-3 py-2 text-gray-600">{product.min_stock_level ?? 0}</td>
                          <td className="px-3 py-2 text-gray-900">{product.selling_price?.toFixed(2)} ر.س</td>
                          <td className="px-3 py-2">{renderStatus(product)}</td>
                          <td className="px-3 py-2">
                            <Button variant="ghost" size="sm" onClick={() => openEditor(product)} type="button">
                              <Pencil className="h-4 w-4 ml-2" />
                              تعديل
                            </Button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {filteredProducts.length > itemsPerPage && (
                <div className="flex items-center justify-between px-4 py-3 border-t">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-500">
                      عرض
                    </span>
                    <Select value={itemsPerPage.toString()} onValueChange={(value) => {
                      setItemsPerPage(parseInt(value))
                      setCurrentPage(1)
                    }}>
                      <SelectTrigger className="w-[80px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="10">10</SelectItem>
                        <SelectItem value="25">25</SelectItem>
                        <SelectItem value="50">50</SelectItem>
                        <SelectItem value="100">100</SelectItem>
                      </SelectContent>
                    </Select>
                    <span className="text-sm text-gray-500">
                      من {filteredProducts.length} منتج
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      type="button"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                    <span className="text-sm text-gray-700">
                      صفحة {currentPage} من {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages}
                      type="button"
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <Dialog open={editorOpen} onOpenChange={(open) => (open ? setEditorOpen(true) : closeEditor())}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>تعديل بيانات المنتج</DialogTitle>
          </DialogHeader>

          {selectedProduct ? (
            <div className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="name_ar">اسم المنتج</Label>
                  <Input
                    id="name_ar"
                    value={editorState.name_ar}
                    onChange={(event) => handleFieldChange("name_ar", event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sku">رمز SKU</Label>
                  <Input id="sku" value={editorState.sku} onChange={(event) => handleFieldChange("sku", event.target.value)} />
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <Label htmlFor="selling_price">سعر البيع</Label>
                  <Input
                    id="selling_price"
                    type="number"
                    value={editorState.selling_price}
                    onChange={(event) => handleFieldChange("selling_price", event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="current_stock">الكمية الحالية</Label>
                  <Input
                    id="current_stock"
                    type="number"
                    value={editorState.current_stock}
                    onChange={(event) => handleFieldChange("current_stock", event.target.value)}
                  />
                  <p className="text-xs text-gray-500">
                    الكمية المسجلة حالياً: <span className="font-semibold">{selectedProduct.current_stock ?? 0}</span>
                  </p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="min_stock_level">الحد الأدنى</Label>
                  <Input
                    id="min_stock_level"
                    type="number"
                    value={editorState.min_stock_level}
                    onChange={(event) => handleFieldChange("min_stock_level", event.target.value)}
                  />
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="reorder_point">نقطة إعادة الطلب</Label>
                  <Input
                    id="reorder_point"
                    type="number"
                    value={editorState.reorder_point}
                    onChange={(event) => handleFieldChange("reorder_point", event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="notes">ملاحظات حركة المخزون</Label>
                  <Textarea
                    id="notes"
                    placeholder="مثال: تسوية يدوية بعد الجرد الشهري"
                    value={editorState.notes}
                    onChange={(event) => handleFieldChange("notes", event.target.value)}
                    rows={3}
                  />
                </div>
              </div>

              <div className="rounded-xl border bg-gray-50 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-gray-700">
                  <Activity className="h-4 w-4" />
                  أحدث الحركات
                </div>
                <div className="mt-3 space-y-2">
                  {movementsLoading ? (
                    <p className="text-xs text-gray-500">جارٍ تحميل سجل الحركات...</p>
                  ) : movements.length === 0 ? (
                    <p className="text-xs text-gray-500">لا توجد حركات مسجلة لهذا المنتج بعد.</p>
                  ) : (
                    movements.map((movement) => (
                      <div key={movement.id} className="rounded-lg bg-white p-2 text-xs text-gray-700">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold">{movement.movement_type === "in" ? "إدخال" : "إخراج"}</span>
                          <span>
                            {new Date(movement.created_at).toLocaleString("ar-SA", {
                              dateStyle: "short",
                              timeStyle: "short",
                            })}
                          </span>
                        </div>
                        <p className="text-gray-500">الكمية: {movement.quantity}</p>
                        {movement.notes ? <p className="text-gray-400">{movement.notes}</p> : null}
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={closeEditor} type="button">
                  إلغاء
                </Button>
                <Button onClick={handleSave} disabled={saveLoading} type="button">
                  {saveLoading ? "جاري الحفظ..." : "حفظ التعديلات"}
                </Button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500">لم يتم تحديد منتج للتعديل.</p>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
