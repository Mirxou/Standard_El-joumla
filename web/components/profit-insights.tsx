import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { TrendingUp, TrendingDown, DollarSign, BarChart3, Target, Calendar } from "lucide-react"

export default function ProfitInsights() {
  const topProducts = [
    {
      name: "Wireless Earbuds",
      revenue: 4580,
      profit: 2290,
      margin: 50,
      units: 51,
      trend: "up",
    },
    {
      name: "Bluetooth Speakers",
      revenue: 3750,
      profit: 1875,
      margin: 50,
      units: 25,
      trend: "up",
    },
    {
      name: "Phone Cases",
      revenue: 2890,
      profit: 1156,
      margin: 40,
      units: 112,
      trend: "down",
    },
    {
      name: "Power Banks",
      revenue: 2340,
      profit: 1053,
      margin: 45,
      units: 58,
      trend: "up",
    },
  ]

  const monthlyData = [
    { month: "Jan", revenue: 18500, profit: 7400 },
    { month: "Feb", revenue: 22300, profit: 8920 },
    { month: "Mar", revenue: 24580, profit: 9832 },
    { month: "Apr", revenue: 21200, profit: 8480 },
    { month: "May", revenue: 26800, profit: 10720 },
    { month: "Jun", revenue: 24580, profit: 9832 },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Profit Insights</h1>
          <p className="text-gray-600">Track your profitability and business performance</p>
        </div>
        <Button variant="outline">
          <Calendar className="h-4 w-4 mr-2" />
          This Month
        </Button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Revenue</p>
                <p className="text-2xl font-bold text-green-600">$24,580</p>
              </div>
              <div className="bg-green-100 p-2 rounded-lg">
                <DollarSign className="h-5 w-5 text-green-600" />
              </div>
            </div>
            <div className="flex items-center mt-2">
              <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
              <span className="text-xs text-green-500">+12.5% from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Profit</p>
                <p className="text-2xl font-bold text-blue-600">$9,832</p>
              </div>
              <div className="bg-blue-100 p-2 rounded-lg">
                <Target className="h-5 w-5 text-blue-600" />
              </div>
            </div>
            <div className="flex items-center mt-2">
              <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
              <span className="text-xs text-green-500">+8.2% from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Profit Margin</p>
                <p className="text-2xl font-bold text-purple-600">40.0%</p>
              </div>
              <div className="bg-purple-100 p-2 rounded-lg">
                <BarChart3 className="h-5 w-5 text-purple-600" />
              </div>
            </div>
            <div className="flex items-center mt-2">
              <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
              <span className="text-xs text-green-500">+2.1% from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Units Sold</p>
                <p className="text-2xl font-bold text-orange-600">1,247</p>
              </div>
              <div className="bg-orange-100 p-2 rounded-lg">
                <TrendingUp className="h-5 w-5 text-orange-600" />
              </div>
            </div>
            <div className="flex items-center mt-2">
              <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
              <span className="text-xs text-green-500">+15.3% from last month</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Monthly Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {monthlyData.map((data, index) => (
              <div key={data.month} className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 text-sm font-medium text-gray-600">{data.month}</div>
                  <div className="flex-1">
                    <div className="flex justify-between text-sm mb-1">
                      <span>Revenue: ${data.revenue.toLocaleString('en-US')}</span>
                      <span>Profit: ${data.profit.toLocaleString('en-US')}</span>
                    </div>
                    <Progress value={(data.profit / data.revenue) * 100} className="h-2" />
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{((data.profit / data.revenue) * 100).toFixed(1)}%</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Top Performing Products */}
      <Card>
        <CardHeader>
          <CardTitle>Top Performing Products</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {topProducts.map((product, index) => (
              <div key={product.name} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-sm font-bold text-blue-600">#{index + 1}</span>
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">{product.name}</h3>
                    <p className="text-sm text-gray-500">{product.units} units sold</p>
                  </div>
                </div>

                <div className="text-right">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium">${product.profit.toLocaleString('en-US')}</span>
                    {product.trend === "up" ? (
                      <TrendingUp className="h-3 w-3 text-green-500" />
                    ) : (
                      <TrendingDown className="h-3 w-3 text-red-500" />
                    )}
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {product.margin}% margin
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Profit Goals */}
      <Card>
        <CardHeader>
          <CardTitle>Monthly Goals</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Revenue Goal</span>
                <span>$24,580 / $30,000</span>
              </div>
              <Progress value={82} className="h-3" />
              <p className="text-xs text-gray-500 mt-1">82% of monthly goal achieved</p>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Profit Goal</span>
                <span>$9,832 / $12,000</span>
              </div>
              <Progress value={82} className="h-3" />
              <p className="text-xs text-gray-500 mt-1">82% of monthly goal achieved</p>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Units Goal</span>
                <span>1,247 / 1,500</span>
              </div>
              <Progress value={83} className="h-3" />
              <p className="text-xs text-gray-500 mt-1">83% of monthly goal achieved</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
