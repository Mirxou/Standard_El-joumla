// AI-Powered Demand Forecasting
// التنبؤ بالطلب باستخدام الذكاء الاصطناعي

import { sql } from '@/lib/db/client'

interface SalesDataPoint {
  date: string
  quantity: number
  revenue: number
}

interface ForecastResult {
  product_id: number
  product_name: string
  current_stock: number
  predicted_demand_7days: number
  predicted_demand_30days: number
  recommended_reorder: number
  confidence_level: 'high' | 'medium' | 'low'
  trend: 'increasing' | 'stable' | 'decreasing'
}

export async function predictDemand(productId: number, days: number = 30): Promise<ForecastResult | null> {
  try {
    // Get historical sales data for the past 90 days
    const historicalData = await sql`
      SELECT 
        DATE(s.invoice_date) as date,
        SUM(i.quantity) as quantity,
        SUM(i.line_total) as revenue
      FROM sales_invoice_items i
      JOIN sales_invoices s ON i.sales_invoice_id = s.id
      WHERE i.product_id = ${productId} 
        AND s.invoice_date >= CURRENT_DATE - INTERVAL '90 days'
        AND s.status = 'confirmed'
      GROUP BY DATE(s.invoice_date)
      ORDER BY date ASC
    `

    if (historicalData.length < 7) {
      // Not enough data for prediction
      return null
    }

    // Get product details
    const product = await sql`SELECT id, name_ar, quantity_in_stock, min_stock_level, reorder_quantity FROM products WHERE id = ${productId}`

    if (!product[0]) return null

    const salesData = historicalData as SalesDataPoint[]
    
    // Calculate simple moving average (SMA) for trend analysis
    const recentData = salesData.slice(-30) // Last 30 days
    const averageDailyDemand = recentData.reduce((sum, d) => sum + Number(d.quantity), 0) / recentData.length

    // Calculate trend using linear regression
    const trend = calculateTrend(salesData)
    
    // Predict demand for next 7 and 30 days
    const predicted_7days = Math.round(averageDailyDemand * 7 * (1 + trend))
    const predicted_30days = Math.round(averageDailyDemand * 30 * (1 + trend))

    // Calculate confidence based on data variance
    const variance = calculateVariance(recentData.map(d => Number(d.quantity)))
    const confidence = variance < 10 ? 'high' : variance < 25 ? 'medium' : 'low'

    // Determine trend direction
    const trendDirection = trend > 0.05 ? 'increasing' : trend < -0.05 ? 'decreasing' : 'stable'

    // Calculate recommended reorder quantity
    const currentStock = Number((product[0] as any).quantity_in_stock)
    const minStock = Number((product[0] as any).min_stock_level)
    const safetyStock = minStock * 1.5 // 50% buffer
    const recommended_reorder = Math.max(0, predicted_30days + safetyStock - currentStock)

    return {
      product_id: productId,
      product_name: (product[0] as any).name_ar,
      current_stock: currentStock,
      predicted_demand_7days: predicted_7days,
      predicted_demand_30days: predicted_30days,
      recommended_reorder: Math.round(recommended_reorder),
      confidence_level: confidence,
      trend: trendDirection
    }
  } catch (error) {
    console.error('[v0] Error in demand forecasting:', error)
    return null
  }
}

export async function predictDemandForAllProducts(): Promise<ForecastResult[]> {
  try {
    const products = await sql`SELECT id FROM products WHERE is_active = true ORDER BY id`

    const forecasts: ForecastResult[] = []

    for (const product of products) {
      const forecast = await predictDemand((product as any).id)
      if (forecast && forecast.predicted_demand_30days > 0) {
        forecasts.push(forecast)
      }
    }

    return forecasts.sort((a, b) => b.recommended_reorder - a.recommended_reorder)
  } catch (error) {
    console.error('[v0] Error forecasting all products:', error)
    return []
  }
}

function calculateTrend(data: SalesDataPoint[]): number {
  if (data.length < 2) return 0

  const n = data.length
  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0

  data.forEach((point, index) => {
    const x = index
    const y = Number(point.quantity)
    sumX += x
    sumY += y
    sumXY += x * y
    sumX2 += x * x
  })

  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX)
  const avgY = sumY / n
  
  return avgY > 0 ? slope / avgY : 0
}

function calculateVariance(data: number[]): number {
  if (data.length === 0) return 0
  
  const mean = data.reduce((sum, val) => sum + val, 0) / data.length
  const squaredDiffs = data.map(val => Math.pow(val - mean, 2))
  const variance = squaredDiffs.reduce((sum, val) => sum + val, 0) / data.length
  
  return Math.sqrt(variance)
}
