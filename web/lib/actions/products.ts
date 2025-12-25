'use server'

import { fetchFromAPI } from '@/lib/db/client'
import { revalidatePath } from 'next/cache'

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
    // نجلب البيانات من السيرفر المحلي
    const rawData = await fetchFromAPI('/products')

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
    console.error('Failed to fetch products:', error)
    return { products: [], totalProducts: 0 }
  }
}

// --- دوال التعديل (سنقوم بتفعيلها لاحقاً) ---
// حالياً نضعها بشكل صوري لكي ينجح الـ Build دون أخطاء

export async function createProduct(data: any) {
  console.log('🚧 Create Product: بانتظار تفعيل API POST')
  return { success: false, message: "Server read-only for now" }
}

export async function updateProduct(id: number, data: any) {
  console.log('🚧 Update Product: بانتظار تفعيل API PUT')
  revalidatePath('/dashboard/products')
  return { success: false }
}

export async function deleteProduct(id: number) {
  console.log('🚧 Delete Product: بانتظار تفعيل API DELETE')
  revalidatePath('/dashboard/products')
  return { success: false }
}
