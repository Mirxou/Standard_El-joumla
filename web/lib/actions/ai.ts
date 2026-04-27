'use server'

// Server Actions for AI Features
// إجراءات الخادم لميزات الذكاء الاصطناعي

import { apiClient } from '@/lib/api/client'
import { API_CONFIG } from '@/lib/config/api'
import { predictDemand, predictDemandForAllProducts } from '@/lib/ai/demand-forecasting'
import { optimizePrice } from '@/lib/ai/price-optimization'
import { detectAnomalies } from '@/lib/ai/anomaly-detection'
import { getSmartRecommendations } from '@/lib/ai/smart-recommendations'
import { logger } from '@/lib/utils/logger'

export async function getDemandForecast(productId: number) {
  try {
    // محاولة جلب من API أولاً
    try {
      const apiData = await apiClient.get<any>(`${API_CONFIG.ENDPOINTS.AI.FORECAST}?product_id=${productId}`)
      if (apiData) return { success: true, data: apiData }
    } catch (apiError) {
      logger.debug('API forecast not available, using local prediction')
    }
    
    // استخدام التنبؤ المحلي كبديل
    const forecast = await predictDemand(productId)
    return { success: true, data: forecast }
  } catch (error) {
    logger.error('[v0] Error in demand forecast:', error)
    return { success: false, error: 'فشل في التنبؤ بالطلب' }
  }
}

export async function getAllDemandForecasts() {
  try {
    const forecasts = await predictDemandForAllProducts()
    return { success: true, data: forecasts }
  } catch (error) {
    logger.error('[v0] Error in demand forecasts:', error)
    return { success: false, error: 'فشل في التنبؤ بالطلب' }
  }
}

export async function getPriceOptimization(productId: number) {
  try {
    const recommendation = await optimizePrice(productId)
    return { success: true, data: recommendation }
  } catch (error) {
    logger.error('[v0] Error in price optimization:', error)
    return { success: false, error: 'فشل في تحسين السعر' }
  }
}

export async function getAnomalyDetection() {
  try {
    // محاولة جلب من API أولاً
    try {
      const apiData = await apiClient.get<any>(API_CONFIG.ENDPOINTS.AI.ANOMALY_DETECTION)
      if (apiData && apiData.anomalies) return { success: true, data: apiData.anomalies }
    } catch (apiError) {
      logger.debug('API anomaly detection not available, using local detection')
    }
    
    // استخدام الكشف المحلي كبديل
    const anomalies = await detectAnomalies()
    return { success: true, data: anomalies }
  } catch (error) {
    logger.error('[v0] Error in anomaly detection:', error)
    return { success: false, error: 'فشل في كشف الشذوذ' }
  }
}

export async function getAIRecommendations() {
  try {
    // محاولة جلب من API أولاً
    try {
      const apiData = await apiClient.get<any>(API_CONFIG.ENDPOINTS.AI.RECOMMENDATIONS)
      if (apiData && apiData.recommendations) return { success: true, data: apiData.recommendations }
    } catch (apiError) {
      logger.debug('API recommendations not available, using local recommendations')
    }
    
    // استخدام التوصيات المحلية كبديل
    const recommendations = await getSmartRecommendations()
    return { success: true, data: recommendations }
  } catch (error) {
    logger.error('[v0] Error in AI recommendations:', error)
    return { success: false, error: 'فشل في جلب التوصيات' }
  }
}
