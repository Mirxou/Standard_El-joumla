"use client"

import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Bell, Plus, Menu, Package, ShoppingCart, FileText, Users, Box, LogOut, User, ChevronDown, Building2 } from 'lucide-react'
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator, DropdownMenuLabel } from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { useAuth } from "@/lib/auth-context"
import Navigation from "@/components/navigation"
import InventoryManagement from "@/components/inventory-management"
import SalesManagement from "@/components/sales-management"
import ProfitReports from "@/components/profit-reports"
import WarehouseManagement from "@/components/warehouse-management"
import ExpiryTracking from "@/components/expiry-tracking"
import SupplierManagement from "@/components/supplier-management"
import AdvancedReports from "@/components/advanced-reports"
import DashboardHome from "@/components/dashboard-home"
import AIInsights from "@/components/ai-insights"
import AdvancedAnalytics from "@/components/advanced-analytics"
import AIForecastDashboard from "@/components/ai-forecast-dashboard"
import ProductsManagement from "@/components/products-management"
import CategoriesManagement from "@/components/categories-management"
import AlertsPage from "@/components/alerts-page"
import AdvancedReportsPage from "@/components/advanced-reports-page"
import SettingsPage from "@/components/settings-page"
import UsersManagement from "@/components/users-management"
import ActivityLog from "@/components/activity-log"
import BackupRestore from "@/components/backup-restore"
import PurchasesManagement from "@/components/purchases-management"
import ReturnsManagement from "@/components/returns-management"
import ReportsManagement from "@/components/reports-management"
import AIForecast from "@/components/ai-forecast"

export default function Dashboard() {
  const { user, logout, companies, currentCompany, selectCompany } = useAuth()
  const [activeView, setActiveView] = useState("dashboard")
  const [showNotifications, setShowNotifications] = useState(false)
  const [showAddMenu, setShowAddMenu] = useState(false)

  const renderContent = () => {
    switch (activeView) {
      case "products":
        return <ProductsManagement />
      case "categories":
        return <CategoriesManagement />
      case "inventory":
        return <InventoryManagement />
      case "sales":
        return <SalesManagement />
      case "profit-reports":
        return <ProfitReports />
      case "ai-forecast-dashboard":
        return <AIForecastDashboard />
      case "analytics":
        return <AdvancedAnalytics />
      case "warehouses":
        return <WarehouseManagement />
      case "expiry":
        return <ExpiryTracking />
      case "suppliers":
        return <SupplierManagement />
      case "advanced-reports":
        return <AdvancedReportsPage />
      case "alerts":
        return <AlertsPage />
      case "settings":
        return <SettingsPage />
      case "users":
        return <UsersManagement />
      case "activity":
        return <ActivityLog />
      case "backup":
        return <BackupRestore />
      case "purchases":
        return <PurchasesManagement />
      case "returns":
        return <ReturnsManagement />
      case "reports":
        return <ReportsManagement />
      case "ai-forecast":
        return <AIForecast />
      default:
        return <DashboardHome setActiveView={setActiveView} />
    }
  }

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      {/* الهيدر */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="md:hidden">
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-64 p-0">
                <Navigation activeView={activeView} setActiveView={setActiveView} />
              </SheetContent>
            </Sheet>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <div className="flex items-center gap-3 cursor-pointer hover:bg-gray-100 p-2 rounded-lg transition-colors">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-green-600 rounded-lg flex items-center justify-center">
                    <Building2 className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h1 className="text-xl font-bold text-gray-900">{currentCompany?.name || "Standard"}</h1>
                      <ChevronDown className="h-4 w-4 text-gray-500" />
                    </div>
                    <p className="text-xs text-blue-600 font-semibold">
                      الشركة المختارة
                    </p>
                  </div>
                </div>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-64">
                <DropdownMenuLabel>الشركات المتاحة</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {companies.map((company) => (
                  <DropdownMenuItem
                    key={company.id}
                    onClick={() => selectCompany(company)}
                    className="cursor-pointer justify-between"
                  >
                    <span className={currentCompany?.id === company.id ? "font-bold" : ""}>
                      {company.name}
                    </span>
                    {company && <Badge variant="secondary" className="text-xs">مختارة</Badge>}
                  </DropdownMenuItem>
                ))}
                {companies.length === 0 && (
                  <div className="p-2 text-sm text-gray-500">لا توجد شركات أخرى</div>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          <div className="flex items-center gap-2">
            {/* زر التنبيهات */}
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="ghost" size="icon" className="relative cursor-pointer" type="button">
                  <Bell className="h-5 w-5" />
                  <Badge className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs bg-red-500">
                    5
                  </Badge>
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80" align="end">
                <div className="space-y-3">
                  <h3 className="font-semibold text-gray-900">التنبيهات</h3>
                  <div className="space-y-2">
                    <div className="p-3 bg-red-50 rounded-lg border border-red-100">
                      <p className="text-sm font-medium text-red-900">مخزون حرج</p>
                      <p className="text-xs text-red-700">سماعات بلوتوث - متبقي 8 وحدات</p>
                    </div>
                    <div className="p-3 bg-orange-50 rounded-lg border border-orange-100">
                      <p className="text-sm font-medium text-orange-900">قرب الانتهاء</p>
                      <p className="text-xs text-orange-700">شوكولاتة - تنتهي 2024-08-20</p>
                    </div>
                    <div className="p-3 bg-blue-50 rounded-lg border border-blue-100">
                      <p className="text-sm font-medium text-blue-900">طلبية جديدة</p>
                      <p className="text-xs text-blue-700">فاتورة #1234 - 450 ر.س</p>
                    </div>
                  </div>
                  <Button variant="outline" className="w-full" size="sm" onClick={() => setActiveView('alerts')}>
                    عرض جميع التنبيهات
                  </Button>
                </div>
              </PopoverContent>
            </Popover>

            {/* قائمة المستخدم */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="gap-2">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-blue-100 text-blue-600 text-sm font-semibold">
                      {user?.name?.split(" ").slice(0, 2).map(n => n[0]).join("") || "AM"}
                    </AvatarFallback>
                  </Avatar>
                  <div className="text-right hidden lg:block">
                    <p className="text-sm font-semibold text-gray-900">{user?.name || "أحمد محمد"}</p>
                    <p className="text-xs text-gray-500">{user?.role || "مدير النظام"}</p>
                  </div>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <div className="px-2 py-3 border-b">
                  <p className="text-sm font-semibold text-gray-900">{user?.name || "أحمد محمد"}</p>
                  <p className="text-xs text-gray-500">{user?.email || "admin@standard.com"}</p>
                </div>
                <DropdownMenuItem onClick={() => setActiveView('settings')} className="cursor-pointer">
                  <User className="h-4 w-4 ml-2" />
                  الملف الشخصي
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setActiveView('settings')} className="cursor-pointer">
                  <Package className="h-4 w-4 ml-2" />
                  الإعدادات
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout} className="cursor-pointer text-red-600">
                  <LogOut className="h-4 w-4 ml-2" />
                  تسجيل الخروج
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* زر إضافة جديد */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button size="sm" className="bg-blue-600 hover:bg-blue-700 cursor-pointer" type="button">
                  <Plus className="h-4 w-4 ml-1" />
                  إضافة جديد
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={() => setActiveView('products')} className="cursor-pointer">
                  <Package className="h-4 w-4 ml-2" />
                  منتج جديد
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setActiveView('sales')} className="cursor-pointer">
                  <ShoppingCart className="h-4 w-4 ml-2" />
                  فاتورة بيع
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setActiveView('inventory')} className="cursor-pointer">
                  <Box className="h-4 w-4 ml-2" />
                  حركة مخزون
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => setActiveView('suppliers')} className="cursor-pointer">
                  <Users className="h-4 w-4 ml-2" />
                  مورد جديد
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* الشريط الجانبي للديسكتوب */}
        <div className="hidden md:block w-64 bg-white border-l border-gray-200 min-h-screen">
          <Navigation activeView={activeView} setActiveView={setActiveView} />
        </div>

        {/* المحتوى الرئيسي */}
        <main className="flex-1 p-6">{renderContent()}</main>
      </div>
    </div>
  )
}
