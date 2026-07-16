"use client"

import { User, Database, Shield, Monitor, Globe, Bell } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { motion } from "framer-motion"

export default function SettingsPage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">الإعدادات</h1>
                <p className="text-gray-400">تخصيص النظام وإعدادات الحساب.</p>
            </div>

            <Tabs defaultValue="general" className="w-full">
                <TabsList className="glass-panel p-1 border-white/10 bg-white/5 w-full justify-start h-auto flex-wrap gap-2">
                    <TabsTrigger value="general" className="data-[state=active]:bg-cyan-500 data-[state=active]:text-white h-10 px-6 rounded-lg transition-all">
                        <Monitor className="w-4 h-4 mr-2" /> عام
                    </TabsTrigger>
                    <TabsTrigger value="account" className="data-[state=active]:bg-purple-500 data-[state=active]:text-white h-10 px-6 rounded-lg transition-all">
                        <User className="w-4 h-4 mr-2" /> الحساب
                    </TabsTrigger>
                    <TabsTrigger value="database" className="data-[state=active]:bg-orange-500 data-[state=active]:text-white h-10 px-6 rounded-lg transition-all">
                        <Database className="w-4 h-4 mr-2" /> النسخ الاحتياطي
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="general" className="mt-6 space-y-6">
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-6 rounded-2xl space-y-6">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="bg-white/5 p-3 rounded-xl"><Globe className="w-6 h-6 text-cyan-400" /></div>
                                <div>
                                    <h3 className="font-bold text-white">لغة النظام</h3>
                                    <p className="text-sm text-gray-400">تغيير لغة الواجهة (العربية / English)</p>
                                </div>
                            </div>
                            <Switch defaultChecked />
                        </div>

                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="bg-white/5 p-3 rounded-xl"><Bell className="w-6 h-6 text-purple-400" /></div>
                                <div>
                                    <h3 className="font-bold text-white">الإشعارات الصوتية</h3>
                                    <p className="text-sm text-gray-400">تشغيل صوت عند وجود تنبيه جديد</p>
                                </div>
                            </div>
                            <Switch defaultChecked />
                        </div>
                    </motion.div>
                </TabsContent>

                <TabsContent value="account" className="mt-6">
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-6 rounded-2xl max-w-xl space-y-4">
                        <div className="grid gap-2">
                            <Label className="text-white">اسم المستخدم</Label>
                            <Input value="admin" disabled className="bg-white/5 border-white/10 text-gray-400" />
                        </div>
                        <div className="grid gap-2">
                            <Label className="text-white">كلمة المرور الحالية</Label>
                            <Input type="password" placeholder="••••••" className="bg-white/5 border-white/10 text-white" />
                        </div>
                        <div className="grid gap-2">
                            <Label className="text-white">كلمة المرور الجديدة</Label>
                            <Input type="password" placeholder="••••••" className="bg-white/5 border-white/10 text-white" />
                        </div>
                        <Button className="w-full bg-purple-600 hover:bg-purple-500">حفظ التغييرات</Button>
                    </motion.div>
                </TabsContent>

                <TabsContent value="database" className="mt-6">
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-6 rounded-2xl space-y-6">
                        <div className="flex items-center justify-between p-4 bg-orange-500/10 border border-orange-500/20 rounded-xl">
                            <div className="flex gap-4">
                                <Database className="w-10 h-10 text-orange-500" />
                                <div>
                                    <h3 className="font-bold text-white">النسخ الاحتياطي التلقائي</h3>
                                    <p className="text-sm text-gray-400">آخر نسخة: 2024-03-20 12:00 PM</p>
                                </div>
                            </div>
                            <Button className="bg-orange-600 hover:bg-orange-500">إنشاء نسخة الآن</Button>
                        </div>
                    </motion.div>
                </TabsContent>
            </Tabs>
        </div>
    )
}
