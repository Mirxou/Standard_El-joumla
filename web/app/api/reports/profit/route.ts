import { NextResponse } from "next/server"

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const period = searchParams.get("period") || "month"
    const category = searchParams.get("category") || "all"

    // Mock data للأرباح
    const profitData = {
      totalRevenue: 245800,
      totalCost: 147480,
      totalProfit: 98320,
      profitMargin: 40.0,
      previousPeriodProfit: 89650,
      profitGrowth: 9.7,
      categoryBreakdown: [
        {
          name: "المواد الغذائية",
          revenue: 89500,
          cost: 53700,
          profit: 35800,
          margin: 40.0,
          growth: 12.5,
        },
        {
          name: "صحة وجمال",
          revenue: 67200,
          cost: 40320,
          profit: 26880,
          margin: 40.0,
          growth: 8.3,
        },
      ],
      topProducts: [
        {
          name: "زيت الزيتون البكر",
          revenue: 12250,
          profit: 4900,
          margin: 40.0,
          units: 245,
          trend: "up",
        },
      ],
    }

    return NextResponse.json({
      success: true,
      data: profitData,
      period,
      category,
    })
  } catch (error) {
    return NextResponse.json({ success: false, error: "فشل في جلب تقارير الأرباح" }, { status: 500 })
  }
}
