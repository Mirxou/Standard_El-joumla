'use server'

import { apiClient } from '@/lib/api/client'
import { API_CONFIG } from '@/lib/config/api'
import { revalidatePath } from 'next/cache'
import { logger } from '@/lib/utils/logger'

// تعريف شكل المنتج كما يأتي من البايثون
export interface Product {
  id: number
  name: string
  sku: string
  price: number
  stock: number
  category?: string
  description?: string
  status?: 'active' | 'draft' | 'archived'
}

/**
 * جلب المنتجات من خلال Python API
 */
export async function getProducts(
  search: string = '',
  offset: number = 0
): Promise<{ products: Product[]; totalProducts: number }> {
  try {
    // نجلب البيانات من السيرفر المحلي باستخدام المسار الصحيح
    const rawData = await apiClient.get<any>(API_CONFIG.ENDPOINTS.PRODUCTS)

    // تحويل البيانات وتأمينها في حال كانت فارغة
    const allProducts = Array.isArray(rawData) ? rawData : []

    // بما أن البايثون حالياً يرجع كل شيء، نقوم بالفلترة هنا مؤقتاً
    // (لاحقاً سننقل الفلترة للسيرفر)
    const filteredProducts = search
      ? allProducts.filter((p: any) =>
        (p.name || '').toLowerCase().includes(search.toLowerCase()) ||
        (p.sku || '').toLowerCase().includes(search.toLowerCase())
      )
      : allProducts

    return {
      products: filteredProducts,
      totalProducts: filteredProducts.length,
    }
  } catch (error) {
    logger.error('Failed to fetch products:', error)
    return { products: [], totalProducts: 0 }
  }
}

// --- دوال التعديل (سنقوم بتفعيلها لاحقاً) ---
// حالياً نضعها بشكل صوري لكي ينجح الـ Build دون أخطاء

export async function createProduct(data: any) {
  logger.warn('Create Product: بانتظار تفعيل API POST')
  return { success: false, message: "Server read-only for now" }
}

export async function updateProduct(id: number, data: any) {
  logger.warn('Update Product: بانتظار تفعيل API PUT')
  revalidatePath('/dashboard/products')
  return { success: false }
}

export async function deleteProduct(id: number) {
  logger.warn('Delete Product: بانتظار تفعيل API DELETE')
  revalidatePath('/dashboard/products')
  return { success: false }
}
