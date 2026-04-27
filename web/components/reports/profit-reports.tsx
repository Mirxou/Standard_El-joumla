"use client"

import { BarChart3, TrendingUp, DollarSign, Calendar } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts"

const DATA = [
    { name: 'يناير', profit: 4000, revenue: 2400 },
    { name: 'فبراير', profit: 3000, revenue: 1398 },
    { name: 'مارس', profit: 2000, revenue: 9800 },
    { name: 'أبريل', profit: 2780, revenue: 3908 },
    { name: 'مايو', profit: 1890, revenue: 4800 },
    { name: 'يونيو', profit: 2390, revenue: 3800 },
]

export default function ProfitReports() {
    return (
        <div className="space-y-6">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">تقارير الأرباح</h1>
                    <p className="text-gray-400">تحليل الأداء المالي للفترة الحالية.</p>
                </div>
                <div className="glass-panel px-4 py-2 border-white/10 text-cyan-400 font-mono text-xl font-bold">
                    2024
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="glass-panel border-0 border-r-4 border-r-green-500">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-gray-400 text-sm font-medium">صافي الربح</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold text-white">45,230 ر.س</div>
                    </CardContent>
                </Card>
                <Card className="glass-panel border-0 border-r-4 border-r-blue-500">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-gray-400 text-sm font-medium">الإيرادات</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold text-white">120,500 ر.س</div>
                    </CardContent>
                </Card>
                <Card className="glass-panel border-0 border-r-4 border-r-red-500">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-gray-400 text-sm font-medium">المصروفات</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold text-white">75,270 ر.س</div>
                    </CardContent>
                </Card>
            </div>

            <Card className="glass-panel border-0">
                <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-cyan-400" />
                        تحليل الأرباح الشهري
                    </CardTitle>
                </CardHeader>
                <CardContent className="h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={DATA}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis dataKey="name" stroke="#666" />
                            <YAxis stroke="#666" />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
                                cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                            />
                            <Bar dataKey="revenue" fill="#3b82f6" radius={[4, 4, 0, 0]} name="الإيرادات" />
                            <Bar dataKey="profit" fill="#10b981" radius={[4, 4, 0, 0]} name="الربح" />
                        </BarChart>
                    </ResponsiveContainer>
                </CardContent>
            </Card>
        </div>
    )
}
