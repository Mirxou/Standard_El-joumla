"use client"

import { FileText, Download } from "lucide-react"
import { Button } from "@/components/ui/button"

const REPORTS = [
    { name: 'تقرير المبيعات اليومي', desc: 'ملخص المبيعات وطرق الدفع', type: 'PDF' },
    { name: 'تقرير المخزون الجردي', desc: 'قائمة بجميع العناصر والكميات', type: 'Excel' },
    { name: 'تقرير أداء الموظفين', desc: 'ساعات العمل والعمولات', type: 'PDF' },
    { name: 'تقرير الضرائب', desc: 'ضريبة القيمة المضافة VAT', type: 'Excel' },
]

export default function ReportsManagement() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">التقارير العامة</h1>
                <p className="text-gray-400">تصدير وطباعة التقارير الدورية.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {REPORTS.map((rep, i) => (
                    <div key={i} className="glass-panel p-6 rounded-2xl flex items-center justify-between group hover:border-cyan-500/50 transition-colors">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-white/5 rounded-xl flex items-center justify-center">
                                <FileText className="w-6 h-6 text-cyan-400" />
                            </div>
                            <div>
                                <h3 className="font-bold text-white">{rep.name}</h3>
                                <p className="text-sm text-gray-500">{rep.desc}</p>
                            </div>
                        </div>
                        <Button variant="ghost" size="icon" className="text-gray-400 hover:text-white">
                            <Download className="w-5 h-5" />
                        </Button>
                    </div>
                ))}
            </div>
        </div>
    )
}
