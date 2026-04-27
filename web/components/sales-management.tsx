"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Calendar as CalendarIcon } from "lucide-react"
import { format } from "date-fns"
import { Calendar } from "@/components/ui/calendar"
import {
  Plus,
  Search,
  Filter,
  FileText,
  Printer,
  Download,
  Eye,
  Edit,
  Trash2,
  ShoppingCart,
  DollarSign,
  User,
  ChevronRight,
  ChevronLeft,
  RefreshCcw,
  Loader2,
  Copy,
  Check,
  MoreVertical,
} from "lucide-react"
import { toast } from "sonner"
import CreateInvoice from "./create-invoice"
import PrintInvoice from "./print-invoice"
import {
  getAllInvoices,
  deleteInvoice,
  updateInvoice,
  initializeSampleData,
  calculateStats,
  type Invoice,
} from "@/lib/invoice-storage"
import { TableSkeleton } from "@/components/ui/loading-skeletons"

export default function SalesManagement() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedStatus, setSelectedStatus] = useState("all")
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(10)
  const [dateFilter, setDateFilter] = useState<string>("all")
  const [stats, setStats] = useState({
    todaySales: 0,
    todayCount: 0,
    monthSales: 0,
    monthCount: 0,
    pendingCount: 0,
    pendingAmount: 0,
    averageInvoice: 0,
  })
  const [editingInvoice, setEditingInvoice] = useState<Invoice | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [invoiceToDelete, setInvoiceToDelete] = useState<string | null>(null)
  const [printDialogOpen, setPrintDialogOpen] = useState(false)
  const [invoiceToPrint, setInvoiceToPrint] = useState<Invoice | null>(null)
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false)
  const [invoiceToView, setInvoiceToView] = useState<Invoice | null>(null)
  const [copiedInvoiceId, setCopiedInvoiceId] = useState<string | null>(null)
  const [customDateRange, setCustomDateRange] = useState<{ from?: Date; to?: Date }>({})
  const [showDatePicker, setShowDatePicker] = useState(false)

  // تحميل البيانات عند بدء التشغيل
  useEffect(() => {
    loadInvoices()
  }, [])

  const loadInvoices = async () => {
    setLoading(true)
    try {
      const loadedInvoices = await getAllInvoices()
      setInvoices(loadedInvoices)
      try {
        const dataStats = await calculateStats()
        setStats(dataStats)
      } catch (statsError: any) {
        console.error("Error loading stats:", statsError)
        // لا نوقف التحميل إذا فشلت الإحصائيات
        toast.warning("تم تحميل الفواتير لكن فشل تحميل الإحصائيات")
      }
    } catch (error: any) {
      console.error("Error loading invoices:", error)
      const errorMessage = error?.message || "حدث خطأ أثناء تحميل البيانات"
      toast.error(errorMessage)
      setInvoices([])
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = (id: string) => {
    setInvoiceToDelete(id)
    setDeleteDialogOpen(true)
  }

  const confirmDelete = async () => {
    if (!invoiceToDelete) {
      setDeleteDialogOpen(false)
      return
    }
    
    setLoading(true)
    try {
      await deleteInvoice(invoiceToDelete)
      toast.success("تم حذف الفاتورة بنجاح")
      await loadInvoices()
    } catch (error: any) {
      console.error("Error deleting invoice:", error)
      const errorMessage = error?.message || "فشل حذف الفاتورة"
      toast.error(errorMessage)
    } finally {
      setLoading(false)
      setDeleteDialogOpen(false)
      setInvoiceToDelete(null)
    }
  }

  const handleEdit = (invoice: Invoice) => {
    setEditingInvoice(invoice)
  }

  const handleViewDetails = (invoice: Invoice) => {
    setInvoiceToView(invoice)
    setDetailsDialogOpen(true)
  }

  const handleCopyInvoiceNumber = async (invoiceNumber: string) => {
    try {
      await navigator.clipboard.writeText(invoiceNumber)
      setCopiedInvoiceId(invoiceNumber)
      toast.success("تم نسخ رقم الفاتورة")
      setTimeout(() => setCopiedInvoiceId(null), 2000)
    } catch (error) {
      toast.error("فشل نسخ رقم الفاتورة")
    }
  }

  const handleQuickStatusChange = async (invoice: Invoice, newStatus: "مدفوعة" | "معلقة" | "ملغية") => {
    try {
      setLoading(true)
      await updateInvoice(invoice.id, { status: newStatus })
      toast.success(`تم تغيير حالة الفاتورة إلى ${newStatus}`)
      await loadInvoices()
    } catch (error: any) {
      console.error("Error updating invoice status:", error)
      const errorMessage = error?.message || "فشل تحديث حالة الفاتورة"
      toast.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "مدفوعة":
        return "bg-green-100 text-green-800"
      case "معلقة":
        return "bg-orange-100 text-orange-800"
      case "ملغية":
        return "bg-red-100 text-red-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const filteredInvoices = invoices.filter((invoice) => {
    const matchesSearch =
      invoice.invoiceNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
      invoice.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      invoice.customerPhone.includes(searchTerm)
    const matchesStatus = selectedStatus === "all" || invoice.status === selectedStatus

    // فلترة حسب التاريخ
    let matchesDate = true
    if (dateFilter === "today") {
      const today = new Date().toISOString().split('T')[0]
      matchesDate = invoice.date === today
    } else if (dateFilter === "week") {
      const weekAgo = new Date()
      weekAgo.setDate(weekAgo.getDate() - 7)
      matchesDate = new Date(invoice.date) >= weekAgo
    } else if (dateFilter === "month") {
      const monthAgo = new Date()
      monthAgo.setMonth(monthAgo.getMonth() - 1)
      matchesDate = new Date(invoice.date) >= monthAgo
    } else if (dateFilter === "custom" && customDateRange.from && customDateRange.to) {
      const invoiceDate = new Date(invoice.date)
      matchesDate = invoiceDate >= customDateRange.from && invoiceDate <= customDateRange.to
    }

    return matchesSearch && matchesStatus && matchesDate
  })

  // Pagination
  const totalPages = Math.ceil(filteredInvoices.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const paginatedInvoices = filteredInvoices.slice(startIndex, endIndex)

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1)
  }, [searchTerm, selectedStatus, dateFilter])

  const handlePrint = (invoice: Invoice) => {
    setInvoiceToPrint(invoice)
    setPrintDialogOpen(true)
  }

  const exportToExcel = () => {
    if (filteredInvoices.length === 0) {
      toast.error("لا توجد فواتير للتصدير")
      return
    }

    const headers = [
      "رقم الفاتورة",
      "اسم العميل",
      "رقم الهاتف",
      "التاريخ",
      "الوقت",
      "عدد الأصناف",
      "المجموع الفرعي",
      "الضريبة",
      "الخصم",
      "الإجمالي",
      "الحالة",
      "طريقة الدفع"
    ]

    const csvRows = [
      headers.join(","),
      ...filteredInvoices.map(invoice => [
        invoice.invoiceNumber,
        `"${invoice.customerName}"`,
        invoice.customerPhone,
        invoice.date,
        invoice.time,
        invoice.items.length,
        invoice.subtotal.toFixed(2),
        invoice.tax.toFixed(2),
        invoice.discount.toFixed(2),
        invoice.total.toFixed(2),
        invoice.status,
        invoice.paymentMethod
      ].join(","))
    ]

    const csvContent = csvRows.join("\n")
    const BOM = "\uFEFF"
    const blob = new Blob([BOM + csvContent], { type: "text/csv;charset=utf-8;" })
    const link = document.createElement("a")
    link.href = URL.createObjectURL(blob)
    link.download = `invoices_export_${new Date().toISOString().split('T')[0]}.csv`
    link.click()
    toast.success(`تم تصدير ${filteredInvoices.length} فاتورة بنجاح`)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">المبيعات والفواتير</h1>
          <p className="text-gray-600">
            إدارة المبيعات وإصدار الفواتير مع إمكانية الطباعة والتصدير
            {filteredInvoices.length !== invoices.length && (
              <span className="text-blue-600 font-semibold mr-2">
                ({filteredInvoices.length} من {invoices.length})
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={loadInvoices}
            disabled={loading}
            type="button"
          >
            <RefreshCcw className={`h-4 w-4 ml-2 ${loading ? 'animate-spin' : ''}`} />
            تحديث
          </Button>
          <CreateInvoice
            key={editingInvoice?.id || 'new'}
            invoice={editingInvoice}
            onSaved={() => {
              loadInvoices();
              setEditingInvoice(null);
            }}
          />
        </div>
      </div>

      {/* البحث والفلترة */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder="البحث برقم الفاتورة، اسم العميل، أو رقم الهاتف..."
            className="pr-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <Select value={selectedStatus} onValueChange={setSelectedStatus}>
          <SelectTrigger className="w-full md:w-48">
            <SelectValue placeholder="حالة الفاتورة" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">جميع الحالات</SelectItem>
            <SelectItem value="مدفوعة">مدفوعة</SelectItem>
            <SelectItem value="معلقة">معلقة</SelectItem>
            <SelectItem value="ملغية">ملغية</SelectItem>
          </SelectContent>
        </Select>
        <Select value={dateFilter} onValueChange={(value) => {
          setDateFilter(value)
          if (value !== "custom") {
            setCustomDateRange({})
          }
        }}>
          <SelectTrigger className="w-full md:w-48">
            <SelectValue placeholder="الفترة الزمنية" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">جميع الفترات</SelectItem>
            <SelectItem value="today">اليوم</SelectItem>
            <SelectItem value="week">آخر أسبوع</SelectItem>
            <SelectItem value="month">آخر شهر</SelectItem>
            <SelectItem value="custom">نطاق مخصص</SelectItem>
          </SelectContent>
        </Select>
        {dateFilter === "custom" && (
          <Popover open={showDatePicker} onOpenChange={setShowDatePicker}>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-full md:w-48 justify-start text-right font-normal">
                <CalendarIcon className="mr-2 h-4 w-4" />
                {customDateRange.from && customDateRange.to ? (
                  `${format(customDateRange.from, "yyyy-MM-dd")} - ${format(customDateRange.to, "yyyy-MM-dd")}`
                ) : (
                  "اختر النطاق"
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                initialFocus
                mode="range"
                defaultMonth={customDateRange.from}
                selected={{ from: customDateRange.from, to: customDateRange.to }}
                onSelect={(range) => {
                  if (range?.from && range?.to) {
                    setCustomDateRange({ from: range.from, to: range.to })
                    setShowDatePicker(false)
                  }
                }}
                numberOfMonths={2}
              />
            </PopoverContent>
          </Popover>
        )}
      </div>

      {/* ملخص المبيعات */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">مبيعات اليوم</p>
                <p className="text-2xl font-bold text-green-600">{stats.todaySales.toFixed(2)} ر.س</p>
              </div>
              <div className="bg-green-100 p-2 rounded-lg">
                <DollarSign className="h-5 w-5 text-green-600" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">{stats.todayCount} فاتورة</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">مبيعات الشهر</p>
                <p className="text-2xl font-bold text-blue-600">{stats.monthSales.toFixed(2)} ر.س</p>
              </div>
              <div className="bg-blue-100 p-2 rounded-lg">
                <ShoppingCart className="h-5 w-5 text-blue-600" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">{stats.monthCount} فاتورة</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">فواتير معلقة</p>
                <p className="text-2xl font-bold text-orange-600">{stats.pendingCount}</p>
              </div>
              <div className="bg-orange-100 p-2 rounded-lg">
                <FileText className="h-5 w-5 text-orange-600" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">{stats.pendingAmount.toFixed(2)} ر.س</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">متوسط الفاتورة</p>
                <p className="text-2xl font-bold text-purple-600">{stats.averageInvoice.toFixed(2)} ر.س</p>
              </div>
              <div className="bg-purple-100 p-2 rounded-lg">
                <CalendarIcon className="h-5 w-5 text-purple-600" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">هذا الشهر</p>
          </CardContent>
        </Card>
      </div>

      {/* قائمة الفواتير */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>الفواتير ({filteredInvoices.length})</CardTitle>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={exportToExcel}>
                <Download className="h-4 w-4 ml-2" />
                تصدير Excel
              </Button>
              <Button variant="outline" size="sm" onClick={() => window.print()}>
                <Printer className="h-4 w-4 ml-2" />
                طباعة التقرير
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {loading ? (
              <TableSkeleton rows={5} cols={6} />
            ) : paginatedInvoices.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 text-lg mb-2">لا توجد فواتير</p>
                <p className="text-gray-400 text-sm">
                  {invoices.length === 0
                    ? "ابدأ بإنشاء فاتورة جديدة"
                    : "لا توجد نتائج مطابقة للبحث"}
                </p>
              </div>
            ) : (
              paginatedInvoices.map((invoice) => (
                <div key={invoice.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                        <FileText className="h-6 w-6 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg text-gray-900">{invoice.invoiceNumber}</h3>
                        <div className="flex items-center gap-2 mt-1">
                          <User className="h-4 w-4 text-gray-400" />
                          <span className="text-sm text-gray-600">{invoice.customerName}</span>
                          <span className="text-sm text-gray-400">({invoice.customerPhone})</span>
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <CalendarIcon className="h-4 w-4 text-gray-400" />
                          <span className="text-sm text-gray-500">
                            {invoice.date} - {invoice.time}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="text-left">
                      <Badge className={`mb-2 ${getStatusColor(invoice.status)}`}>{invoice.status}</Badge>
                      <p className="text-2xl font-bold text-green-600">{invoice.total.toFixed(2)} ر.س</p>
                      <p className="text-sm text-gray-500">{invoice.paymentMethod}</p>
                    </div>
                  </div>

                  {/* تفاصيل المنتجات */}
                  <div className="bg-gray-50 rounded-lg p-3 mb-4">
                    <h4 className="font-medium text-gray-900 mb-2">المنتجات:</h4>
                    <div className="space-y-1">
                      {invoice.items.map((item, index) => (
                        <div key={index} className="flex justify-between text-sm">
                          <span>
                            {item.productName} × {item.quantity}
                          </span>
                          <span>{item.total.toFixed(2)} ر.س</span>
                        </div>
                      ))}
                    </div>
                    <div className="border-t pt-2 mt-2">
                      <div className="flex justify-between text-sm">
                        <span>المجموع الفرعي:</span>
                        <span>{invoice.subtotal.toFixed(2)} ر.س</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>الضريبة (15%):</span>
                        <span>{invoice.tax.toFixed(2)} ر.س</span>
                      </div>
                      {invoice.discount > 0 && (
                        <div className="flex justify-between text-sm text-green-600">
                          <span>الخصم:</span>
                          <span>-{invoice.discount.toFixed(2)} ر.س</span>
                        </div>
                      )}
                      <div className="flex justify-between font-semibold border-t pt-1 mt-1">
                        <span>الإجمالي:</span>
                        <span>{invoice.total.toFixed(2)} ر.س</span>
                      </div>
                    </div>
                  </div>

                  {invoice.notes && (
                    <div className="bg-blue-50 rounded-lg p-3 mb-4">
                      <p className="text-sm text-blue-800">
                        <strong>ملاحظات:</strong> {invoice.notes}
                      </p>
                    </div>
                  )}

                  <div className="flex justify-between items-center">
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={() => handleViewDetails(invoice)}>
                        <Eye className="h-4 w-4 ml-1" />
                        تفاصيل
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleEdit(invoice)}>
                        <Edit className="h-4 w-4 ml-1" />
                        تعديل
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handlePrint(invoice)}>
                        <Printer className="h-4 w-4 ml-1" />
                        طباعة
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleCopyInvoiceNumber(invoice.invoiceNumber)}
                      >
                        {copiedInvoiceId === invoice.invoiceNumber ? (
                          <Check className="h-4 w-4 ml-1 text-green-600" />
                        ) : (
                          <Copy className="h-4 w-4 ml-1" />
                        )}
                      </Button>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button size="sm" variant="outline">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() => handleQuickStatusChange(invoice, "مدفوعة")}
                            disabled={invoice.status === "مدفوعة"}
                          >
                            تغيير الحالة إلى مدفوعة
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => handleQuickStatusChange(invoice, "معلقة")}
                            disabled={invoice.status === "معلقة"}
                          >
                            تغيير الحالة إلى معلقة
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => handleQuickStatusChange(invoice, "ملغية")}
                            disabled={invoice.status === "ملغية"}
                          >
                            تغيير الحالة إلى ملغية
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-red-600 hover:text-red-700 bg-transparent"
                      onClick={() => handleDelete(invoice.id)}
                    >
                      <Trash2 className="h-4 w-4 ml-1" />
                      حذف
                    </Button>
                  </div>
                </div>
              )))}
          </div>

          {/* Pagination */}
          {filteredInvoices.length > 0 && (
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
                  من {filteredInvoices.length} فاتورة
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
        </CardContent>
      </Card>

      {/* مربع حوار التأكيد للحذف */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>هل أنت متأكد من حذف الفاتورة؟</AlertDialogTitle>
            <AlertDialogDescription>
              لن يمكنك التراجع عن هذا الإجراء. سيتم حذف الفاتورة بشكل نهائي من النظام.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>إلغاء</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} className="bg-red-600 hover:bg-red-700">
              حذف الفاتورة
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* مربع حوار الطباعة */}
      <PrintInvoice
        invoice={invoiceToPrint}
        open={printDialogOpen}
        onOpenChange={(open) => {
          setPrintDialogOpen(open)
          if (!open) setInvoiceToPrint(null)
        }}
      />

      {/* مربع حوار تفاصيل الفاتورة */}
      <Dialog open={detailsDialogOpen} onOpenChange={setDetailsDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <span>تفاصيل الفاتورة</span>
              {invoiceToView && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleCopyInvoiceNumber(invoiceToView.invoiceNumber)}
                >
                  {copiedInvoiceId === invoiceToView.invoiceNumber ? (
                    <>
                      <Check className="h-4 w-4 ml-1 text-green-600" />
                      تم النسخ
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4 ml-1" />
                      نسخ رقم الفاتورة
                    </>
                  )}
                </Button>
              )}
            </DialogTitle>
          </DialogHeader>
          {invoiceToView && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">رقم الفاتورة</p>
                  <p className="font-semibold">{invoiceToView.invoiceNumber}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">التاريخ والوقت</p>
                  <p className="font-semibold">{invoiceToView.date} - {invoiceToView.time}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">اسم العميل</p>
                  <p className="font-semibold">{invoiceToView.customerName}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">رقم الهاتف</p>
                  <p className="font-semibold">{invoiceToView.customerPhone || "غير محدد"}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">الحالة</p>
                  <Badge className={getStatusColor(invoiceToView.status)}>{invoiceToView.status}</Badge>
                </div>
                <div>
                  <p className="text-sm text-gray-500">طريقة الدفع</p>
                  <p className="font-semibold">{invoiceToView.paymentMethod}</p>
                </div>
              </div>

              <div className="border-t pt-4">
                <h3 className="font-semibold mb-3">المنتجات</h3>
                <div className="space-y-2">
                  {invoiceToView.items.map((item, index) => (
                    <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <div>
                        <p className="font-medium">{item.productName}</p>
                        <p className="text-sm text-gray-500">الكمية: {item.quantity} × {item.price.toFixed(2)} ر.س</p>
                      </div>
                      <p className="font-semibold">{item.total.toFixed(2)} ر.س</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="border-t pt-4 space-y-2">
                <div className="flex justify-between">
                  <span>المجموع الفرعي:</span>
                  <span className="font-semibold">{invoiceToView.subtotal.toFixed(2)} ر.س</span>
                </div>
                <div className="flex justify-between">
                  <span>الضريبة (15%):</span>
                  <span className="font-semibold">{invoiceToView.tax.toFixed(2)} ر.س</span>
                </div>
                {invoiceToView.discount > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>الخصم:</span>
                    <span className="font-semibold">-{invoiceToView.discount.toFixed(2)} ر.س</span>
                  </div>
                )}
                <div className="flex justify-between text-lg font-bold border-t pt-2">
                  <span>الإجمالي:</span>
                  <span className="text-green-600">{invoiceToView.total.toFixed(2)} ر.س</span>
                </div>
              </div>

              {invoiceToView.notes && (
                <div className="border-t pt-4">
                  <p className="text-sm text-gray-500 mb-1">ملاحظات</p>
                  <p className="bg-blue-50 p-3 rounded">{invoiceToView.notes}</p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
