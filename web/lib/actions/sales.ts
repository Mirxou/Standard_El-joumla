'use server'

import { API_CONFIG, getFullURL, getDefaultHeaders } from '@/lib/config/api'
import { revalidatePath } from 'next/cache'

// Server-side API client for Next.js Server Actions
async function serverApiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = getFullURL(endpoint)
  const headers = getDefaultHeaders()
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...headers,
      ...(options.headers || {}),
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || error.message || `HTTP error! status: ${response.status}`)
  }

  if (response.status === 204) {
    return { success: true } as T
  }

  return await response.json()
}

export interface SalesInvoice {
  id: number
  invoice_number: string
  customer_name?: string
  date: string
  total_amount: number
  status: 'draft' | 'pending' | 'paid' | 'cancelled'
  payment_status: 'unpaid' | 'partial' | 'paid'
}

export async function getSalesInvoices(filters?: {
  customer_id?: number
  status?: string
  date_from?: string
  date_to?: string
}): Promise<SalesInvoice[]> {
  try {
    const params = new URLSearchParams()
    if (filters?.customer_id) params.append('customer_id', filters.customer_id.toString())
    if (filters?.status) params.append('status', filters.status)
    if (filters?.date_from) params.append('start_date', filters.date_from)
    if (filters?.date_to) params.append('end_date', filters.date_to)
    
    const queryString = params.toString()
    const endpoint = `${API_CONFIG.ENDPOINTS.SALES}${queryString ? `?${queryString}` : ''}`
    
    const response = await serverApiRequest<any>(endpoint)
    const sales = Array.isArray(response) ? response : (response as any)?.sales || (response as any)?.items || []
    
    return sales.map((sale: any) => ({
      id: sale.id,
      invoice_number: sale.invoice_number,
      customer_name: sale.customer_name,
      date: sale.sale_date || sale.date,
      total_amount: sale.total_amount || sale.total,
      status: sale.status,
      payment_status: sale.payment_status || 'unpaid'
    }))
  } catch (error) {
    console.error('Failed to fetch sales invoices:', error)
    return []
  }
}

export async function createSalesInvoice(
  invoice: any,
  items: any[]
): Promise<any> {
  try {
    const payload = {
      customer_id: invoice.customer_id || null,
      sale_date: invoice.date || new Date().toISOString().split('T')[0],
      status: invoice.status || 'pending',
      payment_method: invoice.payment_method || 'cash',
      discount_amount: invoice.discount_amount || 0,
      tax_amount: invoice.tax_amount || 0,
      paid_amount: invoice.paid_amount || 0,
      notes: invoice.notes || '',
      items: items.map(item => ({
        product_id: item.product_id,
        quantity: item.quantity,
        unit_price: item.unit_price || item.price,
        discount_amount: item.discount_amount || 0,
        tax_amount: item.tax_amount || 0
      }))
    }
    
    const result = await serverApiRequest<any>(API_CONFIG.ENDPOINTS.SALES, {
      method: 'POST',
      body: JSON.stringify(payload)
    })
    
    revalidatePath('/dashboard/sales')
    return result
  } catch (error: any) {
    console.error('Failed to create sales invoice:', error)
    throw new Error(error.message || 'فشل إنشاء الفاتورة')
  }
}

export async function getSalesInvoiceWithItems(id: number) {
  try {
    const sale = await serverApiRequest<any>(`${API_CONFIG.ENDPOINTS.SALES}/${id}`)
    
    return {
      invoice: {
        id: sale.id,
        invoice_number: sale.invoice_number,
        customer_name: sale.customer_name,
        date: sale.sale_date || sale.date,
        total_amount: sale.total_amount || sale.total,
        status: sale.status,
        payment_status: sale.payment_status || 'unpaid'
      },
      items: sale.items || []
    }
  } catch (error: any) {
    console.error('Failed to get sales invoice:', error)
    if (error.status === 404) {
      return { invoice: null, items: [] }
    }
    throw new Error(error.message || 'فشل جلب تفاصيل الفاتورة')
  }
}

export async function updateInvoiceStatus(
  id: number,
  status: string,
  payment_status?: string
): Promise<void> {
  try {
    const payload: any = { status }
    if (payment_status) {
      payload.payment_status = payment_status
    }
    
    await serverApiRequest(`${API_CONFIG.ENDPOINTS.SALES}/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    })
    
    revalidatePath('/dashboard/sales')
  } catch (error: any) {
    console.error('Failed to update invoice status:', error)
    throw new Error(error.message || 'فشل تحديث حالة الفاتورة')
  }
}
