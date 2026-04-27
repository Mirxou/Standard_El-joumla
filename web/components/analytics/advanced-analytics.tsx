"use client"

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { motion } from "framer-motion"

const DATA_SOURCE = [
    { name: 'متجر الرياض', value: 45000 },
    { name: 'المتجر الإلكتروني', value: 32000 },
    { name: 'الجملة', value: 28000 },
]

const COLORS = ['#06b6d4', '#8b5cf6', '#ec4899']

export default function AdvancedAnalytics() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">تحليلات متقدمة</h1>
                <p className="text-gray-400">توزيع الإيرادات ومصادر الدخل.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
                    <Card className="glass-panel border-0 h-[400px]">
                        <CardHeader>
                            <CardTitle className="text-white text-center">مصادر الإيرادات</CardTitle>
                        </CardHeader>
                        <CardContent className="h-[320px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={DATA_SOURCE}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={100}
                                        paddingAngle={5}
                                        dataKey="value"
                                    >
                                        {DATA_SOURCE.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', border: 'none' }} />
                                    <Legend />
                                </PieChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </motion.div>

                <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.1 }}>
                    <Card className="glass-panel border-0 h-[400px] flex flex-col justify-center items-center text-center p-8">
                        <div className="w-32 h-32 rounded-full border-4 border-cyan-500/30 flex items-center justify-center mb-6 relative">
                            <div className="absolute inset-0 rounded-full border-t-4 border-cyan-400 animate-spin" />
                            <span className="text-3xl font-bold text-white">A+</span>
                        </div>
                        <h3 className="text-2xl font-bold text-white mb-2">تصنيف الأداء</h3>
                        <p className="text-gray-400">أداء مبيعاتك استثنائي مقارنة بالشهر السابق.</p>
                    </Card>
                </motion.div>
            </div>
        </div>
    )
}
