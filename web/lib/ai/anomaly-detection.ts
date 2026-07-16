// AI-Powered Anomaly Detection
// كشف الشذوذ والأنماط غير الطبيعية

import { sql } from '@/lib/db/client'

interface Anomaly {
  type: 'unusual_sales_spike' | 'unusual_sales_drop' | 'inventory_discrepancy' | 'pricing_anomaly'
  severity: 'low' | 'medium' | 'high'
  product_id?: number
  product_name?: string
  description: string
  detected_at: Date
  suggested_action: string
}

export async function detectAnomalies(): Promise<Anomaly[]> {
  const anomalies: Anomaly[] = []

  try {
    // Detect unusual sales spikes
    const salesSpikes = await detectSalesSpikes()
    anomalies.push(...salesSpikes)

    // Detect inventory discrepancies
    const inventoryIssues = await detectInventoryDiscrepancies()
    anomalies.push(...inventoryIssues)

    // Detect pricing anomalies
    const pricingIssues = await detectPricingAnomalies()
    anomalies.push(...pricingIssues)

    return anomalies.sort((a, b) => {
      const severityOrder = { high: 3, medium: 2, low: 1 }
      return severityOrder[b.severity] - severityOrder[a.severity]
    })
  } catch (error) {
    console.error('[v0] Error detecting anomalies:', error)
    return []
  }
}

async function detectSalesSpikes(): Promise<Anomaly[]> {
  const anomalies: Anomaly[] = []

  try {
    // Get daily sales for each product in the last 30 days
    const dailySales = await sql`
      SELECT 
        p.id,
        p.name_ar,
        DATE(s.invoice_date) as date,
        SUM(i.quantity) as daily_quantity
      FROM sales_invoice_items i
      JOIN products p ON i.product_id = p.id
      JOIN sales_invoices s ON i.sales_invoice_id = s.id
      WHERE s.invoice_date >= CURRENT_DATE - INTERVAL '30 days'
        AND s.status = 'confirmed'
      GROUP BY p.id, p.name_ar, DATE(s.invoice_date)
    `

    // Group by product
    const productSales = new Map<number, number[]>()
    
    dailySales.forEach((row: any) => {
      if (!productSales.has(row.id)) {
        productSales.set(row.id, [])
      }
      productSales.get(row.id)!.push(Number(row.daily_quantity))
    })

    // Analyze each product for anomalies
    productSales.forEach((quantities, productId) => {
      if (quantities.length < 7) return

      const mean = quantities.reduce((sum, q) => sum + q, 0) / quantities.length
      const stdDev = Math.sqrt(
        quantities.reduce((sum, q) => sum + Math.pow(q - mean, 2), 0) / quantities.length
      )

      const latest = quantities[quantities.length - 1]
      const zScore = stdDev > 0 ? (latest - mean) / stdDev : 0

      if (zScore > 2.5) {
        const product = dailySales.find((row: any) => row.id === productId)
        anomalies.push({
          type: 'unusual_sales_spike',
          severity: zScore > 3 ? 'high' : 'medium',
          product_id: productId,
          product_name: (product as any)?.name_ar || 'منتج غير معروف',
          description: `ارتفاع غير معتاد في المبيعات (${Math.round(zScore * 100)}% فوق المعدل)`,
          detected_at: new Date(),
          suggested_action: 'تحقق من مستويات المخزون وفكر في زيادة الطلبيات'
        })
      } else if (zScore < -2.5 && mean > 5) {
        const product = dailySales.find((row: any) => row.id === productId)
        anomalies.push({
          type: 'unusual_sales_drop',
          severity: 'medium',
          product_id: productId,
          product_name: (product as any)?.name_ar || 'منتج غير معروف',
          description: `انخفاض غير معتاد في المبيعات (${Math.round(Math.abs(zScore) * 100)}% تحت المعدل)`,
          detected_at: new Date(),
          suggested_action: 'راجع الأسعار والمنافسة وجودة المنتج'
        })
      }
    })
  } catch (error) {
    console.error('[v0] Error detecting sales spikes:', error)
  }

  return anomalies
}

async function detectInventoryDiscrepancies(): Promise<Anomaly[]> {
  const anomalies: Anomaly[] = []

  try {
    // Find products with negative stock or unusual stock levels
    const issues = await sql`
      SELECT 
        id,
        name_ar,
        quantity_in_stock,
        min_stock_level,
        max_stock_level
      FROM products
      WHERE is_active = true
        AND (
          quantity_in_stock < 0 
          OR quantity_in_stock > max_stock_level * 1.5
        )
    `

    issues.forEach((product: any) => {
      if (product.quantity_in_stock < 0) {
        anomalies.push({
          type: 'inventory_discrepancy',
          severity: 'high',
          product_id: product.id,
          product_name: product.name_ar,
          description: `مخزون سالب: ${product.quantity_in_stock}`,
          detected_at: new Date(),
          suggested_action: 'راجع حركة المخزون وصحح الأخطاء فوراً'
        })
      } else if (product.quantity_in_stock > product.max_stock_level * 1.5) {
        anomalies.push({
          type: 'inventory_discrepancy',
          severity: 'medium',
          product_id: product.id,
          product_name: product.name_ar,
          description: `مخزون زائد بشكل غير طبيعي: ${product.quantity_in_stock} (الحد الأقصى: ${product.max_stock_level})`,
          detected_at: new Date(),
          suggested_action: 'راجع سياسة الشراء وفكر في عروض ترويجية'
        })
      }
    })
  } catch (error) {
    console.error('[v0] Error detecting inventory discrepancies:', error)
  }

  return anomalies
}

async function detectPricingAnomalies(): Promise<Anomaly[]> {
  const anomalies: Anomaly[] = []

  try {
    // Find products with prices below cost or unusually high margins
    const issues = await sql`
      SELECT 
        id,
        name_ar,
        unit_cost,
        selling_price,
        ROUND(((selling_price - unit_cost) / NULLIF(unit_cost, 0) * 100)::numeric, 2) as margin_percentage
      FROM products
      WHERE is_active = true
        AND (
          selling_price < unit_cost
          OR ((selling_price - unit_cost) / NULLIF(unit_cost, 0)) > 3
        )
    `

    issues.forEach((product: any) => {
      if (product.selling_price < product.unit_cost) {
        anomalies.push({
          type: 'pricing_anomaly',
          severity: 'high',
          product_id: product.id,
          product_name: product.name_ar,
          description: `سعر البيع أقل من التكلفة (خسارة ${product.margin_percentage}%)`,
          detected_at: new Date(),
          suggested_action: 'راجع التسعير فوراً لتجنب الخسائر'
        })
      } else if (product.margin_percentage > 300) {
        anomalies.push({
          type: 'pricing_anomaly',
          severity: 'low',
          product_id: product.id,
          product_name: product.name_ar,
          description: `هامش ربح مرتفع جداً (${product.margin_percentage}%)`,
          detected_at: new Date(),
          suggested_action: 'قد يكون السعر مرتفعاً جداً، راجع المنافسة'
        })
      }
    })
  } catch (error) {
    console.error('[v0] Error detecting pricing anomalies:', error)
  }

  return anomalies
}
