'use server'

import { fetchFromAPI } from '@/lib/db/client'
import { revalidatePath } from 'next/cache'

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
    // محاكاة الاتصال مؤقتاً
    // const rawData = await fetchFromAPI('/sales')
    return []
  } catch (error) {
    console.error('Failed to fetch sales invoices:', error)
    return []
  }
}

export async function createSalesInvoice(
  invoice: any,
  items: any[]
): Promise<any> {
  console.log('🚧 Create Sales Invoice: بانتظار تفعيل API POST')
  return { id: 0, invoice_number: 'MOCK-001' }
}

export async function getSalesInvoiceWithItems(id: number) {
  console.log('🚧 Get Invoice Details: بانتظار تفعيل API GET')
  return {
    invoice: null,
    items: []
  }
}

export async function updateInvoiceStatus(
  id: number,
  status: string,
  payment_status?: string
): Promise<void> {
  console.log('🚧 Update Invoice Status: بانتظار تفعيل API PUT')
  revalidatePath('/dashboard/sales')
}
