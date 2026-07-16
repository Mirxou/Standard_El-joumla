import { NextRequest, NextResponse } from 'next/server'

/**
 * ABC Analysis API Route
 * تصنيف المنتجات حسب أهميتها (Pareto Analysis)
 * 
 * ملاحظة: يجب تحديث هذا الملف ليستدعي backend API بدلاً من supabase
 */

export async function GET(request: NextRequest) {
  try {
    // TODO: استدعاء backend API بدلاً من supabase
    // const response = await apiClient.get('/api/v1/ai/abc-analysis')
    
    // Mock data for development
    const mockProducts = [
      { 
        id: 1, 
        sku: 'SKU001', 
        name: 'Product A',
        name_ar: 'منتج أ',
        selling_price: 100,
        cost_price: 50,
        quantity: 1000,
        revenue: 100000
      },
      { 
        id: 2, 
        sku: 'SKU002', 
        name: 'Product B',
        name_ar: 'منتج ب',
        selling_price: 50,
        cost_price: 25,
        quantity: 500,
        revenue: 25000
      },
      { 
        id: 3, 
        sku: 'SKU003', 
        name: 'Product C',
        name_ar: 'منتج ج',
        selling_price: 20,
        cost_price: 10,
        quantity: 200,
        revenue: 4000
      }
    ]

    // Calculate cumulative revenue
    const sortedProducts = mockProducts
      .sort((a, b) => b.revenue - a.revenue)
    
    const totalRevenue = sortedProducts.reduce((sum, p) => sum + p.revenue, 0)
    let cumulativeRevenue = 0

    // Assign ABC categories (Pareto 80/20)
    const categorizedProducts = sortedProducts.map(product => {
      cumulativeRevenue += product.revenue
      const cumulativePercent = (cumulativeRevenue / totalRevenue) * 100

      let category = 'C'
      if (cumulativePercent <= 80) {
        category = 'A'
      } else if (cumulativePercent <= 95) {
        category = 'B'
      }

      return {
        ...product,
        category,
        revenue_percent: (product.revenue / totalRevenue) * 100,
        cumulative_percent: cumulativePercent
      }
    })

    // Group by category
    const aItems = categorizedProducts.filter(p => p.category === 'A')
    const bItems = categorizedProducts.filter(p => p.category === 'B')
    const cItems = categorizedProducts.filter(p => p.category === 'C')

    return NextResponse.json({
      analysis_period: '90 days',
      total_products: mockProducts.length,
      total_revenue: Math.round(totalRevenue),
      
      categories: {
        A: {
          count: aItems.length,
          percent: Math.round((aItems.length / mockProducts.length) * 100),
          revenue: Math.round(aItems.reduce((sum, p) => sum + p.revenue, 0)),
          revenue_percent: Math.round((aItems.reduce((sum, p) => sum + p.revenue, 0) / totalRevenue) * 100),
          description: 'منتجات عالية القيمة - تتطلب إدارة دقيقة',
          products: aItems.slice(0, 10)
        },
        B: {
          count: bItems.length,
          percent: Math.round((bItems.length / mockProducts.length) * 100),
          revenue: Math.round(bItems.reduce((sum, p) => sum + p.revenue, 0)),
          revenue_percent: Math.round((bItems.reduce((sum, p) => sum + p.revenue, 0) / totalRevenue) * 100),
          description: 'منتجات متوسطة القيمة - مراقبة منتظمة',
          products: bItems.slice(0, 10)
        },
        C: {
          count: cItems.length,
          percent: Math.round((cItems.length / mockProducts.length) * 100),
          revenue: Math.round(cItems.reduce((sum, p) => sum + p.revenue, 0)),
          revenue_percent: Math.round((cItems.reduce((sum, p) => sum + p.revenue, 0) / totalRevenue) * 100),
          description: 'منتجات منخفضة القيمة - مراقبة أساسية',
          products: cItems.slice(0, 10)
        }
      },
      
      recommendations: [
        'ركز على المنتجات من الفئة A - فهي تمثل 80% من الإيرادات',
        'راقب مستويات مخزون الفئة A بعناية لتجنب نفاذ المخزون',
        'فكر في تقليل المخزون من الفئة C أو إيقاف المنتجات بطيئة الحركة'
      ]
    })

  } catch (error: any) {
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    )
  }
}
