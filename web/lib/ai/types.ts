export interface ForecastResult {
  product_id: string
  forecast: Array<{
    day: number
    date: string
    quantity: number
    confidence_lower: number
    confidence_upper: number
  }>
  average_daily_demand: number
  trend_direction: 'increasing' | 'decreasing' | 'stable'
  confidence: 'low' | 'medium' | 'high'
}

export interface StockOptimization {
  product_id: string
  product_name: string
  current_stock: number
  demand_analysis: {
    daily_demand: number
    weekly_demand: number
    monthly_demand: number
    annual_demand: number
  }
  optimization: {
    economic_order_quantity: number
    reorder_point: number
    safety_stock: number
    optimal_order_frequency: string
    orders_per_year: number
  }
  stock_status: {
    status: 'healthy' | 'warning' | 'low' | 'reorder_now'
    days_remaining: number
    should_reorder: boolean
    recommended_order_quantity: number
  }
  cost_analysis: {
    holding_cost_per_unit: number
    ordering_cost: number
    annual_holding_cost: number
    annual_ordering_cost: number
    total_inventory_cost: number
  }
}

export interface ABCAnalysis {
  analysis_period: string
  total_products: number
  total_revenue: number
  categories: {
    A: CategoryData
    B: CategoryData
    C: CategoryData
  }
  recommendations: string[]
}

interface CategoryData {
  count: number
  percent: number
  revenue: number
  revenue_percent: number
  description: string
  products: Array<{
    id: string
    name: string
    name_ar: string
    revenue: number
    units_sold: number
    category: string
  }>
}
