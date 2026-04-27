"use client"

import { useState, useEffect } from "react"
import {
    Search,
    Plus,
    Filter,
    MoreVertical,
    Edit3,
    Trash2,
    Package,
    AlertTriangle,
    ArrowUpDown,
    Download,
    Barcode
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { productsService } from "@/lib/api/services/products"
import { API_CONFIG } from "@/lib/config/api"
import { toast } from "sonner"
import { motion, AnimatePresence } from "framer-motion"
import ProductForm from "@/components/product-form"

export default function ProductsManagement() {
    const [products, setProducts] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState("")
    const [viewMode, setViewMode] = useState<'list' | 'grid'>('list')
    const [isProductFormOpen, setIsProductFormOpen] = useState(false)

    useEffect(() => {
        fetchProducts()
    }, [])

    const fetchProducts = async () => {
        try {
            setLoading(true)
            const data = await productsService.getAll()
            setProducts(data)
        } catch (error) {
            console.error(error)
            toast.error("فشل تحميل المنتجات")
        } finally {
            setLoading(false)
        }
    }


    // Filtered Products
    const filteredProducts = products.filter(p =>
        p.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.name_ar?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.name_en?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.barcode?.includes(searchQuery)
    )

    return (
        <div className="space-y-6">

            {/* Header & Actions */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">إدارة المنتجات</h1>
                    <p className="text-gray-400">تحكم كامل في المخزون، الأسعار، والباركود.</p>
                </div>
                <div className="flex gap-3">
                    <Button variant="outline" className="glass-panel border-white/10 hover:bg-white/5 text-gray-300">
                        <Download className="w-4 h-4 mr-2" />
                        تصدير
                    </Button>
                    <ProductForm
                        onSaved={() => {
                            fetchProducts()
                        }}
                        trigger={
                            <Button className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white border-0 shadow-lg shadow-cyan-500/20">
                                <Plus className="w-4 h-4 mr-2" />
                                منتج جديد
                            </Button>
                        }
                    />
                </div>
            </div>

            {/* Glass Filter Bar */}
            <div className="glass-panel p-4 rounded-2xl flex flex-col md:flex-row gap-4 items-center">
                <div className="relative flex-1 w-full">
                    <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <Input
                        placeholder="بحث باسم المنتج أو الباركود..."
                        className="bg-white/5 border-white/10 text-white h-10 pr-10 focus-visible:ring-cyan-500/50"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
                <div className="flex gap-2 w-full md:w-auto">
                    <Button variant="outline" className="flex-1 md:flex-none glass-button text-gray-300 border-white/10">
                        <Filter className="w-4 h-4 mr-2" />
                        تصفية
                    </Button>
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="outline" className="flex-1 md:flex-none glass-button text-gray-300 border-white/10">
                                <ArrowUpDown className="w-4 h-4 mr-2" />
                                ترتيب
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent className="glass-panel border-white/10">
                            <DropdownMenuItem className="text-white hover:bg-white/5 focus:bg-white/10">الأعلى سعراً</DropdownMenuItem>
                            <DropdownMenuItem className="text-white hover:bg-white/5 focus:bg-white/10">الأقل سعراً</DropdownMenuItem>
                            <DropdownMenuItem className="text-white hover:bg-white/5 focus:bg-white/10">الأكثر مخزوناً</DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </div>

            {/* Products List (Glass Strips) */}
            <div className="space-y-3">
                {/* Table Header */}
                <div className="hidden md:grid grid-cols-12 gap-4 px-6 py-2 text-sm font-medium text-gray-500">
                    <div className="col-span-4">اسم المنتج</div>
                    <div className="col-span-2">الفئة</div>
                    <div className="col-span-2">المخزون</div>
                    <div className="col-span-2">السعر</div>
                    <div className="col-span-2 text-left">إجراءات</div>
                </div>

                <AnimatePresence mode="popLayout">
                    {loading ? (
                        [...Array(5)].map((_, i) => (
                            <div key={i} className="glass-panel h-20 rounded-xl animate-pulse bg-white/5" />
                        ))
                    ) : filteredProducts.length === 0 ? (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="text-center py-20 text-gray-500"
                        >
                            <Package className="w-16 h-16 mx-auto mb-4 opacity-20" />
                            <p>لا توجد منتجات تطابق بحثك</p>
                        </motion.div>
                    ) : (
                        filteredProducts.map((product, index) => (
                            <ProductRow key={product.id || index} product={product} index={index} onRefresh={fetchProducts} />
                        ))
                    )}
                </AnimatePresence>
            </div>

        </div>
    )
}

function ProductRow({ product, index, onRefresh }: { product: any, index: number, onRefresh: () => void }) {
    const currentStock = product.current_stock || product.stock || 0
    const minStock = product.min_stock || product.min_stock_level || 5
    const isLowStock = currentStock <= minStock

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="glass-panel p-4 rounded-xl group hover:bg-white/10 transition-all duration-300 md:grid md:grid-cols-12 md:gap-4 md:items-center relative overflow-hidden"
        >
            {/* Left Border Accent */}
            <div className={`absolute left-0 top-0 bottom-0 w-1 ${isLowStock ? 'bg-orange-500' : 'bg-cyan-500'} opacity-0 group-hover:opacity-100 transition-opacity`} />

            {/* Name & Avatar */}
            <div className="col-span-4 flex items-center gap-4 mb-4 md:mb-0">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-gray-800 to-gray-900 border border-white/10 flex items-center justify-center shrink-0">
                    {product.image_path || product.image_url ? (
                        <img src={product.image_path || product.image_url} alt={product.name || product.name_ar || ''} className="w-full h-full object-cover rounded-lg" />
                    ) : (
                        <Package className="text-gray-600 w-6 h-6" />
                    )}
                </div>
                <div>
                    <h3 className="font-bold text-white group-hover:text-cyan-400 transition-colors">{product.name || product.name_ar || product.name_en || 'غير محدد'}</h3>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                        <Barcode className="w-3 h-3" />
                        {product.barcode || '---'}
                    </div>
                </div>
            </div>

            {/* Category */}
            <div className="col-span-2 mb-2 md:mb-0">
                <Badge variant="outline" className="border-white/10 text-gray-400 bg-white/5">
                    {product.category_name || 'عام'}
                </Badge>
            </div>

            {/* Stock */}
            <div className="col-span-2 mb-2 md:mb-0">
                <div className="flex items-center gap-2 mb-1">
                    <span className={`text-sm font-bold ${isLowStock ? 'text-orange-400' : 'text-white'}`}>
                        {currentStock}
                    </span>
                    <span className="text-xs text-gray-500">{product.unit || 'وحدة'}</span>
                </div>
                <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                    <div
                        className={`h-full rounded-full ${isLowStock ? 'bg-orange-500' : 'bg-cyan-500'}`}
                        style={{ width: `${Math.min(100, (currentStock / Math.max(100, minStock * 10)) * 100)}%` }}
                    />
                </div>
                {isLowStock && <span className="text-[10px] text-orange-400 flex items-center gap-1 mt-1"><AlertTriangle className="w-3 h-3" /> مخزون منخفض</span>}
            </div>

            {/* Price */}
            <div className="col-span-2 mb-2 md:mb-0">
                <div className="font-bold text-white text-lg">
                    {(product.selling_price || product.price || 0).toLocaleString()} <span className="text-xs text-gray-500">ر.س</span>
                </div>
                <div className="text-xs text-gray-600">
                    التكلفة: {(product.cost_price || 0).toLocaleString()}
                </div>
            </div>

            {/* Actions */}
            <div className="col-span-2 flex justify-end gap-2 opacity-100 md:opacity-0 group-hover:opacity-100 transition-opacity">
                <ProductForm
                    product={product}
                    onSaved={onRefresh}
                    trigger={
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-cyan-400 hover:text-cyan-300 hover:bg-cyan-400/10">
                            <Edit3 className="w-4 h-4" />
                        </Button>
                    }
                />
                <Button variant="ghost" size="icon" className="h-8 w-8 text-red-400 hover:text-red-300 hover:bg-red-400/10">
                    <Trash2 className="w-4 h-4" />
                </Button>
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400">
                            <MoreVertical className="w-4 h-4" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent className="glass-panel border-white/10">
                        <DropdownMenuItem className="text-white hover:bg-white/5">طباعة باركود</DropdownMenuItem>
                        <DropdownMenuItem className="text-white hover:bg-white/5">حركة الصنف</DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>

        </motion.div>
    )
}
