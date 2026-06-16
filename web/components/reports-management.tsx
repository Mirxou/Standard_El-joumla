"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Progress } from "@/components/ui/progress"
import { TrendingUp, TrendingDown, DollarSign, BarChart3, Target, Download, Package, FileText, Calendar, Settings, Plus } from "lucide-react"
import { apiClient } from "@/lib/api/client"
import { API_CONFIG } from "@/lib/config/api"
import { toast } from "sonner"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    BarChart,
    Bar
} from "recharts"

export default function ReportsManagement() {
    const [loading, setLoading] = useState(true)
    const [financialData, setFinancialData] = useState<any>(null)
    const [salesTrends, setSalesTrends] = useState<any[]>([])
    const [topProducts, setTopProducts] = useState<any[]>([])
    const [inventoryStats, setInventoryStats] = useState<any>(null)
    const [period, setPeriod] = useState("30")
    const [reportTemplates, setReportTemplates] = useState<any[]>([])
    const [scheduledReports, setScheduledReports] = useState<any[]>([])
    const [showTemplateDialog, setShowTemplateDialog] = useState(false)
    const [showExportDialog, setShowExportDialog] = useState(false)
    const [exportFormat, setExportFormat] = useState("pdf")

    useEffect(() => {
        loadReports()
    }, [period])

    const loadReports = async () => {
        try {
            setLoading(true)

            // Fetch all reports in parallel
            const [financial, trends, products, inventory, templates, scheduled] = await Promise.all([
                apiClient.get(`/api/v1/reports/financial?period=${period}`).catch(() => null),
                apiClient.get(`/api/v1/reports/charts/sales?days=${period}`).catch(() => []),
                apiClient.get(`/api/v1/reports/charts/top-products?period=${period}`).catch(() => []),
                apiClient.get(`/api/v1/reports/analytics/inventory`).catch(() => null),
                apiClient.get(`/api/v1/reports/templates`).catch(() => []),
                apiClient.get(`/api/v1/reports/scheduled`).catch(() => [])
            ])

            setFinancialData(financial)
            setSalesTrends(trends)
            setTopProducts(products)
            setInventoryStats(inventory)
            setReportTemplates(Array.isArray(templates) ? templates : [])
            setScheduledReports(Array.isArray(scheduled) ? scheduled : [])

        } catch (e) {
            console.error("Failed to load reports", e)
            toast.error("فشل تحميل التقارير")
        } finally {
            setLoading(false)
        }
    }

    const handleExport = async (format: string) => {
        try {
            const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/reports/export?format=${format}&period=${period}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
                },
            })
            const blob = await response.blob()
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `report_${new Date().toISOString().split('T')[0]}.${format === 'excel' ? 'xlsx' : format}`
            document.body.appendChild(a)
            a.click()
            window.URL.revokeObjectURL(url)
            document.body.removeChild(a)
            
            toast.success(`تم تصدير التقرير بنجاح`)
            setShowExportDialog(false)
        } catch (error) {
            console.error("Failed to export report", error)
            toast.error("فشل تصدير التقرير")
        }
    }

    if (loading) {
        return <div className="p-8 text-center text-gray-500">جاري تحميل البيانات...</div>
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">التقارير والتحليلات</h1>
                    <p className="text-gray-600">نظرة شاملة على أداء المتجر والمبيعات</p>
                </div>
                <div className="flex gap-2">
                    <Select value={period} onValueChange={setPeriod}>
                        <SelectTrigger className="w-32 glass-panel border-white/10 text-white">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="7">آخر 7 أيام</SelectItem>
                            <SelectItem value="30">آخر 30 يوم</SelectItem>
                            <SelectItem value="90">آخر 3 أشهر</SelectItem>
                            <SelectItem value="365">آخر سنة</SelectItem>
                        </SelectContent>
                    </Select>
                    <Dialog open={showExportDialog} onOpenChange={setShowExportDialog}>
                        <DialogTrigger asChild>
                            <Button variant="outline" className="gap-2">
                                <Download className="h-4 w-4" />
                                تصدير
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>تصدير التقرير</DialogTitle>
                            </DialogHeader>
                            <div className="space-y-4">
                                <div>
                                    <Label>اختر الصيغة</Label>
                                    <Select value={exportFormat} onValueChange={setExportFormat}>
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="pdf">PDF</SelectItem>
                                            <SelectItem value="excel">Excel (XLSX)</SelectItem>
                                            <SelectItem value="csv">CSV</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <Button onClick={() => handleExport(exportFormat)} className="w-full">
                                    <Download className="h-4 w-4 ml-2" />
                                    تصدير الآن
                                </Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                    <Dialog open={showTemplateDialog} onOpenChange={setShowTemplateDialog}>
                        <DialogTrigger asChild>
                            <Button variant="outline" className="gap-2">
                                <FileText className="h-4 w-4" />
                                قوالب
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-2xl">
                            <DialogHeader>
                                <DialogTitle>قوالب التقارير</DialogTitle>
                            </DialogHeader>
                            <Tabs defaultValue="templates">
                                <TabsList>
                                    <TabsTrigger value="templates">القوالب</TabsTrigger>
                                    <TabsTrigger value="scheduled">المجدولة</TabsTrigger>
                                </TabsList>
                                <TabsContent value="templates" className="space-y-2">
                                    {reportTemplates.length === 0 ? (
                                        <div className="text-center py-8 text-gray-500">
                                            <FileText className="h-12 w-12 mx-auto mb-2 text-gray-400" />
                                            <p>لا توجد قوالب</p>
                                        </div>
                                    ) : (
                                        reportTemplates.map((template) => (
                                            <Card key={template.id} className="cursor-pointer hover:shadow-md">
                                                <CardContent className="p-4">
                                                    <div className="flex items-center justify-between">
                                                        <div>
                                                            <h4 className="font-semibold">{template.name}</h4>
                                                            <p className="text-sm text-gray-500">{template.description}</p>
                                                        </div>
                                                        <Button size="sm" onClick={() => {
                                                            // تطبيق القالب
                                                            toast.success(`تم تطبيق قالب ${template.name}`)
                                                        }}>
                                                            استخدام
                                                        </Button>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        ))
                                    )}
                                </TabsContent>
                                <TabsContent value="scheduled" className="space-y-2">
                                    {scheduledReports.length === 0 ? (
                                        <div className="text-center py-8 text-gray-500">
                                            <Calendar className="h-12 w-12 mx-auto mb-2 text-gray-400" />
                                            <p>لا توجد تقارير مجدولة</p>
                                        </div>
                                    ) : (
                                        scheduledReports.map((scheduled) => (
                                            <Card key={scheduled.id}>
                                                <CardContent className="p-4">
                                                    <div className="flex items-center justify-between">
                                                        <div>
                                                            <h4 className="font-semibold">{scheduled.name}</h4>
                                                            <p className="text-sm text-gray-500">
                                                                {scheduled.frequency} - {scheduled.next_run}
                                                            </p>
                                                        </div>
                                                        <Badge>{scheduled.status}</Badge>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        ))
                                    )}
                                </TabsContent>
                            </Tabs>
                        </DialogContent>
                    </Dialog>
                </div>
            </div>

            {/* Financial Summary Cards */}
            {financialData && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
                        <CardContent className="p-4">
                            <div className="flex justify-between items-start">
                                <div>
                                    <p className="text-sm font-medium text-green-800">إجمالي المبيعات</p>
                                    <h3 className="text-2xl font-bold text-green-900 mt-1">{financialData.total_sales.toLocaleString()} ر.س</h3>
                                </div>
                                <div className="bg-green-200 p-2 rounded-lg">
                                    <DollarSign className="h-5 w-5 text-green-700" />
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
                        <CardContent className="p-4">
                            <div className="flex justify-between items-start">
                                <div>
                                    <p className="text-sm font-medium text-blue-800">صافي الربح</p>
                                    <h3 className="text-2xl font-bold text-blue-900 mt-1">{financialData.net_profit.toLocaleString()} ر.س</h3>
                                </div>
                                <div className="bg-blue-200 p-2 rounded-lg">
                                    <Target className="h-5 w-5 text-blue-700" />
                                </div>
                            </div>
                            <div className="mt-2 text-xs text-blue-700 font-medium">
                                هامش الربح: {financialData.profit_margin}%
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
                        <CardContent className="p-4">
                            <div className="flex justify-between items-start">
                                <div>
                                    <p className="text-sm font-medium text-orange-800">تكلفة البضاعة</p>
                                    <h3 className="text-2xl font-bold text-orange-900 mt-1">{financialData.total_cost.toLocaleString()} ر.س</h3>
                                </div>
                                <div className="bg-orange-200 p-2 rounded-lg">
                                    <TrendingDown className="h-5 w-5 text-orange-700" />
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="glass-panel border-white/10 shadow-lg">
                        <CardContent className="p-4">
                            <div className="flex justify-between items-start">
                                <div>
                                    <p className="text-sm font-medium text-gray-600">النقد المحصل</p>
                                    <h3 className="text-2xl font-bold text-gray-900 mt-1">{financialData.collected_cash.toLocaleString()} ر.س</h3>
                                </div>
                                <div className="bg-gray-100 p-2 rounded-lg">
                                    <DollarSign className="h-5 w-5 text-gray-600" />
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Sales Trends Chart */}
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">اتجاه المبيعات</CardTitle>
                        <CardDescription>حركة المبيعات خلال الفترة المحددة</CardDescription>
                    </CardHeader>
                    <CardContent className="h-[300px]">
                        {salesTrends.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={salesTrends}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                    <XAxis dataKey="day" tick={{ fontSize: 12 }} tickFormatter={(val) => val.slice(5)} />
                                    <YAxis tick={{ fontSize: 12 }} />
                                    <Tooltip
                                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                                        formatter={(value: any) => [`${value.toLocaleString()} ر.س`, "المبيعات"]}
                                    />
                                    <Line type="monotone" dataKey="daily_sales" stroke="#10b981" strokeWidth={3} dot={false} />
                                </LineChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="h-full flex items-center justify-center text-gray-400">لا توجد بيانات للعرض</div>
                        )}
                    </CardContent>
                </Card>

                {/* Top Products */}
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">المنتجات الأكثر ربحية (Top 5)</CardTitle>
                        <CardDescription>المنتجات التي تحقق أعلى أرباح</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {topProducts.map((product, idx) => (
                                <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                    <div className="flex items-center gap-3">
                                        <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-bold text-xs">
                                            #{idx + 1}
                                        </div>
                                        <div>
                                            <p className="font-medium text-sm text-gray-900">{product.name}</p>
                                            <p className="text-xs text-gray-500">{product.units_sold} قطعة مباعة</p>
                                        </div>
                                    </div>
                                    <div className="text-left">
                                        <p className="font-bold text-sm text-green-700">+{product.profit.toLocaleString()} ر.س</p>
                                        <p className="text-xs text-gray-500">مبيعات: {product.revenue.toLocaleString()}</p>
                                    </div>
                                </div>
                            ))}
                            {topProducts.length === 0 && <div className="text-center text-gray-400 py-4">لا توجد بيانات</div>}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Inventory Analytics */}
            {inventoryStats && (
                <Card className="bg-slate-900 text-white border-0">
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between mb-6">
                            <div>
                                <h3 className="text-xl font-bold">تحليلات قيم المخزون</h3>
                                <p className="text-slate-400 text-sm">القيمة السوقية والتكلفة للمخزون الحالي</p>
                            </div>
                            <Package className="h-8 w-8 text-slate-500" />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                            <div>
                                <p className="text-slate-400 text-sm mb-1">عدد المنتجات</p>
                                <p className="text-2xl font-bold">{inventoryStats.total_products}</p>
                            </div>
                            <div>
                                <p className="text-slate-400 text-sm mb-1">قيمة التكلفة (رأس المال)</p>
                                <p className="text-2xl font-bold text-orange-400">{inventoryStats.total_cost_value.toLocaleString()} ر.س</p>
                            </div>
                            <div>
                                <p className="text-slate-400 text-sm mb-1">القيمة البيعية المتوقعة</p>
                                <p className="text-2xl font-bold text-green-400">{inventoryStats.total_sales_value.toLocaleString()} ر.س</p>
                            </div>
                            <div>
                                <p className="text-slate-400 text-sm mb-1">الربح المتوقع</p>
                                <p className="text-2xl font-bold text-blue-400">+{inventoryStats.potential_profit.toLocaleString()} ر.س</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
