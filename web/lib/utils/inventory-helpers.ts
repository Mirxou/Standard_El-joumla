// مساعدات لإدارة المنتجات والمخزون
// Product and Inventory Management Helpers

export interface ProductFormData {
  name: string
  sku: string
  barcode?: string
  category?: string
  buyPrice?: number
  sellPrice: number
  stock: number
  minStock?: number
  maxStock?: number
  warehouse?: string
  supplier?: string
  expiryDate?: string
  batchNumber?: string
  notes?: string
}

// توليد SKU تلقائي
export function generateSKU(category: string = 'PROD'): string {
  const timestamp = Date.now().toString().slice(-6)
  const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0')
  return `${category.toUpperCase()}-${timestamp}${random}`
}

// التحقق من صحة البيانات
export function validateProductData(data: Partial<ProductFormData>): {
  valid: boolean
  errors: string[]
} {
  const errors: string[] = []

  if (!data.name || data.name.trim().length === 0) {
    errors.push('اسم المنتج مطلوب')
  }

  if (!data.sku || data.sku.trim().length === 0) {
    errors.push('رمز SKU مطلوب')
  }

  if (data.sellPrice === undefined || data.sellPrice <= 0) {
    errors.push('سعر البيع يجب أن يكون أكبر من صفر')
  }

  if (data.buyPrice && data.sellPrice && data.buyPrice > data.sellPrice) {
    errors.push('سعر الشراء لا يمكن أن يكون أكبر من سعر البيع')
  }

  if (data.stock !== undefined && data.stock < 0) {
    errors.push('الكمية لا يمكن أن تكون سالبة')
  }

  if (data.minStock && data.maxStock && data.minStock > data.maxStock) {
    errors.push('الحد الأدنى لا يمكن أن يكون أكبر من الحد الأقصى')
  }

  return {
    valid: errors.length === 0,
    errors
  }
}

// حساب هامش الربح
export function calculateProfitMargin(buyPrice: number, sellPrice: number): number {
  if (buyPrice === 0) return 0
  return ((sellPrice - buyPrice) / buyPrice) * 100
}

// تنسيق السعر
export function formatPrice(price: number): string {
  return `${price.toFixed(2)} ر.س`
}

// تنسيق التاريخ
export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('ar-SA', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// التحقق من قرب انتهاء الصلاحية
export function checkExpiryStatus(expiryDate: string): {
  status: 'expired' | 'expiring-soon' | 'valid'
  daysRemaining: number
} {
  const today = new Date()
  const expiry = new Date(expiryDate)
  const diffTime = expiry.getTime() - today.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays < 0) {
    return { status: 'expired', daysRemaining: diffDays }
  } else if (diffDays <= 30) {
    return { status: 'expiring-soon', daysRemaining: diffDays }
  } else {
    return { status: 'valid', daysRemaining: diffDays }
  }
}

// حالة المخزون
export function getStockStatus(stock: number, minStock: number): 'critical' | 'low' | 'normal' {
  if (stock === 0) return 'critical'
  if (stock <= minStock) return 'low'
  return 'normal'
}

// تصدير البيانات إلى CSV
export function exportToCSV(data: any[], filename: string) {
  if (data.length === 0) return

  const headers = Object.keys(data[0])
  const csvContent = [
    headers.join(','),
    ...data.map(row => headers.map(header => {
      const value = row[header]
      return typeof value === 'string' && value.includes(',') 
        ? `"${value}"` 
        : value
    }).join(','))
  ].join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`
  link.click()
}

// بيانات وهمية للتجربة (عند عدم وجود قاعدة بيانات)
export const mockProducts = [
  {
    id: 1,
    name: 'زيت الزيتون البكر',
    sku: 'FOOD-001',
    barcode: '1234567890123',
    category: 'مواد غذائية',
    buyPrice: 25.5,
    sellPrice: 35.99,
    stock: 45,
    minStock: 20,
    status: 'normal'
  },
  {
    id: 2,
    name: 'شامبو الأطفال',
    sku: 'HEALTH-002',
    barcode: '2345678901234',
    category: 'صحة وجمال',
    buyPrice: 15.0,
    sellPrice: 22.99,
    stock: 12,
    minStock: 25,
    status: 'low'
  }
]

// إشعارات النجاح/الفشل
import { toast } from 'sonner'

export function showToast(message: string, type: 'success' | 'error' | 'info' = 'info') {
  switch (type) {
    case 'success':
      toast.success(message)
      break
    case 'error':
      toast.error(message)
      break
    default:
      toast.info(message)
  }
}
