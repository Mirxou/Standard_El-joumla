"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search, Filter, Package, TrendingUp, TrendingDown, MoreVertical, Edit, Trash2 } from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"

export default function InventoryView() {
  const [searchTerm, setSearchTerm] = useState("")

  const products = [
    {
      id: 1,
      name: "iPhone 15 Pro Cases",
      category: "Electronics",
      sku: "IPH15-CASE-001",
      stock: 45,
      minStock: 20,
      price: 25.99,
      cost: 15.5,
      status: "in-stock",
      lastUpdated: "2 hours ago",
    },
    {
      id: 2,
      name: "Wireless Earbuds",
      category: "Electronics",
      sku: "WE-BT-002",
      stock: 12,
      minStock: 25,
      price: 89.99,
      cost: 45.0,
      status: "low-stock",
      lastUpdated: "1 hour ago",
    },
    {
      id: 3,
      name: "Phone Chargers USB-C",
      category: "Accessories",
      sku: "CHG-USBC-003",
      stock: 8,
      minStock: 30,
      price: 19.99,
      cost: 8.5,
      status: "critical",
      lastUpdated: "30 min ago",
    },
    {
      id: 4,
      name: "Bluetooth Speakers",
      category: "Electronics",
      sku: "BT-SPK-004",
      stock: 23,
      minStock: 15,
      price: 149.99,
      cost: 75.0,
      status: "in-stock",
      lastUpdated: "4 hours ago",
    },
    {
      id: 5,
      name: "Power Banks 10000mAh",
      category: "Electronics",
      sku: "PB-10K-005",
      stock: 3,
      minStock: 15,
      price: 39.99,
      cost: 22.0,
      status: "critical",
      lastUpdated: "1 hour ago",
    },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case "in-stock":
        return "bg-green-100 text-green-800"
      case "low-stock":
        return "bg-orange-100 text-orange-800"
      case "critical":
        return "bg-red-100 text-red-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const getStockIcon = (status: string) => {
    switch (status) {
      case "in-stock":
        return <TrendingUp className="h-3 w-3 text-green-600" />
      case "low-stock":
        return <TrendingDown className="h-3 w-3 text-orange-600" />
      case "critical":
        return <TrendingDown className="h-3 w-3 text-red-600" />
      default:
        return null
    }
  }

  const filteredProducts = products.filter(
    (product) =>
      product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.category.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Inventory</h1>
          <p className="text-gray-600">Manage your product inventory and stock levels</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700">
          <Package className="h-4 w-4 mr-2" />
          Add Product
        </Button>
      </div>

      {/* Search and Filter */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder="Search products, SKU, or category..."
            className="pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <Button variant="outline">
          <Filter className="h-4 w-4 mr-2" />
          Filter
        </Button>
      </div>

      {/* Inventory Summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Total Products</p>
              <p className="text-2xl font-bold text-blue-600">1,247</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">In Stock</p>
              <p className="text-2xl font-bold text-green-600">1,201</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Low Stock</p>
              <p className="text-2xl font-bold text-orange-600">23</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Out of Stock</p>
              <p className="text-2xl font-bold text-red-600">23</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Products List */}
      <Card>
        <CardHeader>
          <CardTitle>Products ({filteredProducts.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredProducts.map((product) => (
              <div key={product.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-4 flex-1">
                  <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                    <Package className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-900 truncate">{product.name}</h3>
                    <p className="text-sm text-gray-500">SKU: {product.sku}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline" className="text-xs">
                        {product.category}
                      </Badge>
                      <Badge className={`text-xs ${getStatusColor(product.status)}`}>
                        {getStockIcon(product.status)}
                        <span className="ml-1">{product.status.replace("-", " ")}</span>
                      </Badge>
                    </div>
                  </div>
                </div>

                <div className="text-right mr-4">
                  <p className="font-medium">${product.price}</p>
                  <p className="text-sm text-gray-500">Stock: {product.stock}</p>
                  <p className="text-xs text-gray-400">Min: {product.minStock}</p>
                </div>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem>
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem className="text-red-600">
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
