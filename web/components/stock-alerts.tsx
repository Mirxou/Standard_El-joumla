import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AlertTriangle, Package, TrendingDown, Clock } from "lucide-react"

export default function StockAlerts() {
  const alerts = [
    {
      id: 1,
      product: "iPhone 15 Cases",
      category: "Electronics",
      currentStock: 5,
      minStock: 20,
      status: "critical",
      lastUpdated: "2 min ago",
    },
    {
      id: 2,
      product: "Wireless Earbuds",
      category: "Electronics",
      currentStock: 12,
      minStock: 25,
      status: "low",
      lastUpdated: "15 min ago",
    },
    {
      id: 3,
      product: "Phone Chargers",
      category: "Accessories",
      currentStock: 8,
      minStock: 30,
      status: "critical",
      lastUpdated: "1 hour ago",
    },
    {
      id: 4,
      product: "Bluetooth Speakers",
      category: "Electronics",
      currentStock: 18,
      minStock: 25,
      status: "low",
      lastUpdated: "2 hours ago",
    },
    {
      id: 5,
      product: "Power Banks",
      category: "Electronics",
      currentStock: 3,
      minStock: 15,
      status: "critical",
      lastUpdated: "3 hours ago",
    },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case "critical":
        return "bg-red-100 text-red-800 border-red-200"
      case "low":
        return "bg-orange-100 text-orange-800 border-orange-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const getStatusIcon = (status: string) => {
    return status === "critical" ? AlertTriangle : TrendingDown
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Stock Alerts</h1>
          <p className="text-gray-600">Monitor low stock items and critical alerts</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700">
          <Package className="h-4 w-4 mr-2" />
          Reorder All
        </Button>
      </div>

      {/* Alert Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Critical Alerts</p>
                <p className="text-2xl font-bold text-red-600">3</p>
              </div>
              <div className="bg-red-100 p-2 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Low Stock</p>
                <p className="text-2xl font-bold text-orange-600">2</p>
              </div>
              <div className="bg-orange-100 p-2 rounded-lg">
                <TrendingDown className="h-5 w-5 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Items</p>
                <p className="text-2xl font-bold text-blue-600">5</p>
              </div>
              <div className="bg-blue-100 p-2 rounded-lg">
                <Package className="h-5 w-5 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alerts List */}
      <Card>
        <CardHeader>
          <CardTitle>Active Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {alerts.map((alert) => {
              const StatusIcon = getStatusIcon(alert.status)
              return (
                <div key={alert.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-4">
                    <div className={`p-2 rounded-lg ${alert.status === "critical" ? "bg-red-100" : "bg-orange-100"}`}>
                      <StatusIcon
                        className={`h-4 w-4 ${alert.status === "critical" ? "text-red-600" : "text-orange-600"}`}
                      />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">{alert.product}</h3>
                      <p className="text-sm text-gray-500">{alert.category}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className={getStatusColor(alert.status)}>
                          {alert.status.toUpperCase()}
                        </Badge>
                        <span className="text-xs text-gray-400 flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {alert.lastUpdated}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Current: {alert.currentStock}</p>
                    <p className="text-sm text-gray-600">Min: {alert.minStock}</p>
                    <Button size="sm" className="mt-2 bg-blue-600 hover:bg-blue-700">
                      Reorder
                    </Button>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
