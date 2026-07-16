"use client"

import { useState, useEffect } from "react"
import { Sparkles, TrendingUp, Zap, Target } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts"
import { motion } from "framer-motion"
import { apiClient } from "@/lib/api/client"
import { API_CONFIG } from "@/lib/config/api"

const FORECAST_DATA = [
    { day: 'اليوم', actual: 4000, predicted: 4200 },
    { day: 'غداً', actual: null, predicted: 4500 },
    { day: '+2', actual: null, predicted: 4800 },
    { day: '+3', actual: null, predicted: 3900 },
    { day: '+4', actual: null, predicted: 5100 },
    { day: '+5', actual: null, predicted: 5400 },
    { day: '+6', actual: null, predicted: 4900 },
]

export default function AIForecastDashboard() {
    return (
        <div className="space-y-6">
            <div className="flex items-center gap-3">
                <div className="p-3 bg-purple-500/10 rounded-xl border border-purple-500/20">
                    <Sparkles className="w-8 h-8 text-purple-400 animate-pulse" />
                </div>
                <div>
                    <h1 className="text-3xl font-bold text-white mb-1">التنبؤ الذكي AI</h1>
                    <p className="text-purple-300">تحليل الاتجاهات المستقبلية باستخدام الذكاء الاصطناعي.</p>
                </div>
            </div>

            {/* Insight Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                    <Card className="glass-panel border-purple-500/20 bg-purple-900/10">
                        <CardContent className="p-6">
                            <div className="flex items-center gap-3 mb-2">
                                <TrendingUp className="w-5 h-5 text-purple-400" />
                                <h3 className="text-purple-200 font-bold">توقعات الطلب</h3>
                            </div>
                            <p className="text-2xl font-bold text-white mb-1">+15%</p>
                            <p className="text-xs text-purple-300">ارتفاع متوقع في الأسبوع القادم</p>
                        </CardContent>
                    </Card>
                </motion.div>

                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                    <Card className="glass-panel border-cyan-500/20 bg-cyan-900/10">
                        <CardContent className="p-6">
                            <div className="flex items-center gap-3 mb-2">
                                <Zap className="w-5 h-5 text-cyan-400" />
                                <h3 className="text-cyan-200 font-bold">المنتجات الرائجة</h3>
                            </div>
                            <p className="text-xl font-bold text-white mb-1">سماعات بلوتوث</p>
                            <p className="text-xs text-cyan-300">احتمالية نفاذ المخزون: 85%</p>
                        </CardContent>
                    </Card>
                </motion.div>

                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
                    <Card className="glass-panel border-green-500/20 bg-green-900/10">
                        <CardContent className="p-6">
                            <div className="flex items-center gap-3 mb-2">
                                <Target className="w-5 h-5 text-green-400" />
                                <h3 className="text-green-200 font-bold">دقة التنبؤ</h3>
                            </div>
                            <p className="text-2xl font-bold text-white mb-1">94.2%</p>
                            <p className="text-xs text-green-300">بناءً على البيانات التاريخية</p>
                        </CardContent>
                    </Card>
                </motion.div>
            </div>

            {/* Main Chart */}
            <Card className="glass-panel border-0">
                <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-purple-400" />
                        توقعات المبيعات (7 أيام)
                    </CardTitle>
                </CardHeader>
                <CardContent className="h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={FORECAST_DATA}>
                            <defs>
                                <linearGradient id="splitColor" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis dataKey="day" stroke="#666" />
                            <YAxis stroke="#666" />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#a855f7', borderRadius: '8px' }}
                                itemStyle={{ color: '#fff' }}
                            />
                            <Area
                                type="monotone"
                                dataKey="predicted"
                                stroke="#a855f7"
                                strokeWidth={3}
                                strokeDasharray="5 5"
                                fill="url(#splitColor)"
                                name="تنبؤ AI"
                            />
                            <Area
                                type="monotone"
                                dataKey="actual"
                                stroke="#22c55e"
                                strokeWidth={3}
                                fill="transparent"
                                name="فعلي"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </CardContent>
            </Card>
        </div>
    )
}
