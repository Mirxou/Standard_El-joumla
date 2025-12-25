'use server'

// Server Actions for AI Features
// إجراءات الخادم لميزات الذكاء الاصطناعي

import { predictDemand, predictDemandForAllProducts } from '@/lib/ai/demand-forecasting'
import { optimizePrice } from '@/lib/ai/price-optimization'
import { detectAnomalies } from '@/lib/ai/anomaly-detection'
import { getSmartRecommendations } from '@/lib/ai/smart-recommendations'

export async function getDemandForecast(productId: number) {
  try {
    const forecast = await predictDemand(productId)
    return { success: true, data: forecast }
  } catch (error) {
    console.error('[v0] Error in demand forecast:', error)
    return { success: false, error: 'فشل في التنبؤ بالطلب' }
  }
}

export async function getAllDemandForecasts() {
  try {
    const forecasts = await predictDemandForAllProducts()
    return { success: true, data: forecasts }
  } catch (error) {
    console.error('[v0] Error in demand forecasts:', error)
    return { success: false, error: 'فشل في التنبؤ بالطلب' }
  }
}

export async function getPriceOptimization(productId: number) {
  try {
    const recommendation = await optimizePrice(productId)
    return { success: true, data: recommendation }
  } catch (error) {
    console.error('[v0] Error in price optimization:', error)
    return { success: false, error: 'فشل في تحسين السعر' }
  }
}

export async function getAnomalyDetection() {
  try {
    const anomalies = await detectAnomalies()
    return { success: true, data: anomalies }
  } catch (error) {
    console.error('[v0] Error in anomaly detection:', error)
    return { success: false, error: 'فشل في كشف الشذوذ' }
  }
}

export async function getAIRecommendations() {
  try {
    const recommendations = await getSmartRecommendations()
    return { success: true, data: recommendations }
  } catch (error) {
    console.error('[v0] Error in AI recommendations:', error)
    return { success: false, error: 'فشل في جلب التوصيات' }
  }
}
