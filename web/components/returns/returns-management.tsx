"use client"

import { RefreshCcw, FileText, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { motion } from "framer-motion"

const RETURNS = [
    { id: 'RET-001', order: 'ORD-5020', item: 'ايفون 13', reason: 'عيب مصنعي', status: 'approved', date: '2024-03-18' },
    { id: 'RET-002', order: 'ORD-5025', item: 'غطاء حماية', reason: 'تغيير رأي', status: 'pending', date: '2024-03-20' },
]

export default function ReturnsManagement() {
    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">المرتجعات</h1>
                    <p className="text-gray-400">إدارة طلبات الاسترجاع والاستبدال.</p>
                </div>
                <Button className="glass-button bg-red-500/10 text-red-400 border-red-500/20 hover:bg-red-500/20">
                    <RefreshCcw className="w-4 h-4 mr-2" />
                    طلب استرجاع جديد
                </Button>
            </div>

            <div className="space-y-4">
                {RETURNS.map((ret, i) => (
                    <motion.div
                        key={ret.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="glass-panel p-4 rounded-xl flex items-center justify-between"
                    >
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-xl bg-red-500/10 flex items-center justify-center text-red-500">
                                <RefreshCcw className="w-5 h-5" />
                            </div>
                            <div>
                                <h3 className="font-bold text-white">{ret.item}</h3>
                                <p className="text-sm text-gray-400">فاتورة: {ret.order}</p>
                            </div>
                        </div>

                        <div className="text-sm text-gray-300">
                            السبب: {ret.reason}
                        </div>

                        <div className={`px-3 py-1 rounded-full text-xs font-bold ${ret.status === 'approved' ? 'bg-green-500/10 text-green-400' : 'bg-orange-500/10 text-orange-400'
                            }`}>
                            {ret.status === 'approved' ? 'تم الموافقة' : 'قيد المراجعة'}
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    )
}
