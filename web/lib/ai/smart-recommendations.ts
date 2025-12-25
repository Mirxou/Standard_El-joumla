// AI-Powered Smart Recommendations
// توصيات ذكية للأعمال

import { sql } from '@/lib/db/client'
import { predictDemandForAllProducts } from './demand-forecasting'
import { detectAnomalies } from './anomaly-detection'

interface SmartRecommendation {
  id: string
  category: 'reorder' | 'pricing' | 'inventory' | 'sales' | 'alert'
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  action: string
  impact: string
  data?: any
}

export async function getSmartRecommendations(): Promise<SmartRecommendation[]> {
  const recommendations: SmartRecommendation[] = []

  try {
    // Get reorder recommendations
    const reorderRecs = await getReorderRecommendations()
    recommendations.push(...reorderRecs)

    // Get pricing recommendations
    const pricingRecs = await getPricingRecommendations()
    recommendations.push(...pricingRecs)

    // Get inventory optimization recommendations
    const inventoryRecs = await getInventoryOptimizationRecommendations()
    recommendations.push(...inventoryRecs)

    // Get anomaly alerts
    const anomalies = await detectAnomalies()
    anomalies.forEach((anomaly, index) => {
      recommendations.push({
        id: `anomaly-${index}`,
        category: 'alert',
        priority: anomaly.severity === 'high' ? 'high' : anomaly.severity === 'medium' ? 'medium' : 'low',
        title: anomaly.description,
        description: `تم اكتشاف: ${anomaly.type}`,
        action: anomaly.suggested_action,
        impact: `المنتج: ${anomaly.product_name || 'عام'}`,
        data: anomaly
      })
    })

    return recommendations.sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 }
      return priorityOrder[b.priority] - priorityOrder[a.priority]
    })
  } catch (error) {
    console.error('[v0] Error generating smart recommendations:', error)
    return []
  }
}

async function getReorderRecommendations(): Promise<SmartRecommendation[]> {
  const recommendations: SmartRecommendation[] = []

  try {
    const forecasts = await predictDemandForAllProducts()
    
    forecasts.forEach((forecast, index) => {
      if (forecast.recommended_reorder > 0) {
        const urgency = forecast.current_stock < forecast.predicted_demand_7days ? 'high' : 'medium'
        
        recommendations.push({
          id: `reorder-${index}`,
          category: 'reorder',
          priority: urgency,
          title: `إعادة طلب ${forecast.product_name}`,
          description: `المخزون الحالي: ${forecast.current_stock} | الطلب المتوقع (30 يوم): ${forecast.predicted_demand_30days}`,
          action: `طلب ${forecast.recommended_reorder} وحدة`,
          impact: `تجنب نفاذ المخزون واستمرارية المبيعات`,
          data: forecast
        })
      }
    })
  } catch (error) {
    console.error('[v0] Error getting reorder recommendations:', error)
  }

  return recommendations
}

async function getPricingRecommendations(): Promise<SmartRecommendation[]> {
  const recommendations: SmartRecommendation[] = []

  try {
    // Find products with low turnover and high stock
    const slowMovers = await sql`
      SELECT 
        p.id,
        p.name_ar,
        p.selling_price,
        p.quantity_in_stock,
        COALESCE(SUM(i.quantity), 0) as total_sold_30days
      FROM products p
      LEFT JOIN sales_invoice_items i ON p.id = i.product_id
      LEFT JOIN sales_invoices s ON i.sales_invoice_id = s.id 
        AND s.invoice_date >= CURRENT_DATE - INTERVAL '30 days'
        AND s.status = 'confirmed'
      WHERE p.is_active = true
        AND p.quantity_in_stock > p.min_stock_level * 2
      GROUP BY p.id, p.name_ar, p.selling_price, p.quantity_in_stock
      HAVING COALESCE(SUM(i.quantity), 0) < 5
      ORDER BY p.quantity_in_stock DESC
      LIMIT 5
    `

    slowMovers.forEach((product: any, index: number) => {
      recommendations.push({
        id: `pricing-${index}`,
        category: 'pricing',
        priority: 'medium',
        title: `تخفيض سعر ${product.name_ar}`,
        description: `منتج بطيء الحركة: ${product.total_sold_30days} مبيعات في 30 يوم`,
        action: `خفض السعر 10-15% أو عمل عرض ترويجي`,
        impact: `تسريع دوران المخزون وتحرير رأس المال`,
        data: product
      })
    })
  } catch (error) {
    console.error('[v0] Error getting pricing recommendations:', error)
  }

  return recommendations
}

async function getInventoryOptimizationRecommendations(): Promise<SmartRecommendation[]> {
  const recommendations: SmartRecommendation[] = []

  try {
    // Find overstocked items
    const overstocked = await sql`
      SELECT 
        p.id,
        p.name_ar,
        p.quantity_in_stock,
        p.max_stock_level,
        p.unit_cost,
        (p.quantity_in_stock * p.unit_cost) as stock_value
      FROM products p
      WHERE p.is_active = true
        AND p.quantity_in_stock > p.max_stock_level * 1.3
      ORDER BY stock_value DESC
      LIMIT 5
    `

    overstocked.forEach((product: any, index: number) => {
      recommendations.push({
        id: `inventory-${index}`,
        category: 'inventory',
        priority: 'low',
        title: `تحسين مخزون ${product.name_ar}`,
        description: `مخزون زائد: ${product.quantity_in_stock} (الحد الأقصى: ${product.max_stock_level})`,
        action: `إيقاف الطلبات المؤقت وتقليل الحد الأقصى`,
        impact: `تحرير ${Math.round(product.stock_value)} درهم من رأس المال`,
        data: product
      })
    })
  } catch (error) {
    console.error('[v0] Error getting inventory recommendations:', error)
  }

  return recommendations
}
