"use client"

import {
  Package,
  Home,
  FolderTree,
  Warehouse,
  ShoppingCart,
  Truck,
  RotateCcw,
  BarChart3,
  Brain,
  TrendingUp,
  Users,
  Calendar,
  AlertTriangle,
  Activity,
  Database,
  Settings,
  Zap,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { ScrollArea } from "@/components/ui/scroll-area"

interface NavigationProps {
  activeView: string
  setActiveView: (view: string) => void
}

export default function Navigation({ activeView, setActiveView }: NavigationProps) {
  const navItems = [
    {
      title: "الرئيسية", items: [
        { id: "dashboard", label: "لوحة التحكم", icon: Home },
      ]
    },
    {
      title: "العمليات", items: [
        { id: "sales", label: "المبيعات", icon: ShoppingCart },
        { id: "purchases", label: "المشتريات", icon: Truck },
        { id: "returns", label: "المرتجعات", icon: RotateCcw },
      ]
    },
    {
      title: "المخزون", items: [
        { id: "products", label: "المنتجات", icon: Package },
        { id: "categories", label: "الفئات", icon: FolderTree },
        { id: "warehouses", label: "المستودعات", icon: Warehouse },
        { id: "inventory", label: "حركات المخزون", icon: Database },
        { id: "expiry", label: "الصلاحية", icon: Calendar },
      ]
    },
    {
      title: "الذكاء والتقارير", items: [
        { id: "ai-forecast", label: "التنبؤ الذكي", icon: Brain, badge: "AI" },
        { id: "reports", label: "التقارير", icon: BarChart3 },
        { id: "analytics", label: "التحليلات", icon: TrendingUp },
      ]
    },
    {
      title: "الإدارة", items: [
        { id: "suppliers", label: "الموردين", icon: Users },
        { id: "users", label: "المستخدمين", icon: Users },
        { id: "settings", label: "الإعدادات", icon: Settings },
      ]
    },
  ]

  return (
    <div className="flex flex-col h-full bg-[#0f172a]/50 text-white" dir="rtl">

      {/* Logo Area */}
      <div className="p-6 border-b border-white/5 bg-white/[0.02]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-purple-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Zap className="w-6 h-6 text-white fill-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
              Standard
            </h1>
            <p className="text-xs text-cyan-400 font-medium tracking-wide">V 2.0 Visionary</p>
          </div>
        </div>
      </div>

      {/* Navigation Items */}
      <ScrollArea className="flex-1 py-6 px-3">
        <div className="space-y-8">
          {navItems.map((group, idx) => (
            <div key={idx}>
              <h3 className="px-4 text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-2">
                {group.title}
              </h3>
              <div className="space-y-1">
                {group.items.map((item) => {
                  const Icon = item.icon
                  const isActive = activeView === item.id
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActiveView(item.id)}
                      className={cn(
                        "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300 group relative overflow-hidden",
                        isActive
                          ? "bg-gradient-to-r from-cyan-500/10 to-transparent text-cyan-400 shadow-[inset_3px_0_0_0_#22d3ee]"
                          : "text-gray-400 hover:text-gray-100 hover:bg-white/5"
                      )}
                    >
                      <Icon className={cn(
                        "w-5 h-5 transition-transform duration-300",
                        isActive ? "text-cyan-400 scale-110 drop-shadow-[0_0_8px_rgba(34,211,238,0.5)]" : "group-hover:text-white"
                      )} />

                      <span className="relative z-10">{item.label}</span>

                      {item.badge && (
                        <span className="mr-auto px-1.5 py-0.5 rounded text-[10px] bg-purple-500/20 text-purple-400 border border-purple-500/20">
                          {item.badge}
                        </span>
                      )}

                      {/* Hover effect */}
                      {isActive && (
                        <div className="absolute inset-0 bg-cyan-500/5 animate-pulse-soft" />
                      )}
                    </button>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Footer / User Preview */}
      <div className="p-4 border-t border-white/5 bg-black/20">
        <div className="rounded-xl bg-gradient-to-r from-purple-500/10 to-transparent border border-purple-500/10 p-3 flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.5)]" />
          <span className="text-xs text-purple-300 font-medium">النظام متصل: 12ms</span>
        </div>
      </div>
    </div>
  )
}
