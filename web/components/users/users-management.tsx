"use client"

import { UserCircle, Shield, Mail } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

export default function UsersManagement() {
    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">المستخدمين والصلاحيات</h1>
                    <p className="text-gray-400">إدارة فريق العمل وصلاحيات الوصول للنظام.</p>
                </div>
                <Button className="glass-button">مستخدم جديد</Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="glass-panel p-6 rounded-2xl flex flex-col items-center text-center">
                    <div className="w-20 h-20 rounded-full bg-cyan-500/20 flex items-center justify-center text-cyan-400 mb-4 border-2 border-cyan-500/30">
                        <UserCircle className="w-10 h-10" />
                    </div>
                    <h3 className="text-xl font-bold text-white">المدير العام</h3>
                    <p className="text-gray-400 text-sm mb-4">admin@system.com</p>
                    <Badge className="bg-cyan-500/20 text-cyan-300 border-cyan-500/30 mb-6">صلاحيات كاملة</Badge>

                    <div className="w-full grid grid-cols-2 gap-2 mt-auto">
                        <Button variant="outline" className="border-white/10 text-gray-300">تعديل</Button>
                        <Button variant="outline" className="border-white/10 text-gray-300">سجل</Button>
                    </div>
                </div>

                <div className="glass-panel p-6 rounded-2xl flex flex-col items-center text-center bg-white/5 border-dashed border-2 border-white/10 hover:border-white/30 transition-colors cursor-pointer justify-center min-h-[300px]">
                    <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center text-gray-400 mb-2">
                        <UserCircle className="w-8 h-8" />
                    </div>
                    <p className="text-gray-400 font-medium">إضافة عضو جديد</p>
                </div>
            </div>
        </div>
    )
}
