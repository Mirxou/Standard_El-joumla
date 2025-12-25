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
    const sales = await apiClient.get<Sale[]>(API_CONFIG.ENDPOINTS.SALES)
    if (!Array.isArray(sales)) {
      // إذا كانت الاستجابة مختلفة (pagination, etc)
      const salesArray = Array.isArray(sales) ? sales : (sales as any)?.items || []
      return salesArray.map(mapSaleToInvoice)
    }
    return sales.map(mapSaleToInvoice)
  } catch (error) {
    console.error("Error loading invoices from API:", error)
    return []
  }
}

// حفظ فاتورة جديدة عبر API
export async function saveInvoice(invoice: Omit<Invoice, "id" | "invoiceNumber" | "createdAt" | "updatedAt">): Promise<Invoice | null> {
  const payload = {
    customer_id: null, // سيتم تحسينه لاحقاً ليدعم اختيار العميل
    // ملاحظة: الـ SaleManager في الـ Core يدعم customer_name و customer_phone برمجياً
    // لكن الـ SaleCreate Pydantic قد يحتاج لتعديل ليدعمهم مباشرة. 
    // سنستخدم الملاحظات حالياً أو نعتمد على استنتاج الاسم في الـ Backend إذا أمكن.
    sale_date: invoice.date,
    status: invoice.status,
    payment_method: invoice.paymentMethod,
    discount_amount: invoice.discount,
    tax_amount: invoice.tax,
    paid_amount: invoice.status === "مدفوعة" ? invoice.total : 0,
    notes: invoice.notes,
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
    return newSale ? mapSaleToInvoice(newSale) : null
  } catch (error) {
    console.error("Error saving invoice to API:", error)
    return null
  }
}

// تحديث فاتورة موجودة عبر API
export async function updateInvoice(id: string, updates: Partial<Invoice>): Promise<Invoice | null> {
  const payload: any = {}
  if (updates.status) payload.status = updates.status
  if (updates.paymentMethod) payload.payment_method = updates.paymentMethod
  if (updates.notes) payload.notes = updates.notes
  if (updates.discount !== undefined) payload.discount_amount = updates.discount

  try {
    const updatedSale = await apiClient.put<Sale>(`${API_CONFIG.ENDPOINTS.SALES}/${id}`, payload)
    return updatedSale ? mapSaleToInvoice(updatedSale) : null
  } catch (error) {
    console.error("Error updating invoice on API:", error)
    return null
  }
}

// حذف فاتورة عبر API
export async function deleteInvoice(id: string): Promise<boolean> {
  try {
    await apiClient.delete(`${API_CONFIG.ENDPOINTS.SALES}/${id}`)
    return true
  } catch (error) {
    console.error("Error deleting invoice on API:", error)
    return false
  }
}

// الحصول على فاتورة واحدة عبر API
export async function getInvoiceById(id: string): Promise<Invoice | null> {
  try {
    const sale = await apiClient.get<Sale>(`${API_CONFIG.ENDPOINTS.SALES}/${id}`)
    return sale ? mapSaleToInvoice(sale) : null
  } catch (error) {
    console.error("Error getting invoice from API:", error)
    return null
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

    return {
      todaySales: data.today_revenue || 0,
      todayCount: data.today_orders || 0,
      monthSales: data.monthly_revenue || 0,
      monthCount: data.monthly_orders || 0, // تقديري إذا لم يتوفر
      pendingCount: data.pending_orders || 0,
      pendingAmount: 0, // يحتاج إلى endpoint تفصيلي
      averageInvoice: data.monthly_revenue > 0 ? data.monthly_revenue / (data.monthly_orders || 1) : 0
    };
  } catch (error) {
    console.error("Error calculating stats:", error);
    return {
      todaySales: 0,
      todayCount: 0,
      monthSales: 0,
      monthCount: 0,
      pendingCount: 0,
      pendingAmount: 0,
      averageInvoice: 0
    };
  }
}

// وظائف مساعدة بقيت للتوافق ولكن قد لا نحتاجها
export function initializeSampleData(): void { }
export function searchInvoices(query: string): Invoice[] { return [] }
export function filterByStatus(status: string): Invoice[] { return [] }
