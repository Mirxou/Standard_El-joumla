"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/lib/auth-context"
import { useNotifications } from "@/lib/notifications/notification-context"
import Navigation from "./navigation"
import { Button } from "@/components/ui/button"
import {
  Bell,
  Search,
  Menu,
  Plus,
  ChevronRight,
  LogOut,
  Building2,
  User,
  Settings,
  ChevronDown,
  LayoutDashboard
} from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from "@/components/ui/sheet"
import { format } from "date-fns"
import { arSA } from "date-fns/locale"
import { Badge } from "@/components/ui/badge"

// Components
import ProductsManagement from "@/components/products/products-management"
import CategoriesManagement from "@/components/categories/categories-management"
import InventoryManagement from "@/components/inventory/inventory-management"
import SalesManagement from "@/components/sales/sales-management"
import ProfitReports from "@/components/reports/profit-reports"
import AIForecastDashboard from "@/components/ai/ai-forecast-dashboard"
import AdvancedAnalytics from "@/components/analytics/advanced-analytics"
import WarehouseManagement from "@/components/warehouses/warehouse-management"
import ExpiryTracking from "@/components/inventory/expiry-tracking"
import SupplierManagement from "@/components/suppliers/supplier-management"
import AdvancedReportsPage from "@/components/reports/advanced-reports-page"
import AlertsPage from "@/components/alerts/alerts-page"
import SettingsPage from "@/components/settings/settings-page"
import UsersManagement from "@/components/users/users-management"
import ActivityLog from "@/components/settings/activity-log"
import BackupRestore from "@/components/settings/backup-restore"
import PurchasesManagement from "@/components/purchases/purchases-management"
import ReturnsManagement from "@/components/returns/returns-management"
import ReportsManagement from "@/components/reports/reports-management"
import DashboardHome from "./dashboard-home"

export default function Dashboard() {
  const { user, logout, companies, currentCompany, selectCompany } = useAuth()
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotifications()
  const [activeView, setActiveView] = useState("dashboard")

  // Keyboard shortcuts (Keep existing logic)
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
      }
      if (e.key === 'Escape' && activeView !== 'dashboard') {
        setActiveView('dashboard')
      }
    }
    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [activeView])

  // Content Renderer
  const renderContent = () => {
    switch (activeView) {
      case "products": return <ProductsManagement />
      case "categories": return <CategoriesManagement />
      case "inventory": return <InventoryManagement />
      case "sales": return <SalesManagement />
      case "purchases": return <PurchasesManagement />
      case "returns": return <ReturnsManagement />
      case "reports": return <ReportsManagement />
      case "ai-forecast": return <AIForecastDashboard />
      case "analytics": return <AdvancedAnalytics />
      case "warehouses": return <WarehouseManagement />
      case "expiry": return <ExpiryTracking />
      case "suppliers": return <SupplierManagement />
      case "advanced-reports": return <AdvancedReportsPage />
      case "alerts": return <AlertsPage />
      case "settings": return <SettingsPage />
      case "users": return <UsersManagement />
      case "activity": return <ActivityLog />
      case "backup": return <BackupRestore />
      default: return <DashboardHome setActiveView={setActiveView} />
    }
  }

  return (
    <div className="min-h-screen bg-transparent rtl-grid font-cairo" dir="rtl">

      {/* Sidebar - Desktop (Fixed Column 1) */}
      <aside className="hidden lg:block sticky top-0 h-screen p-2 lg:p-4 overflow-hidden transition-all duration-300">
        <div className="h-full glass-panel rounded-2xl lg:rounded-3xl overflow-hidden flex flex-col relative transition-all duration-300">
          {/* Decor */}
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 to-purple-500" />
          <Navigation activeView={activeView} setActiveView={setActiveView} />
        </div>
      </aside>

      {/* Main Content - (Column 2) */}
      <main className="flex-1 flex flex-col min-w-0 p-2 sm:p-4 lg:pr-0 gap-3 sm:gap-4 lg:gap-6 h-screen overflow-y-auto scroll-smooth">

        {/* Header */}
        <header className="glass-panel mx-0 sm:mx-1 z-40 rounded-xl sm:rounded-2xl sticky top-0 backdrop-blur-xl transition-all duration-300">
          <div className="flex items-center justify-between p-2 sm:p-3 lg:p-4 gap-2 sm:gap-3">

            {/* Mobile Menu */}
            <div className="flex items-center gap-2 sm:gap-3 lg:hidden">
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="ghost" size="icon" className="transition-transform hover:scale-110">
                    <Menu className="h-5 w-5 sm:h-6 sm:w-6 text-white" />
                  </Button>
                </SheetTrigger>
                <SheetContent side="right" className="w-[85vw] sm:w-80 p-0 border-l border-white/10 bg-[#0f172a] transition-all duration-300">
                  <SheetTitle className="sr-only">القائمة الرئيسية</SheetTitle>
                  <Navigation activeView={activeView} setActiveView={setActiveView} />
                </SheetContent>
              </Sheet>
              <span className="text-lg sm:text-xl font-bold text-white">Standard</span>
            </div>

            {/* Search Bar */}
            <div className="hidden md:flex items-center relative flex-1 max-w-md mx-2 lg:mx-4">
              <Search className="absolute right-3 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="بحث سريع (Ctrl + K)..."
                className="w-full bg-white/5 border border-white/10 rounded-lg lg:rounded-xl py-1.5 lg:py-2 pr-10 pl-4 text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all duration-200 placeholder:text-gray-500"
              />
            </div>

            {/* Actions */}
            <div className="flex items-center gap-1.5 sm:gap-2 lg:gap-3">

              {/* Add Menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button className="bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white rounded-lg lg:rounded-xl shadow-lg shadow-cyan-500/20 border-0 transition-all duration-200 hover:scale-105 active:scale-95 text-xs sm:text-sm px-2 sm:px-4">
                    <Plus className="h-4 w-4 sm:h-5 sm:w-5 ml-1 sm:ml-2" />
                    <span className="hidden sm:inline">إضافة جديدة</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="glass-panel border-white/10 text-white">
                  <DropdownMenuItem onClick={() => setActiveView('products')}>منتج جديد</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setActiveView('sales')}>فاتورة مبيعات</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setActiveView('purchases')}>فاتورة مشتريات</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              {/* Notifications */}
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="ghost" size="icon" className="relative text-gray-300 hover:text-white hover:bg-white/10 rounded-xl">
                    <Bell className="h-5 w-5" />
                    {unreadCount > 0 && (
                      <span className="absolute top-2 right-2 h-2.5 w-2.5 rounded-full bg-red-500 animate-pulse ring-2 ring-black" />
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-80 p-0 glass-panel border-white/10" align="end">
                  <div className="p-4 border-b border-white/10">
                    <h4 className="font-semibold text-white">التنبيهات</h4>
                  </div>
                  <ScrollArea className="h-[300px]">
                    {notifications.length === 0 ? (
                      <div className="p-8 text-center text-gray-500">لا توجد تنبيهات جديدة</div>
                    ) : (
                      <div className="divide-y divide-white/5">
                        {notifications.map((notification: any) => (
                          <div key={notification.id} className="p-4 hover:bg-white/5 transition-colors">
                            <p className="text-sm font-medium text-white">{notification.title}</p>
                            <p className="text-xs text-gray-400 mt-1">{notification.message}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </ScrollArea>
                </PopoverContent>
              </Popover>

              <div className="h-8 w-[1px] bg-white/10 mx-1" />

              {/* User Menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="flex items-center gap-2 px-2 hover:bg-white/5 rounded-xl">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-purple-500 p-[1px]">
                      <div className="w-full h-full rounded-[7px] bg-black flex items-center justify-center">
                        <User className="w-4 h-4 text-white" />
                      </div>
                    </div>
                    <div className="hidden md:block text-right">
                      <p className="text-sm font-medium text-white leading-none">{user?.username || 'Admin'}</p>
                      <p className="text-xs text-cyan-400 mt-1">مدير النظام</p>
                    </div>
                    <ChevronDown className="h-4 w-4 text-gray-400" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56 glass-panel border-white/10 text-white" align="end">
                  <DropdownMenuLabel>حسابي</DropdownMenuLabel>
                  <DropdownMenuSeparator className="bg-white/10" />
                  <DropdownMenuItem className="focus:bg-white/10 focus:text-cyan-400">الملف الشخصي</DropdownMenuItem>
                  <DropdownMenuItem className="focus:bg-white/10 focus:text-cyan-400">الإعدادات</DropdownMenuItem>
                  <DropdownMenuSeparator className="bg-white/10" />
                  <DropdownMenuItem onClick={logout} className="text-red-400 focus:text-red-300 focus:bg-red-500/10">
                    تسجيل الخروج
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

            </div>
          </div>
        </header>

        {/* Dynamic Content */}
        <div className="flex-1 glass-panel rounded-xl sm:rounded-2xl lg:rounded-3xl p-3 sm:p-4 lg:p-6 overflow-x-hidden animate-in fade-in slide-in-from-bottom-4 duration-500 transition-all">
          {renderContent()}
        </div>

      </main>
    </div>
  )
}
