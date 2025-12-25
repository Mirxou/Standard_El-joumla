'use server'

import { fetchFromAPI } from '@/lib/db/client'
import { revalidatePath } from 'next/cache'

// تعريف مؤقت لشكل فاتورة الشراء
export interface PurchaseOrder {
  id: number
  supplierName: string
  date: string
  total: number
  status: 'pending' | 'completed' | 'cancelled'
  items: any[]
}

/**
 * جلب أوامر الشراء (حالياً يرجع قائمة فارغة حتى نربطها بالبايثون)
 */
export async function getPurchaseOrders(
  search: string = '',
  offset: number = 0
) {
  try {
    // محاكاة الاتصال (أو استبدله بـ fetchFromAPI('/purchases') لاحقاً)
    return {
      purchases: [],
      totalPurchases: 0,
    }
  } catch (error) {
    console.error('Failed to fetch purchase orders:', error)
    return { purchases: [], totalPurchases: 0 }
  }
}

export async function createPurchaseOrder(data: any) {
  console.log('🚧 Create Purchase: بانتظار تفعيل API')
  return { success: false, message: "Not implemented yet" }
}

export async function updatePurchaseOrderStatus(id: number, status: string) {
  console.log('🚧 Update Purchase Status: بانتظار تفعيل API')
  revalidatePath('/dashboard/purchases')
  return { success: false }
}
