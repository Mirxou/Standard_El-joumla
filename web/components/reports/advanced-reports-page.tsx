"use client"

import { FileBarChart } from "lucide-react"

export default function AdvancedReportsPage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">تقارير مخصصة</h1>
                <p className="text-gray-400">بناء تقارير متقدمة حسب الحاجة.</p>
            </div>
            <div className="glass-panel p-12 text-center flex flex-col items-center">
                <FileBarChart className="w-16 h-16 text-cyan-500/50 mb-4" />
                <h3 className="text-xl font-bold text-white">منشئ التقارير</h3>
                <p className="text-gray-400 mt-2">اختر المعايير والفلاتر لإنشاء تقريرك الخاص.</p>
            </div>
        </div>
    )
}
