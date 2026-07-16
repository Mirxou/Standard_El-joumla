"use client"

import { useState, useEffect } from "react"
import { ArrowDownLeft, ArrowUpRight, History, Search, FileText } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { motion } from "framer-motion"
import { apiClient } from "@/lib/api/client"
import { API_CONFIG } from "@/lib/config/api"

export default function InventoryManagement() {
    const [search, setSearch] = useState("")
    const [transactions, setTransactions] = useState<any[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchTransactions = async () => {
            try {
                setLoading(true)
                const response = await apiClient.get(`${API_CONFIG.ENDPOINTS.INVENTORY}/transactions`)
                setTransactions(Array.isArray(response) ? response : (response?.items || response?.transactions || []))
            } catch (e) {
                console.error("Error fetching inventory transactions:", e)
                setTransactions([])
            } finally {
                setLoading(false)
            }
        }
        fetchTransactions()
    }, [])

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">سجل حركات المخزون</h1>
                    <p className="text-gray-400">تتبع كامل لحركة الصادر والوارد.</p>
                </div>
                <Button className="glass-button bg-cyan-500/20 text-cyan-400 border-cyan-500/30 hover:bg-cyan-500/30">
                    <FileText className="w-4 h-4 mr-2" />
                    تقرير الجرد
                </Button>
            </div>

            <div className="glass-panel p-4 rounded-2xl">
                <div className="relative">
                    <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <Input
                        placeholder="بحث في السجل..."
                        className="bg-white/5 border-white/10 text-white pl-4 pr-10"
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                    />
                </div>
            </div>

            <div className="space-y-4">
                {loading ? (
                    <div className="text-center text-white py-12">جاري التحميل...</div>
                ) : transactions.length === 0 ? (
                    <div className="text-center text-white py-12">لا توجد حركات مخزون</div>
                ) : (
                transactions.filter(tx => 
                    !search || 
                    tx.product?.toLowerCase().includes(search.toLowerCase()) ||
                    tx.product_name?.toLowerCase().includes(search.toLowerCase())
                ).map((tx, i) => (
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 }}
                        key={tx.id}
                        className="glass-panel p-4 rounded-xl flex items-center justify-between group hover:bg-white/5 transition-colors"
                    >
                        <div className="flex items-center gap-4">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${(tx.type === 'in' || tx.transaction_type === 'in' || tx.quantity > 0) ? 'bg-green-500/10 text-green-400' : 'bg-orange-500/10 text-orange-400'}`}>
                                {(tx.type === 'in' || tx.transaction_type === 'in' || tx.quantity > 0) ? <ArrowDownLeft className="w-5 h-5" /> : <ArrowUpRight className="w-5 h-5" />}
                            </div>
                            <div>
                                <h4 className="font-bold text-white">{tx.product || tx.product_name || 'غير محدد'}</h4>
                                <p className="text-xs text-gray-500">{tx.date || tx.created_at || ''} • بواسطة {tx.user || tx.created_by || 'غير محدد'}</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-6">
                            <div className="text-center">
                                <span className="block text-xs text-gray-500">الكمية</span>
                                <span className={`font-bold ${(tx.type === 'in' || tx.transaction_type === 'in' || tx.quantity > 0) ? 'text-green-400' : 'text-orange-400'}`}>
                                    {(tx.type === 'in' || tx.transaction_type === 'in' || tx.quantity > 0) ? '+' : '-'}{Math.abs(tx.quantity || 0)}
                                </span>
                            </div>
                            <Badge variant="outline" className="border-white/10 text-gray-400">
                                {(tx.type === 'in' || tx.transaction_type === 'in' || tx.quantity > 0) ? 'شراء' : 'بيع'}
                            </Badge>
                        </div>
                    </motion.div>
                ))
                )}
            </div>
        </div>
    )
}
