"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Input } from "@/components/ui/input"
import {
  Package,
  ShoppingCart,
  TrendingUp,
  AlertTriangle,
  DollarSign,
  BarChart3,
  Bell,
  Search,
  Users,
  Warehouse,
  Calendar,
  Settings,
  FolderTree,
  Loader2,
  RefreshCw,
  Zap,
  ArrowUpRight
} from "lucide-react"
import { API_CONFIG } from "@/lib/config/api"
import { toast } from "sonner"
import type { Category } from "@/lib/database/types"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts"
import { motion } from "framer-motion"
import { dashboardService } from "@/lib/api/services/dashboard"
import { DashboardHomeSkeleton } from "@/components/ui/loading-skeletons"
import { getWebSocketClient } from "@/lib/websocket-client"

interface DashboardHomeProps {
  setActiveView?: (view: string) => void
}

export default function DashboardHome(props: DashboardHomeProps = {} as DashboardHomeProps) {
  const { setActiveView } = props
  const [loading, setLoading] = useState(true)
  const [realTimeData, setRealTimeData] = useState({
    totalRevenue: 0,
    totalProducts: 0,
    lowStockAlerts: 0,
    profitMargin: 0,
    todaySales: 0,
    pendingOrders: 0,
  })
  const [salesChartData, setSalesChartData] = useState<any[]>([])
  const [liveActivities, setLiveActivities] = useState<any[]>([])

  // Initial Data Fetch
  useEffect(() => {
    fetchDashboardData()
    
    // Connect to WebSocket for real-time updates (optional - won't break if fails)
    let wsClient: any = null
    try {
      wsClient = getWebSocketClient('data_updates')
      
      wsClient.on('data_update', (message: any) => {
        if (message.data) {
          // تحديث البيانات عند استقبال تحديثات من Desktop
          if (message.data.type === 'sale' || message.data.type === 'product' || message.data.type === 'inventory') {
            fetchDashboardData()
            
            // إضافة نشاط مباشر جديد
            if (message.data.type === 'sale') {
              setLiveActivities(prev => [{
                title: `فاتورة جديدة #${message.data.id || ''}`,
                time: 'الآن',
                desc: `+ ${message.data.amount || 0} ر.س`,
                isAlert: false
              }, ...prev.slice(0, 4)])
            } else if (message.data.type === 'inventory' && message.data.low_stock) {
              setLiveActivities(prev => [{
                title: `مخزون منخفض: ${message.data.product_name || ''}`,
                time: 'الآن',
                desc: `متبقي ${message.data.current_stock || 0} قطعة`,
                isAlert: true
              }, ...prev.slice(0, 4)])
            }
          }
        }
      })
      
      // محاولة الاتصال بدون إيقاف التطبيق عند الفشل
      wsClient.connect().catch((err: any) => {
        // WebSocket غير متاح - هذا طبيعي إذا كان Backend غير متاح
        console.info("ℹ️ WebSocket غير متاح - سيتم العمل بدون تحديثات مباشرة")
      })
      
    } catch (err) {
      // WebSocket غير متاح - هذا طبيعي
      console.info("ℹ️ WebSocket غير متاح - سيتم العمل بدون تحديثات مباشرة")
    }
    
    return () => {
      if (wsClient) {
        try {
          wsClient.disconnect()
        } catch (e) {
          // تجاهل الأخطاء عند الإغلاق
        }
      }
    }
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const [statsData, chartData] = await Promise.all([
        dashboardService.getStats(),
        dashboardService.getSalesChartData(7)
      ])

      // تحويل بيانات الرسم البياني من API
      if (Array.isArray(chartData) && chartData.length > 0) {
        setSalesChartData(chartData.map((item: any) => ({
          name: item.date || item.name || '',
          value: item.value || item.amount || item.total || 0
        })))
      } else {
        setSalesChartData([])
      }

      setRealTimeData({
        totalRevenue: statsData.total_revenue || statsData.total_sales || 0,
        totalProducts: statsData.products_count || 0,
        lowStockAlerts: statsData.low_stock_count || 0,
        profitMargin: statsData.profit_margin || 0,
        todaySales: statsData.today_sales || 0,
        pendingOrders: statsData.pending_orders || 0,
      })
    } catch (e) {
      console.error("Error fetching dashboard data:", e)
      setSalesChartData([])
      setRealTimeData({
        totalRevenue: 0,
        totalProducts: 0,
        lowStockAlerts: 0,
        profitMargin: 0,
        todaySales: 0,
        pendingOrders: 0,
      })
    } finally {
      setLoading(false)
    }
  }

  const containerAnimations = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  const itemAnimations = {
    hidden: { y: 20, opacity: 0 },
    show: { y: 0, opacity: 1 }
  }

  if (loading) {
    return <DashboardHomeSkeleton />
  }

  return (
    <motion.div
      variants={containerAnimations}
      initial="hidden"
      animate="show"
      className="space-y-8"
    >

      {/* Title & Actions */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">لوحة القيادة</h1>
          <p className="text-gray-400">نظرة عامة على أداء مشروعك اليوم.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="glass-panel border-white/10 hover:bg-white/5 text-gray-300">
            <RefreshCw className="w-4 h-4 mr-2" />
            تحديث
          </Button>
          <Button className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white border-0 shadow-lg shadow-cyan-500/20">
            <Zap className="w-4 h-4 mr-2" />
            تقرير ذكي
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6">
        <StatsCard
          title="إجمالي الإيرادات"
          value={`${realTimeData.totalRevenue.toLocaleString()} ر.س`}
          trend="+12.5%"
          icon={DollarSign}
          color="cyan"
          delay={0.1}
        />
        <StatsCard
          title="المنتجات النشطة"
          value={realTimeData.totalProducts.toString()}
          trend="+4"
          icon={Package}
          color="purple"
          delay={0.2}
        />
        <StatsCard
          title="تنبيهات المخزون"
          value={realTimeData.lowStockAlerts.toString()}
          trend="تحذير"
          isAlert
          icon={AlertTriangle}
          color="orange"
          delay={0.3}
        />
        <StatsCard
          title="مؤشر الأداء"
          value="98.2%"
          trend="+1.2%"
          icon={TrendingUp}
          color="green"
          delay={0.4}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">

        {/* Sales Chart (2 Cols) */}
        <motion.div variants={itemAnimations} className="lg:col-span-2 glass-panel p-3 sm:p-4 lg:p-6 rounded-xl sm:rounded-2xl lg:rounded-3xl relative overflow-hidden transition-all">
          <div className="absolute top-0 right-0 p-6 opacity-10 pointer-events-none">
            <BarChart3 className="w-32 h-32 text-cyan-500" />
          </div>

          <div className="flex items-center justify-between mb-8 relative z-10">
            <h3 className="text-xl font-bold text-white">تحليل المبيعات</h3>
            <div className="flex gap-2">
              <Badge variant="outline" className="border-cyan-500/30 text-cyan-400 bg-cyan-500/10 cursor-pointer">اسبوعي</Badge>
              <Badge variant="outline" className="border-white/10 text-gray-400 hover:bg-white/5 cursor-pointer">شهري</Badge>
            </div>
          </div>

          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={salesChartData}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <YAxis stroke="#64748b" tick={{ fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.05)" />
                <Area type="monotone" dataKey="value" stroke="#06b6d4" strokeWidth={3} fillOpacity={1} fill="url(#colorValue)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Quick Actions & Recent Activity (1 Col) */}
        <motion.div variants={itemAnimations} className="space-y-6">

          {/* Quick Actions */}
          <div className="glass-panel p-3 sm:p-4 lg:p-6 rounded-xl sm:rounded-2xl lg:rounded-3xl transition-all">
            <h3 className="text-base sm:text-lg font-bold text-white mb-3 sm:mb-4">وصول سريع</h3>
            <div className="grid grid-cols-2 gap-2 sm:gap-3 lg:gap-4">
              <ActionButton icon={ShoppingCart} label="بيع جديد" color="bg-green-500" onClick={() => setActiveView?.("sales")} />
              <ActionButton icon={Package} label="إضافة منتج" color="bg-blue-500" onClick={() => setActiveView?.("products")} />
              <ActionButton icon={Users} label="موردين" color="bg-purple-500" onClick={() => setActiveView?.("suppliers")} />
              <ActionButton icon={Settings} label="إعدادات" color="bg-gray-600" onClick={() => setActiveView?.("settings")} />
            </div>
          </div>

          {/* Live Activity */}
          <div className="glass-panel p-3 sm:p-4 lg:p-6 rounded-xl sm:rounded-2xl lg:rounded-3xl transition-all">
            <div className="flex items-center justify-between mb-3 sm:mb-4">
              <h3 className="text-base sm:text-lg font-bold text-white">النشاط المباشر</h3>
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            </div>
            <div className="space-y-2 sm:space-y-3 lg:space-y-4">
              {liveActivities.length === 0 ? (
                <div className="text-center text-gray-400 py-8 text-sm">لا يوجد نشاط مباشر</div>
              ) : (
                liveActivities.map((activity, index) => (
                  <ActivityItem 
                    key={index}
                    title={activity.title} 
                    time={activity.time} 
                    desc={activity.desc} 
                    isAlert={activity.isAlert} 
                  />
                ))
              )}
            </div>
          </div>

        </motion.div>
      </div>

    </motion.div>
  )
}

function StatsCard({ title, value, trend, icon: Icon, color, delay, isAlert }: any) {
  const colors: any = {
    cyan: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
    purple: "text-purple-400 bg-purple-500/10 border-purple-500/20",
    orange: "text-orange-400 bg-orange-500/10 border-orange-500/20",
    green: "text-green-400 bg-green-500/10 border-green-500/20",
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className={`glass-panel p-4 sm:p-5 lg:p-6 rounded-xl sm:rounded-2xl lg:rounded-3xl relative overflow-hidden group hover:-translate-y-1 transition-all duration-300`}
    >
      <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-xl sm:rounded-2xl flex items-center justify-center mb-3 sm:mb-4 ${colors[color]} group-hover:scale-110 transition-transform`}>
        <Icon className="w-5 h-5 sm:w-6 sm:h-6" />
      </div>
      <div>
        <p className="text-gray-400 text-xs sm:text-sm font-medium mb-1">{title}</p>
        <h3 className="text-xl sm:text-2xl font-bold text-white">{value}</h3>
      </div>
      <div className={`absolute top-3 left-3 sm:top-4 sm:left-4 lg:top-6 lg:left-6 text-xs sm:text-sm font-bold flex items-center gap-1 ${isAlert ? 'text-red-400' : 'text-green-400'}`}>
        <span>{trend}</span>
        {!isAlert && <ArrowUpRight className="w-3 h-3 sm:w-4 sm:h-4" />}
      </div>
    </motion.div>
  )
}

function ActionButton({ icon: Icon, label, color, onClick }: any) {
  return (
    <button
      onClick={onClick}
      className="flex flex-col items-center justify-center p-2 sm:p-3 lg:p-4 rounded-xl sm:rounded-2xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all group"
    >
      <div className={`w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center text-white mb-1 sm:mb-2 ${color} shadow-lg group-hover:scale-110 transition-transform`}>
        <Icon className="w-4 h-4 sm:w-5 sm:h-5" />
      </div>
      <span className="text-[10px] sm:text-xs font-medium text-gray-300 group-hover:text-white text-center">{label}</span>
    </button>
  )
}

function ActivityItem({ title, time, desc, isAlert }: any) {
  return (
    <div className="flex items-start gap-2 sm:gap-3 p-2 sm:p-3 rounded-lg sm:rounded-xl hover:bg-white/5 transition-colors">
      <div className={`w-2 h-2 mt-2 rounded-full ${isAlert ? 'bg-red-500' : 'bg-cyan-500'}`} />
      <div className="flex-1">
        <div className="flex justify-between items-start">
          <h4 className="text-sm font-medium text-white">{title}</h4>
          <span className="text-[10px] text-gray-500">{time}</span>
        </div>
        <p className="text-xs text-gray-400 mt-1">{desc}</p>
      </div>
    </div>
  )
}
