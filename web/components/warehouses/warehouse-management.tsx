"use client"

import React from "react"
import { Warehouse as WarehouseIcon, MapPin, Package, AlertTriangle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { motion } from "framer-motion"
import { warehousesService, Warehouse } from "@/lib/api/services/warehouses"
import CreateWarehouse from "@/components/create-warehouse"

export default function WarehouseManagement() {
    const [warehouses, setWarehouses] = React.useState<Warehouse[]>([])
    const [loading, setLoading] = React.useState(true)

    const fetchWarehouses = async () => {
        try {
            setLoading(true)
            const data = await warehousesService.getAll()
            setWarehouses(data)
        } catch (error) {
            console.error(error)
        } finally {
            setLoading(false)
        }
    }

    React.useEffect(() => {
        fetchWarehouses()
    }, [])

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">المستودعات</h1>
                    <p className="text-gray-400">إدارة مواقع التخزين والسعة الاستيعابية.</p>
                </div>
                <div className="flex gap-2">
                    <Button onClick={fetchWarehouses} variant="outline" className="glass-button">
                        تحديث
                    </Button>
                    <CreateWarehouse onSaved={fetchWarehouses} />
                </div>
            </div>

            {loading ? (
                <div className="text-center text-gray-400 py-10">جاري التحميل...</div>
            ) : warehouses.length === 0 ? (
                <div className="text-center text-gray-400 py-10">
                    لا توجد مستودعات متاحة. قم بإضافة مستودع جديد.
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {warehouses.map((wh, i) => (
                        <motion.div
                            key={wh.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.15 }}
                            className="glass-panel p-6 rounded-3xl relative overflow-hidden group hover:border-cyan-500/30 transition-colors"
                        >
                            <div className="flex justify-between items-start mb-6">
                                <div className="flex gap-4">
                                    <div className="w-14 h-14 rounded-2xl bg-orange-500/10 flex items-center justify-center text-orange-500">
                                        <WarehouseIcon className="w-7 h-7" />
                                    </div>
                                    <div>
                                        <h3 className="text-xl font-bold text-white mb-1">{wh.name}</h3>
                                        <div className="flex items-center gap-2 text-sm text-gray-400">
                                            <MapPin className="w-3 h-3" />
                                            {wh.city} - {wh.address || 'لا يوجد عنوان'}
                                        </div>
                                    </div>
                                </div>
                                <div className={`px-3 py-1 rounded-full text-xs font-bold ${wh.status === 'ممتلئ تقريباً' ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'}`}>
                                    {wh.status}
                                </div>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <div className="flex justify-between text-sm mb-2">
                                        <span className="text-gray-400">السعة المستخدمة</span>
                                        <span className={`font-bold ${wh.current_utilization / wh.capacity > 0.9 ? 'text-red-400' : 'text-cyan-400'}`}>
                                            {wh.capacity > 0 ? Math.round((wh.current_utilization / wh.capacity) * 100) : 0}%
                                        </span>
                                    </div>
                                    <Progress value={wh.capacity > 0 ? (wh.current_utilization / wh.capacity) * 100 : 0}
                                        className={`h-2 ${wh.current_utilization / wh.capacity > 0.9 ? 'bg-red-900/20' : 'bg-cyan-900/20'}`} />
                                </div>

                                <div className="flex gap-6 pt-4 border-t border-white/5">
                                    <div>
                                        <span className="text-xs text-gray-500 block mb-1">السعة الكلية</span>
                                        <span className="text-lg font-bold text-white flex items-center gap-2">
                                            <Package className="w-4 h-4 text-gray-400" />
                                            {wh.capacity.toLocaleString()}
                                        </span>
                                    </div>
                                    <div>
                                        <span className="text-xs text-gray-500 block mb-1">المشغولة</span>
                                        <span className="text-lg font-bold text-white flex items-center gap-2">
                                            <Package className="w-4 h-4 text-orange-400" />
                                            {wh.current_utilization.toLocaleString()}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}
        </div>
    )
}
