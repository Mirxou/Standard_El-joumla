"use client"

import { Cloud, Download, Upload } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function BackupRestore() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">النسخ الاحتياطي</h1>
                <p className="text-gray-400">حماية بياناتك من الفقدان.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass-panel p-8 rounded-3xl flex flex-col items-center text-center border-t-4 border-t-cyan-500">
                    <Cloud className="w-16 h-16 text-cyan-400 mb-6" />
                    <h3 className="text-2xl font-bold text-white mb-2">نسخة سحابية</h3>
                    <p className="text-gray-400 mb-8">يتم حفظ البيانات تلقائياً كل 24 ساعة.</p>
                    <Button className="w-full bg-cyan-600 hover:bg-cyan-500">مزامنة الآن</Button>
                </div>

                <div className="glass-panel p-8 rounded-3xl flex flex-col items-center text-center border-t-4 border-t-purple-500">
                    <Download className="w-16 h-16 text-purple-400 mb-6" />
                    <h3 className="text-2xl font-bold text-white mb-2">تصدير محلي</h3>
                    <p className="text-gray-400 mb-8">تحميل قاعدة البيانات كملف SQL.</p>
                    <Button variant="outline" className="w-full border-white/10 text-white hover:bg-white/5">تحميل الملف</Button>
                </div>
            </div>
        </div>
    )
}
