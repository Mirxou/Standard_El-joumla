import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function POST(request: NextRequest) {
  try {
    const { product_id, periods = 30 } = await request.json()

    if (!product_id) {
      return NextResponse.json(
        { error: 'Product ID is required' },
        { status: 400 }
      )
    }

    // Fetch historical sales data
    const { data: salesData, error } = await supabase
      .from('sales_invoice_items')
      .select(`
        quantity,
        created_at,
        sales_invoices!inner(invoice_date)
      `)
      .eq('product_id', product_id)
      .order('created_at', { ascending: true })
      .limit(365) // Last year of data

    if (error) throw error

    // Simple moving average forecast (in production, call Python AI service)
    const forecast = generateSimpleForecast(salesData, periods)

    return NextResponse.json({
      product_id,
      forecast,
      periods,
      data_points: salesData?.length || 0
    })

  } catch (error: any) {
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    )
  }
}

function generateSimpleForecast(historicalData: any[], periods: number) {
  if (!historicalData || historicalData.length === 0) {
    return {
      forecast: Array(periods).fill(0),
      confidence: 'low'
    }
  }

  // Calculate average daily demand
  const totalQuantity = historicalData.reduce((sum, item) => sum + item.quantity, 0)
  const averageDailyDemand = totalQuantity / historicalData.length

  // Generate forecast with slight trend
  const forecast = []
  const trend = 0.02 // 2% growth trend
  
  for (let i = 1; i <= periods; i++) {
    const forecastValue = averageDailyDemand * (1 + trend * i / periods)
    forecast.push({
      day: i,
      date: new Date(Date.now() + i * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      quantity: Math.round(forecastValue),
      confidence_lower: Math.round(forecastValue * 0.8),
      confidence_upper: Math.round(forecastValue * 1.2)
    })
  }

  return {
    forecast,
    average_daily_demand: Math.round(averageDailyDemand),
    trend_direction: 'increasing',
    confidence: historicalData.length > 90 ? 'high' : 'medium'
  }
}
