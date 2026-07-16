import { apiClient } from "@/lib/api/client"
import { API_CONFIG } from "@/lib/config/api"
import type { Sale, Invoice as InvoiceType, InvoiceItem as InvoiceItemType } from "@/lib/types"

// نظام تخزين الفواتير عبر API
export interface InvoiceItem extends InvoiceItemType {
  id: string
}

export interface Invoice extends InvoiceType {
  id: string
  invoiceNumber: string
  customerName: string
  customerPhone: string
  date: string
  time: string
  items: InvoiceItem[]
  subtotal: number
  tax: number
  discount: number
  total: number
  status: "مدفوعة" | "معلقة" | "ملغية" | "paid" | "pending" | "cancelled"
  paymentMethod: string
  notes: string
  createdAt: string
  updatedAt: string
}

/**
 * تحويل من استجابة API إلى نموذج Invoice الخاص بالواجهة
 */
function mapSaleToInvoice(sale: Sale): Invoice {
  return {
    id: sale.id.toString(),
    invoiceNumber: sale.invoice_number,
    customerName: sale.customer_name || "عميل عام",
    customerPhone: sale.customer_phone || "",
    date: sale.sale_date,
    time: sale.created_at ? new Date(sale.created_at).toLocaleTimeString("ar-SA", { hour: "2-digit", minute: "2-digit" }) : "",
    items: (sale.items || []).map((item: InvoiceItemType) => ({
      id: item.id || Math.random().toString(),
      product_id: item.product_id,
      productName: item.productName,
      quantity: item.quantity,
      price: item.price,
      total: item.total,
      unit_price: item.price,
    })),
    subtotal: sale.subtotal,
    tax: sale.tax_amount,
    discount: sale.discount_amount,
    total: sale.total_amount,
    status: mapStatusToArabic(sale.status),
    paymentMethod: sale.payment_method,
    notes: "",
    createdAt: sale.created_at,
    updatedAt: sale.updated_at
  }
}

/**
 * تحويل الحالة من الإنجليزية للعربية
 */
function mapStatusToArabic(status: string): "مدفوعة" | "معلقة" | "ملغية" {
  switch (status.toLowerCase()) {
    case 'paid': return "مدفوعة"
    case 'confirmed':
    case 'pending': return "معلقة"
    case 'cancelled': return "ملغية"
    default: return "معلقة"
  }
}

/**
 * جلب جميع الفواتير من API
 */
export async function getAllInvoices(): Promise<Invoice[]> {
  try {
    const response = await apiClient.get<any>(API_CONFIG.ENDPOINTS.SALES)
    
    // معالجة pagination response
    let sales: Sale[] = []
    if (Array.isArray(response)) {
      sales = response
    } else if (response && typeof response === 'object') {
      // Paginated response
      if (Array.isArray(response.sales)) {
        sales = response.sales
      } else if (Array.isArray(response.items)) {
        sales = response.items
      } else if (Array.isArray(response.data)) {
        sales = response.data
      }
    }
    
    return sales.map(mapSaleToInvoice)
  } catch (error: any) {
    console.error("Error loading invoices from API:", error)
    
    // إعادة رمي الخطأ مع معلومات إضافية
    const errorMessage = error?.message || error?.detail || "فشل تحميل الفواتير"
    throw new Error(`خطأ في تحميل الفواتير: ${errorMessage}`)
  }
}

/**
 * التحقق من صحة بيانات الفاتورة قبل الحفظ
 */
function validateInvoice(invoice: Omit<Invoice, "id" | "invoiceNumber" | "createdAt" | "updatedAt">): string | null {
  if (!invoice.customerName || invoice.customerName.trim() === "") {
    return "اسم العميل مطلوب"
  }
  
  if (!invoice.items || invoice.items.length === 0) {
    return "يجب إضافة منتج واحد على الأقل"
  }
  
  for (const item of invoice.items) {
    if (!item.productName || item.productName.trim() === "") {
      return "اسم المنتج مطلوب لجميع الأصناف"
    }
    if (item.quantity <= 0) {
      return "الكمية يجب أن تكون أكبر من صفر"
    }
    if (item.price < 0) {
      return "السعر لا يمكن أن يكون سالباً"
    }
  }
  
  if (invoice.total < 0) {
    return "المجموع الإجمالي لا يمكن أن يكون سالباً"
  }
  
  return null
}

// حفظ فاتورة جديدة عبر API
export async function saveInvoice(invoice: Omit<Invoice, "id" | "invoiceNumber" | "createdAt" | "updatedAt">): Promise<Invoice | null> {
  // التحقق من صحة البيانات
  const validationError = validateInvoice(invoice)
  if (validationError) {
    throw new Error(validationError)
  }
  
  // تحويل الحالة من العربية إلى الإنجليزية
  const mapStatusToEnglish = (status: string): string => {
    switch (status) {
      case "مدفوعة": return "paid"
      case "معلقة": return "pending"
      case "ملغية": return "cancelled"
      default: return status
    }
  }
  
  const payload = {
    customer_id: null, // سيتم تحسينه لاحقاً ليدعم اختيار العميل
    sale_date: invoice.date,
    status: mapStatusToEnglish(invoice.status),
    payment_method: invoice.paymentMethod,
    discount_amount: invoice.discount,
    tax_amount: invoice.tax,
    paid_amount: invoice.status === "مدفوعة" || invoice.status === "paid" ? invoice.total : 0,
    notes: invoice.notes || "",
    items: invoice.items.map(item => ({
      product_id: item.product_id || 1, // معرف افتراضي إذا لم يتوفر
      quantity: item.quantity,
      unit_price: item.price,
      discount_amount: 0,
      tax_amount: 0
    }))
  }

  try {
    const newSale = await apiClient.post<Sale>(API_CONFIG.ENDPOINTS.SALES, payload)
    if (!newSale) {
      throw new Error("لم يتم إنشاء الفاتورة - استجابة فارغة من الخادم")
    }
    return mapSaleToInvoice(newSale)
  } catch (error: any) {
    console.error("Error saving invoice to API:", error)
    const errorMessage = error?.message || error?.detail || "فشل حفظ الفاتورة"
    throw new Error(`خطأ في حفظ الفاتورة: ${errorMessage}`)
  }
}

// تحديث فاتورة موجودة عبر API
export async function updateInvoice(id: string, updates: Partial<Invoice>): Promise<Invoice | null> {
  if (!id || id.trim() === "") {
    throw new Error("معرف الفاتورة مطلوب للتحديث")
  }
  
  // تحويل الحالة من العربية إلى الإنجليزية
  const mapStatusToEnglish = (status: string): string => {
    switch (status) {
      case "مدفوعة": return "paid"
      case "معلقة": return "pending"
      case "ملغية": return "cancelled"
      default: return status
    }
  }
  
  const payload: any = {}
  if (updates.status) {
    payload.status = mapStatusToEnglish(updates.status)
  }
  if (updates.paymentMethod) {
    payload.payment_method = updates.paymentMethod
  }
  if (updates.notes !== undefined) {
    payload.notes = updates.notes || ""
  }
  if (updates.discount !== undefined) {
    payload.discount_amount = updates.discount
  }
  if (updates.tax !== undefined) {
    payload.tax_amount = updates.tax
  }
  if (updates.total !== undefined) {
    payload.total_amount = updates.total
  }

  try {
    const updatedSale = await apiClient.put<Sale>(`${API_CONFIG.ENDPOINTS.SALES}/${id}`, payload)
    if (!updatedSale) {
      throw new Error("لم يتم تحديث الفاتورة - استجابة فارغة من الخادم")
    }
    return mapSaleToInvoice(updatedSale)
  } catch (error: any) {
    console.error("Error updating invoice on API:", error)
    const errorMessage = error?.message || error?.detail || "فشل تحديث الفاتورة"
    throw new Error(`خطأ في تحديث الفاتورة: ${errorMessage}`)
  }
}

// حذف فاتورة عبر API
export async function deleteInvoice(id: string): Promise<boolean> {
  if (!id || id.trim() === "") {
    throw new Error("معرف الفاتورة مطلوب للحذف")
  }
  
  try {
    await apiClient.delete(`${API_CONFIG.ENDPOINTS.SALES}/${id}`)
    return true
  } catch (error: any) {
    console.error("Error deleting invoice on API:", error)
    const errorMessage = error?.message || error?.detail || "فشل حذف الفاتورة"
    throw new Error(`خطأ في حذف الفاتورة: ${errorMessage}`)
  }
}

// الحصول على فاتورة واحدة عبر API
export async function getInvoiceById(id: string): Promise<Invoice | null> {
  if (!id || id.trim() === "") {
    throw new Error("معرف الفاتورة مطلوب")
  }
  
  try {
    const sale = await apiClient.get<Sale>(`${API_CONFIG.ENDPOINTS.SALES}/${id}`)
    if (!sale) {
      return null
    }
    return mapSaleToInvoice(sale)
  } catch (error: any) {
    console.error("Error getting invoice from API:", error)
    
    // إذا كان الخطأ 404، الفاتورة غير موجودة
    if (error?.status === 404) {
      return null
    }
    
    const errorMessage = error?.message || error?.detail || "فشل جلب الفاتورة"
    throw new Error(`خطأ في جلب الفاتورة: ${errorMessage}`)
  }
}

// حساب الإحصائيات (من الـ API مباشرة)
export interface InvoiceStats {
  todaySales: number
  todayCount: number
  monthSales: number
  monthCount: number
  pendingCount: number
  pendingAmount: number
  averageInvoice: number
}

export async function calculateStats(): Promise<InvoiceStats> {
  try {
    const data = await apiClient.get<any>(API_CONFIG.ENDPOINTS.DASHBOARD.STATS);

    const todaySales = data.today_revenue || data.today_sales || 0
    const todayCount = data.today_orders || data.today_count || 0
    const monthSales = data.monthly_revenue || data.month_sales || 0
    const monthCount = data.monthly_orders || data.month_count || 0
    const pendingCount = data.pending_orders || data.pending_count || 0
    const pendingAmount = data.pending_amount || data.pending_revenue || 0

    return {
      todaySales: Number(todaySales),
      todayCount: Number(todayCount),
      monthSales: Number(monthSales),
      monthCount: Number(monthCount),
      pendingCount: Number(pendingCount),
      pendingAmount: Number(pendingAmount),
      averageInvoice: monthCount > 0 ? monthSales / monthCount : 0
    };
  } catch (error: any) {
    console.error("Error calculating stats:", error);
    
    // في حالة فشل API، نحسب الإحصائيات محلياً من الفواتير المحملة
    try {
      const invoices = await getAllInvoices()
      const today = new Date().toISOString().split('T')[0]
      const monthStart = new Date()
      monthStart.setDate(1)
      
      const todayInvoices = invoices.filter(inv => inv.date === today)
      const monthInvoices = invoices.filter(inv => new Date(inv.date) >= monthStart)
      const pendingInvoices = invoices.filter(inv => inv.status === "معلقة" || inv.status === "pending")
      
      return {
        todaySales: todayInvoices.reduce((sum, inv) => sum + inv.total, 0),
        todayCount: todayInvoices.length,
        monthSales: monthInvoices.reduce((sum, inv) => sum + inv.total, 0),
        monthCount: monthInvoices.length,
        pendingCount: pendingInvoices.length,
        pendingAmount: pendingInvoices.reduce((sum, inv) => sum + inv.total, 0),
        averageInvoice: monthInvoices.length > 0 
          ? monthInvoices.reduce((sum, inv) => sum + inv.total, 0) / monthInvoices.length 
          : 0
      }
    } catch (fallbackError) {
      console.error("Error in fallback stats calculation:", fallbackError)
      return {
        todaySales: 0,
        todayCount: 0,
        monthSales: 0,
        monthCount: 0,
        pendingCount: 0,
        pendingAmount: 0,
        averageInvoice: 0
      }
    }
  }
}

// وظائف مساعدة بقيت للتوافق ولكن قد لا نحتاجها
export function initializeSampleData(): void { }
export function searchInvoices(query: string): Invoice[] { return [] }
export function filterByStatus(status: string): Invoice[] { return [] }
