"use client"

import { Button } from "@/components/ui/button"
import { Home, Package, ShoppingCart, BarChart3, Warehouse, Calendar, Users, Settings, FileText, AlertTriangle, Brain, LineChart, TrendingUp, Activity, Database, FolderTree, Truck, RotateCcw } from 'lucide-react'

interface NavigationProps {
  activeView: string
  setActiveView: (view: string) => void
}

export default function Navigation({ activeView, setActiveView }: NavigationProps) {
  const navItems = [
    { id: "dashboard", label: "لوحة التحكم", icon: Home },
    { id: "products", label: "إدارة المنتجات", icon: Package },
    { id: "categories", label: "إدارة الفئات", icon: FolderTree },
    { id: "inventory", label: "حركات المخزون", icon: Warehouse },
    { id: "sales", label: "المبيعات والفواتير", icon: ShoppingCart },
    { id: "purchases", label: "إدارة المشتريات", icon: Truck },
    { id: "returns", label: "إدارة المرتجعات", icon: RotateCcw },
    { id: "reports", label: "تقارير الأرباح", icon: BarChart3 },
    { id: "ai-forecast", label: "التنبؤ الذكي", icon: Brain },
    { id: "analytics", label: "التحليلات المتقدمة", icon: TrendingUp },
    { id: "suppliers", label: "إدارة الموردين", icon: Users },
    { id: "expiry", label: "تتبع الصلاحية", icon: Calendar },
    { id: "alerts", label: "التنبيهات", icon: AlertTriangle },
    { id: "advanced-reports", label: "التقارير المتقدمة", icon: BarChart3 },
    { id: "users", label: "المستخدمين", icon: Users },
    { id: "activity", label: "سجل النشاطات", icon: Activity },
    { id: "backup", label: "النسخ الاحتياطي", icon: Database },
    { id: "settings", label: "الإعدادات", icon: Settings },
  ]

  return (
    <nav className="p-4 space-y-2" dir="rtl">
      <div className="mb-6 text-center">
        <div className="w-16 h-16 mx-auto mb-3 bg-gradient-to-br from-blue-600 to-green-600 rounded-full flex items-center justify-center">
          <Package className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-lg font-semibold text-gray-900">Standard</h2>
        <p className="text-sm text-gray-500">نظام إدارة المخزون</p>
      </div>

      {navItems.map((item) => {
        const Icon = item.icon
        return (
          <Button
            key={item.id}
            type="button"
            variant={activeView === item.id ? "default" : "ghost"}
            className={`w-full justify-start gap-3 cursor-pointer ${activeView === item.id ? "bg-blue-600 text-white hover:bg-blue-700" : "text-gray-700 hover:bg-gray-100"
              }`}
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              setActiveView(item.id)
            }}
          >
            <Icon className="h-4 w-4" />
            {item.label}
          </Button>
        )
      })}
    </nav>
  )
}
