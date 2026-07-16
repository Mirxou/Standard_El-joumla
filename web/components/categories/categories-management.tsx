"use client"

import { useState, useEffect } from "react"
import { FolderTree, Plus, MoreVertical, Edit3, Trash2, Package } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger
} from "@/components/ui/dropdown-menu"
import { motion } from "framer-motion"
import { apiClient } from "@/lib/api/client"
import { API_CONFIG } from "@/lib/config/api"

const COLOR_PALETTES = [
    'from-blue-500/20 to-cyan-500/20',
    'from-purple-500/20 to-pink-500/20',
    'from-orange-500/20 to-red-500/20',
    'from-green-500/20 to-emerald-500/20',
    'from-gray-500/20 to-slate-500/20',
]

export default function CategoriesManagement() {
    const [categories, setCategories] = useState<any[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchCategories = async () => {
            try {
                setLoading(true)
                const response = await apiClient.get(API_CONFIG.ENDPOINTS.CATEGORIES)
                const categoriesList = Array.isArray(response) ? response : (response?.items || response?.categories || [])
                
                // إضافة colors و counts من API
                const categoriesWithStats = categoriesList.map((cat: any, index: number) => ({
                    ...cat,
                    color: COLOR_PALETTES[index % COLOR_PALETTES.length],
                    count: cat.product_count || cat.products_count || 0,
                    value: cat.total_value ? `${cat.total_value.toLocaleString()}` : '0'
                }))
                
                setCategories(categoriesWithStats)
            } catch (e) {
                console.error("Error fetching categories:", e)
                setCategories([])
            } finally {
                setLoading(false)
            }
        }
        fetchCategories()
    }, [])
    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">إدارة الفئات</h1>
                    <p className="text-gray-400">تنظيم المنتجات في أقسام رئيسية وفرعية.</p>
                </div>
                <Button className="bg-cyan-600 hover:bg-cyan-500 shadow-lg shadow-cyan-500/20">
                    <Plus className="w-4 h-4 mr-2" />
                    فئة جديدة
                </Button>
            </div>

            {loading ? (
                <div className="text-center text-white py-12">جاري التحميل...</div>
            ) : categories.length === 0 ? (
                <div className="text-center text-white py-12">لا توجد فئات</div>
            ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {categories.map((cat, i) => (
                    <motion.div
                        key={cat.id}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: i * 0.1 }}
                        className={`glass-panel p-6 rounded-2xl relative group overflow-hidden bg-gradient-to-br ${cat.color} border-white/5 hover:border-white/20 transition-all`}
                    >
                        <div className="absolute top-4 left-4 opacity-0 group-hover:opacity-100 transition-opacity">
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full bg-black/20 text-white">
                                        <MoreVertical className="w-4 h-4" />
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent>
                                    <DropdownMenuItem><Edit3 className="w-4 h-4 mr-2" />تعديل</DropdownMenuItem>
                                    <DropdownMenuItem className="text-red-500"><Trash2 className="w-4 h-4 mr-2" />حذف</DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        </div>

                        <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center mb-4">
                            <FolderTree className="w-6 h-6 text-white" />
                        </div>

                        <h3 className="text-xl font-bold text-white mb-1">{cat.name}</h3>

                        <div className="flex items-center gap-4 mt-6">
                            <div className="flex items-center gap-2 text-sm text-white/80">
                                <Package className="w-4 h-4 opacity-70" />
                                {cat.count} منتج
                            </div>
                            <div className="w-px h-4 bg-white/10" />
                            <div className="text-sm text-cyan-300 font-bold">
                                {cat.value} ر.س
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>
            )}
        </div>
    )
}
