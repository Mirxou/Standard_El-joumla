"use client"

import { ShoppingBag, Calendar, Truck, AlertCircle } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { motion } from "framer-motion"

const PURCHASES = [
    { id: 'PO-1001', supplier: 'شركة التقنية المتقدمة', items: 50, total: 12500, status: 'completed', date: '2024-03-15' },
    { id: 'PO-1002', supplier: 'عالم الجوالات', items: 20, total: 4200, status: 'pending', date: '2024-03-20' },
    { id: 'PO-1003', supplier: 'مؤسسة التوريد السريع', items: 100, total: 8900, status: 'processing', date: '2024-03-21' },
]

export default function PurchasesManagement() {
    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">إدارة المشتريات</h1>
                    <p className="text-gray-400">أوامر الشراء وفواتير الموردين.</p>
                </div>
                <Button className="glass-button">شراء جديد</Button>
            </div>

            <div className="space-y-4">
                {PURCHASES.map((po, i) => (
                    <motion.div
                        key={po.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="glass-panel p-4 rounded-xl flex items-center justify-between group hover:bg-white/5"
                    >
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center text-blue-500">
                                <ShoppingBag className="w-6 h-6" />
                            </div>
                            <div>
                                <h3 className="font-bold text-white">{po.supplier}</h3>
                                <div className="flex items-center gap-2 text-xs text-gray-500">
                                    <span className="font-mono">{po.id}</span>
                                    <span>•</span>
                                    <Calendar className="w-3 h-3" /> {po.date}
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center gap-8">
                            <div className="text-center">
                                <span className="text-xs text-gray-500 block">المنتجات</span>
                                <span className="font-bold text-white">{po.items}</span>
                            </div>
                            <div className="text-center">
                                <span className="text-xs text-gray-500 block">الإجمالي</span>
                                <span className="font-bold text-cyan-400">{po.total.toLocaleString()} ر.س</span>
                            </div>
                            <Badge className={`
                      ${po.status === 'completed' ? 'bg-green-500/10 text-green-400 border-green-500/20' : ''}
                      ${po.status === 'pending' ? 'bg-orange-500/10 text-orange-400 border-orange-500/20' : ''}
                      ${po.status === 'processing' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' : ''}
                   `}>
                                {po.status === 'completed' ? 'مكتمل' : po.status === 'pending' ? 'انتظار' : 'جاري التنفيذ'}
                            </Badge>
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    )
}
