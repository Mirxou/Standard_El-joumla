"use client"

import { Calendar, AlertTriangle, Clock } from "lucide-react"
import { motion } from "framer-motion"

const EXPIRY_ITEMS = [
    { name: 'حليب نادك طازج', sku: 'ND-202', date: '2024-03-25', status: 'critical', daysLeft: 2 },
    { name: 'زبادي المراعي', sku: 'MR-101', date: '2024-03-28', status: 'warning', daysLeft: 5 },
    { name: 'عصير برتقال', sku: 'OJ-500', date: '2024-04-10', status: 'ok', daysLeft: 18 },
    { name: 'جبنة شيدر', sku: 'CH-300', date: '2024-04-15', status: 'ok', daysLeft: 23 },
]

export default function ExpiryTracking() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">تتبع الصلاحية</h1>
                <p className="text-gray-400">مراقبة تواريخ الانتهاء للمنتجات القابلة للتلف.</p>
            </div>

            <div className="grid grid-cols-1 gap-4">
                {EXPIRY_ITEMS.map((item, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="glass-panel p-4 rounded-xl flex items-center justify-between"
                    >
                        <div className="flex items-center gap-4">
                            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${item.status === 'critical' ? 'bg-red-500/20 text-red-500' :
                                    item.status === 'warning' ? 'bg-orange-500/20 text-orange-500' :
                                        'bg-green-500/20 text-green-500'
                                }`}>
                                {item.status === 'critical' ? <AlertTriangle className="w-6 h-6" /> : <Clock className="w-6 h-6" />}
                            </div>
                            <div>
                                <h3 className="font-bold text-white">{item.name}</h3>
                                <p className="text-sm text-gray-500">SKU: {item.sku}</p>
                            </div>
                        </div>

                        <div className="text-left">
                            <div className={`text-2xl font-bold ${item.status === 'critical' ? 'text-red-500' :
                                    item.status === 'warning' ? 'text-orange-500' : 'text-green-500'
                                }`}>
                                {item.daysLeft} يوم
                            </div>
                            <div className="text-xs text-gray-500 flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {item.date}
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    )
}
