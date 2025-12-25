// AI-Powered Price Optimization
// تحسين الأسعار باستخدام الذكاء الاصطناعي

import { sql } from '@/lib/db/client'

interface PriceRecommendation {
  product_id: number
  product_name: string
  current_price: number
  recommended_price: number
  expected_revenue_increase: number
  price_elasticity: number
  competitor_avg_price?: number
  recommendation_reason: string
}

export async function optimizePrice(productId: number): Promise<PriceRecommendation | null> {
  try {
    // Get product details
    const product = await sql`SELECT id, name_ar, selling_price, unit_cost, quantity_in_stock 
       FROM products WHERE id = ${productId}`

    if (!product[0]) return null

    const currentPrice = Number((product[0] as any).selling_price)
    const unitCost = Number((product[0] as any).unit_cost)
    const minPrice = unitCost * 1.15 // Minimum 15% profit margin

    // Get sales history at different price points
    const salesHistory = await sql`
      SELECT 
        i.unit_price,
        SUM(i.quantity) as total_quantity,
        SUM(i.line_total) as total_revenue,
        COUNT(DISTINCT s.id) as transaction_count
      FROM sales_invoice_items i
      JOIN sales_invoices s ON i.sales_invoice_id = s.id
      WHERE i.product_id = ${productId} 
        AND s.invoice_date >= CURRENT_DATE - INTERVAL '90 days'
        AND s.status = 'confirmed'
      GROUP BY i.unit_price
      ORDER BY i.unit_price
    `

    if (salesHistory.length < 2) {
      // Not enough price variation data, use cost-plus pricing
      const recommendedPrice = unitCost * 1.35 // 35% markup
      return {
        product_id: productId,
        product_name: (product[0] as any).name_ar,
        current_price: currentPrice,
        recommended_price: Math.round(recommendedPrice * 100) / 100,
        expected_revenue_increase: ((recommendedPrice - currentPrice) / currentPrice) * 100,
        price_elasticity: 0,
        recommendation_reason: 'توصية بناء على هامش ربح مثالي 35%'
      }
    }

    // Calculate price elasticity
    const elasticity = calculatePriceElasticity(salesHistory)

    // Find optimal price point
    let optimalPrice = currentPrice
    let maxRevenue = 0

    // Test different price points
    for (let price = minPrice; price <= currentPrice * 1.5; price += 0.5) {
      const predictedQuantity = predictQuantityAtPrice(price, currentPrice, elasticity, salesHistory)
      const predictedRevenue = price * predictedQuantity
      
      if (predictedRevenue > maxRevenue) {
        maxRevenue = predictedRevenue
        optimalPrice = price
      }
    }

    // Calculate expected revenue increase
    const currentQuantity = salesHistory.reduce((sum, row: any) => sum + Number(row.total_quantity), 0)
    const currentRevenue = currentPrice * currentQuantity
    const revenueIncrease = ((maxRevenue - currentRevenue) / currentRevenue) * 100

    let reason = ''
    if (optimalPrice > currentPrice) {
      reason = 'يمكن زيادة السعر لتحسين الإيرادات بسبب المرونة السعرية المنخفضة'
    } else if (optimalPrice < currentPrice) {
      reason = 'يُنصح بتخفيض السعر لزيادة الكميات المباعة والإيرادات الإجمالية'
    } else {
      reason = 'السعر الحالي مثالي بناء على تحليل البيانات'
    }

    return {
      product_id: productId,
      product_name: (product[0] as any).name_ar,
      current_price: currentPrice,
      recommended_price: Math.round(optimalPrice * 100) / 100,
      expected_revenue_increase: Math.round(revenueIncrease * 100) / 100,
      price_elasticity: Math.round(elasticity * 100) / 100,
      recommendation_reason: reason
    }
  } catch (error) {
    console.error('[v0] Error in price optimization:', error)
    return null
  }
}

function calculatePriceElasticity(salesHistory: any[]): number {
  if (salesHistory.length < 2) return -1

  const sortedData = salesHistory.sort((a, b) => Number(a.unit_price) - Number(b.unit_price))
  
  let totalElasticity = 0
  let count = 0

  for (let i = 1; i < sortedData.length; i++) {
    const price1 = Number(sortedData[i - 1].unit_price)
    const price2 = Number(sortedData[i].unit_price)
    const qty1 = Number(sortedData[i - 1].total_quantity)
    const qty2 = Number(sortedData[i].total_quantity)

    if (price1 > 0 && qty1 > 0 && price2 !== price1) {
      const priceChange = (price2 - price1) / price1
      const qtyChange = (qty2 - qty1) / qty1
      const elasticity = qtyChange / priceChange
      
      totalElasticity += elasticity
      count++
    }
  }

  return count > 0 ? totalElasticity / count : -1
}

function predictQuantityAtPrice(
  newPrice: number,
  currentPrice: number,
  elasticity: number,
  salesHistory: any[]
): number {
  const totalQuantity = salesHistory.reduce((sum, row) => sum + Number(row.total_quantity), 0)
  const avgQuantity = totalQuantity / salesHistory.length

  const priceChange = (newPrice - currentPrice) / currentPrice
  const quantityChange = elasticity * priceChange
  
  return Math.max(0, avgQuantity * (1 + quantityChange))
}
