"use client"

import { Activity } from "lucide-react"

export default function ActivityLog() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">سجل النشاطات</h1>
                <p className="text-gray-400">تتبع جميع العمليات التي تمت في النظام.</p>
            </div>

            <div className="glass-panel p-8 rounded-2xl text-center">
                <div className="w-20 h-20 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Activity className="w-10 h-10 text-gray-500" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">السجل قيد التحديث</h3>
                <p className="text-gray-400 max-w-md mx-auto">سيتم عرض جميع عمليات تسجيل الدخول، المبيعات، وتعديلات المخزون هنا بالتفصيل.</p>
            </div>
        </div>
    )
}
