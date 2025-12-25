import { NextRequest, NextResponse } from 'next/server'

/**
 * Stock Optimization API Route
 * تحسين المخزون باستخدام Economic Order Quantity (EOQ)
 * 
 * ملاحظة: يجب تحديث هذا الملف ليستدعي backend API بدلاً من mock data
 */

export async function POST(request: NextRequest) {
  try {
    const { product_id } = await request.json()

    if (!product_id) {
      return NextResponse.json(
        { error: 'Product ID is required' },
        { status: 400 }
      )
    }

    // TODO: استدعاء backend API بدلاً من mock data
    // const response = await apiClient.post('/api/v1/ai/stock-optimize', { product_id })
    
    // Mock data for development
    const mockProduct = {
      id: product_id,
      name: 'Sample Product',
      cost_price: 100,
      current_stock: 200,
      min_stock: 50
    }

    const salesData = [
      { quantity: 50, created_at: new Date() },
      { quantity: 60, created_at: new Date() },
      { quantity: 55, created_at: new Date() }
    ]

    // Calculate metrics
    const totalSold = salesData.reduce((sum: number, item: any) => sum + item.quantity, 0)
    const daysInPeriod = 90
    const dailyDemand = totalSold / daysInPeriod
    const annualDemand = dailyDemand * 365

    const orderingCost = 100 // Default: 100 SAR per order
    const holdingCostPercent = 0.20 // 20% of product cost
    const holdingCostPerUnit = mockProduct.cost_price * holdingCostPercent

    const eoq = Math.sqrt((2 * annualDemand * orderingCost) / holdingCostPerUnit)
    const numberOfOrders = annualDemand / eoq
    const daysBetweenOrders = 365 / numberOfOrders

    // Reorder Point Calculation
    const leadTimeDays = 7 // Default: 7 days lead time
    const safetyStock = dailyDemand * 3 // 3 days of safety stock
    const reorderPoint = (dailyDemand * leadTimeDays) + safetyStock

    // Stock Status (using mock data)
    const currentStock = mockProduct.current_stock
    const minStock = mockProduct.min_stock
    const daysOfStockRemaining = currentStock / dailyDemand
    
    let stockStatus = 'healthy'
    if (currentStock <= reorderPoint) {
      stockStatus = 'reorder_now'
    } else if (currentStock <= minStock) {
      stockStatus = 'low'
    } else if (daysOfStockRemaining < 7) {
      stockStatus = 'warning'
    }

    return NextResponse.json({
      product_id,
      product_name: mockProduct.name,
      current_stock: currentStock,
      
      demand_analysis: {
        daily_demand: Math.round(dailyDemand * 10) / 10,
        weekly_demand: Math.round(dailyDemand * 7),
        monthly_demand: Math.round(dailyDemand * 30),
        annual_demand: Math.round(annualDemand)
      },
      
      optimization: {
        economic_order_quantity: Math.round(eoq),
        reorder_point: Math.round(reorderPoint),
        safety_stock: Math.round(safetyStock),
        optimal_order_frequency: `كل ${Math.round(daysBetweenOrders)} يوم`,
        orders_per_year: Math.round(numberOfOrders)
      },
      
      stock_status: {
        status: stockStatus,
        days_remaining: Math.round(daysOfStockRemaining),
        should_reorder: currentStock <= reorderPoint,
        recommended_order_quantity: Math.round(eoq)
      },
      
      cost_analysis: {
        holding_cost_per_unit: Math.round(holdingCostPerUnit * 100) / 100,
        ordering_cost: orderingCost,
        annual_holding_cost: Math.round((eoq / 2) * holdingCostPerUnit),
        annual_ordering_cost: Math.round(numberOfOrders * orderingCost),
        total_inventory_cost: Math.round(
          (eoq / 2) * holdingCostPerUnit + numberOfOrders * orderingCost
        )
      }
    })

  } catch (error: any) {
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    )
  }
}
