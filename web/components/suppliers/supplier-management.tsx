"use client"

import { Phone, Mail, MapPin, MoreHorizontal, Star } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { motion } from "framer-motion"

const SUPPLIERS = [
    { id: 1, name: 'شركة التقنية المتقدمة', contact: 'أحمد محمد', phone: '0501234567', email: 'sales@tech-adv.com', rating: 5, category: 'إلكترونيات' },
    { id: 2, name: 'مؤسسة التوريد السريع', contact: 'خالد علي', phone: '0559876543', email: 'info@express.com', rating: 4, category: 'اكسسوارات' },
    { id: 3, name: 'عالم الجوالات', contact: 'سعيد عمر', phone: '0561122334', email: 'saeed@phones.com', rating: 4.5, category: 'قطع غيار' },
    { id: 4, name: 'القمة للتجارة', contact: 'محمد حسن', phone: '0544455666', email: 'top@trading.com', rating: 3, category: 'أجهزة مكتبية' },
]

export default function SupplierManagement() {
    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">الموردين</h1>
                    <p className="text-gray-400">قائمة الشركاء والموردين.</p>
                </div>
                <Button className="glass-button">
                    مورد جديد
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {SUPPLIERS.map((sup, i) => (
                    <motion.div
                        key={sup.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="glass-panel p-4 rounded-2xl flex items-center gap-4 group hover:bg-white/5 transition-colors"
                    >
                        <Avatar className="h-16 w-16 border-2 border-white/10">
                            <AvatarImage src={`https://api.dicebear.com/7.x/initials/svg?seed=${sup.name}`} />
                            <AvatarFallback>SP</AvatarFallback>
                        </Avatar>

                        <div className="flex-1 min-w-0">
                            <div className="flex justify-between">
                                <h3 className="font-bold text-white truncate">{sup.name}</h3>
                                <div className="flex gap-0.5">
                                    {[...Array(5)].map((_, stars) => (
                                        <Star
                                            key={stars}
                                            className={`w-3 h-3 ${stars < Math.floor(sup.rating) ? 'text-yellow-400 fill-yellow-400' : 'text-gray-600'}`}
                                        />
                                    ))}
                                </div>
                            </div>
                            <p className="text-sm text-cyan-400 mb-2">{sup.category}</p>

                            <div className="flex gap-4 text-xs text-gray-400">
                                <div className="flex items-center gap-1 hover:text-white transition-colors cursor-pointer">
                                    <Phone className="w-3 h-3" />
                                    {sup.phone}
                                </div>
                                <div className="flex items-center gap-1 hover:text-white transition-colors cursor-pointer">
                                    <Mail className="w-3 h-3" />
                                    {sup.contact}
                                </div>
                            </div>
                        </div>

                        <Button variant="ghost" size="icon" className="text-gray-500 hover:text-white">
                            <MoreHorizontal className="w-5 h-5" />
                        </Button>
                    </motion.div>
                ))}
            </div>
        </div>
    )
}
