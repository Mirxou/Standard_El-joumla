"use client"

import { Bell, AlertTriangle, CheckCircle, Info } from "lucide-react"
import { motion } from "framer-motion"

const ALERTS = [
    { id: 1, type: 'critical', title: 'مخزون حرج: ايفون 13', time: 'منذ 10 دقائق', desc: 'الكمية المتاحة 2 فقط' },
    { id: 2, type: 'warning', title: 'اقتراب انتهاء صلاحية', time: 'منذ 2 ساعة', desc: 'حليب المراعي - الدفعة #599' },
    { id: 3, type: 'info', title: 'تم اكتمال النسخ الاحتياطي', time: 'منذ 5 ساعات', desc: 'تم حفظ قاعدة البيانات بنجاح' },
    { id: 4, type: 'success', title: 'تحقيق هدف المبيعات', time: 'أمس', desc: 'تم تجاوز هدف 10,000 ر.س' },
]

export default function AlertsPage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">مركز التنبيهات</h1>
                <p className="text-gray-400">جميع الإشعارات الهامة في مكان واحد.</p>
            </div>

            <div className="space-y-3">
                {ALERTS.map((alert, i) => (
                    <motion.div
                        key={alert.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className={`glass-panel p-4 rounded-xl flex items-start gap-4 border-r-4 ${alert.type === 'critical' ? 'border-r-red-500 bg-red-500/5' :
                                alert.type === 'warning' ? 'border-r-orange-500 bg-orange-500/5' :
                                    alert.type === 'success' ? 'border-r-green-500 bg-green-500/5' :
                                        'border-r-blue-500 bg-blue-500/5'
                            }`}
                    >
                        <div className={`mt-1 ${alert.type === 'critical' ? 'text-red-500' :
                                alert.type === 'warning' ? 'text-orange-500' :
                                    alert.type === 'success' ? 'text-green-500' :
                                        'text-blue-500'
                            }`}>
                            {alert.type === 'critical' && <AlertTriangle className="w-5 h-5" />}
                            {alert.type === 'warning' && <Bell className="w-5 h-5" />}
                            {alert.type === 'success' && <CheckCircle className="w-5 h-5" />}
                            {alert.type === 'info' && <Info className="w-5 h-5" />}
                        </div>

                        <div className="flex-1">
                            <div className="flex justify-between items-start">
                                <h3 className="font-bold text-white">{alert.title}</h3>
                                <span className="text-xs text-gray-500">{alert.time}</span>
                            </div>
                            <p className="text-sm text-gray-400 mt-1">{alert.desc}</p>
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    )
}
