"use client"

import { useState, useEffect, useRef } from "react"
import {
    Search,
    ShoppingCart,
    Trash2,
    CreditCard,
    Receipt,
    Plus,
    Minus,
    User,
    Settings,
    ScanBarcode,
    Delete,
    X
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { apiClient } from "@/lib/api/client"
import { API_CONFIG } from "@/lib/config/api"
import { toast } from "sonner"
import { motion, AnimatePresence } from "framer-motion"

// Types
interface CartItem {
    id: string
    productId: number
    name: string
    price: number
    quantity: number
    image?: string
}

// Ensure products service is imported
import { productsService } from "@/lib/api/services/products"
import { salesService } from "@/lib/api/services/sales"

export default function SalesManagement() {
    const [products, setProducts] = useState<any[]>([])
    const [cart, setCart] = useState<CartItem[]>([])
    const [searchQuery, setSearchQuery] = useState("")
    const [loading, setLoading] = useState(true)
    const [showPayModal, setShowPayModal] = useState(false)
    const searchInputRef = useRef<HTMLInputElement>(null)

    useEffect(() => {
        fetchProducts()
    }, [])

    const fetchProducts = async () => {
        try {
            setLoading(true)
            const data = await productsService.getAll()
            // Map backend product to frontend format if needed, but service handles standard response
            setProducts(Array.isArray(data) ? data : [])
        } catch (error) {
            console.error("Error fetching products:", error)
            toast.error("فشل تحميل المنتجات")
        } finally {
            setLoading(false)
        }
    }

    const handlePayment = async () => {
        if (cart.length === 0) return

        try {
            setLoading(true)

            const saleData = {
                payment_method: "نقدي", // Can be dynamic later
                items: cart.map(item => ({
                    product_id: item.productId,
                    quantity: item.quantity,
                    unit_price: item.price,
                    discount_amount: 0,
                    tax_amount: 0
                })),
                paid_amount: cart.reduce((sum, item) => sum + (item.price * item.quantity), 0),
                discount_amount: 0,
                tax_amount: 0
            }

            await salesService.create(saleData)

            toast.success("تم إتمام العملية بنجاح!")
            setCart([])
            setShowPayModal(false)
            // Refresh products to show updated stock
            fetchProducts()

        } catch (error) {
            console.error("Payment failed:", error)
            toast.error("فشل إتمام عملية البيع")
        } finally {
            setLoading(false)
        }
    }

    // Keyboard Shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'F2') searchInputRef.current?.focus()
            if (e.key === 'F12') handlePay()
        }
        window.addEventListener('keydown', handleKeyDown)
        return () => window.removeEventListener('keydown', handleKeyDown)
    }, [cart])



    const addToCart = (product: any) => {
        setCart(prev => {
            const existing = prev.find(item => item.productId === product.id)
            if (existing) {
                return prev.map(item =>
                    item.productId === product.id
                        ? { ...item, quantity: item.quantity + 1 }
                        : item
                )
            }
            return [...prev, {
                id: Math.random().toString(36),
                productId: product.id,
                name: product.name || product.name_ar,
                price: product.selling_price,
                quantity: 1,
                image: product.image_url
            }]
        })
        toast.success("تمت الإضافة للسلة")
    }

    const removeFromCart = (id: string) => {
        setCart(prev => prev.filter(item => item.id !== id))
    }

    const updateQuantity = (id: string, delta: number) => {
        setCart(prev => prev.map(item => {
            if (item.id === id) {
                const newQty = Math.max(1, item.quantity + delta)
                return { ...item, quantity: newQty }
            }
            return item
        }))
    }

    const cartTotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0)
    const taxAmount = cartTotal * 0.15
    const finalTotal = cartTotal + taxAmount

    const handlePay = () => {
        if (cart.length === 0) return toast.error("السلة فارغة")
        toast.success("تم إنشاء الفاتورة بنجاح")
        setCart([])
    }

    const filteredProducts = products.filter(p =>
        (p.name || p.name_ar)?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.barcode?.includes(searchQuery)
    )

    return (
        <div className="h-[calc(100vh-100px)] flex gap-6 overflow-hidden">

            {/* Left Column: Product Grid */}
            <div className="flex-1 flex flex-col gap-4 min-w-0">

                {/* Search Bar */}
                <div className="glass-panel p-4 rounded-2xl flex gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 h-5 w-5" />
                        <Input
                            ref={searchInputRef}
                            placeholder="بحث عن منتج (F2)..."
                            className="pl-4 pr-12 h-12 text-lg bg-white/5 border-white/10 focus-visible:ring-cyan-500/50"
                            value={searchQuery}
                            onChange={e => setSearchQuery(e.target.value)}
                            autoFocus
                        />
                        <div className="absolute left-3 top-1/2 -translate-y-1/2 flex gap-2">
                            <Badge variant="outline" className="text-xs text-gray-500 border-white/10">ESC للمسح</Badge>
                        </div>
                    </div>
                    <Button className="h-12 w-12 glass-button" variant="outline">
                        <ScanBarcode className="h-5 w-5" />
                    </Button>
                </div>

                {/* Categories / Grid */}
                <ScrollArea className="flex-1 rounded-2xl">
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 pb-20">
                        {filteredProducts.map(product => (
                            <motion.button
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                key={product.id}
                                onClick={() => addToCart(product)}
                                className="glass-panel p-4 rounded-xl flex flex-col items-center gap-3 text-center group hover:bg-cyan-500/10 hover:border-cyan-500/30 transition-all cursor-pointer h-full"
                            >
                                <div className="w-20 h-20 rounded-lg bg-white/5 flex items-center justify-center">
                                    {product.image_url ? (
                                        <img src={product.image_url} alt="" className="w-full h-full object-cover rounded-lg" />
                                    ) : (
                                        <span className="text-2xl font-bold text-gray-600">{(product.name || product.name_ar)?.[0]}</span>
                                    )}
                                </div>
                                <div className="w-full">
                                    <h3 className="font-medium text-white truncate w-full text-sm">{product.name || product.name_ar}</h3>
                                    <p className="text-cyan-400 font-bold mt-1">{product.selling_price} ر.س</p>
                                </div>
                                <div className="text-xs text-gray-500">
                                    مخزون: {product.current_stock}
                                </div>
                            </motion.button>
                        ))}
                    </div>
                </ScrollArea>
            </div>

            {/* Right Column: Glass Receipt */}
            <div className="w-[400px] flex flex-col glass-panel rounded-2xl overflow-hidden shadow-2xl shrink-0">

                {/* Cart Header */}
                <div className="p-4 border-b border-white/10 bg-white/5 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <ShoppingCart className="text-cyan-400 h-5 w-5" />
                        <h2 className="font-bold text-white">سلة المشتريات</h2>
                    </div>
                    <Button variant="ghost" size="icon" className="text-red-400 hover:bg-red-400/10" onClick={() => setCart([])}>
                        <Trash2 className="h-4 w-4" />
                    </Button>
                </div>

                {/* Cart Items */}
                <ScrollArea className="flex-1 bg-black/20">
                    <div className="p-4 space-y-3">
                        <AnimatePresence>
                            {cart.map(item => (
                                <motion.div
                                    key={item.id}
                                    layout
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: 20 }}
                                    className="glass-panel p-3 rounded-xl flex gap-3 items-center group relative overflow-hidden"
                                >
                                    <div className="w-12 h-12 bg-white/5 rounded-lg flex items-center justify-center font-bold text-gray-500 shrink-0">
                                        {item.quantity}x
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h4 className="font-medium text-gray-200 truncate">{item.name}</h4>
                                        <p className="text-cyan-400 font-bold">{item.price * item.quantity} ر.س</p>
                                    </div>

                                    <div className="flex flex-col gap-1">
                                        <Button
                                            size="icon"
                                            variant="ghost"
                                            className="h-6 w-6 rounded-full hover:bg-white/10"
                                            onClick={() => updateQuantity(item.id, 1)}
                                        >
                                            <Plus className="h-3 w-3" />
                                        </Button>
                                        <Button
                                            size="icon"
                                            variant="ghost"
                                            className="h-6 w-6 rounded-full hover:bg-white/10"
                                            onClick={() => updateQuantity(item.id, -1)}
                                            disabled={item.quantity <= 1}
                                        >
                                            <Minus className="h-3 w-3" />
                                        </Button>
                                    </div>

                                    <Button
                                        size="icon"
                                        variant="ghost"
                                        className="absolute left-2 opacity-0 group-hover:opacity-100 transition-opacity text-red-400"
                                        onClick={() => removeFromCart(item.id)}
                                    >
                                        <X className="h-4 w-4" />
                                    </Button>
                                </motion.div>
                            ))}
                        </AnimatePresence>

                        {cart.length === 0 && (
                            <div className="text-center py-20 text-gray-500">
                                <Receipt className="w-16 h-16 mx-auto mb-4 opacity-20" />
                                <p>السلة فارغة</p>
                                <p className="text-xs mt-2 opacity-50">اضغط على المنتجات لإضافتها</p>
                            </div>
                        )}
                    </div>
                </ScrollArea>

                {/* Cart Footer / Totals */}
                <div className="p-4 border-t border-white/10 bg-white/5 space-y-4">
                    <div className="space-y-2 text-sm">
                        <div className="flex justify-between text-gray-400">
                            <span>المجموع الفرعي</span>
                            <span>{cartTotal.toLocaleString()} ر.س</span>
                        </div>
                        <div className="flex justify-between text-gray-400">
                            <span>الضريبة (15%)</span>
                            <span>{taxAmount.toLocaleString()} ر.س</span>
                        </div>
                        <Separator className="bg-white/10 my-2" />
                        <div className="flex justify-between text-xl font-bold text-white">
                            <span>الإجمالي</span>
                            <span className="text-cyan-400">{finalTotal.toLocaleString()} ر.س</span>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <Button
                            variant="outline"
                            className="h-12 glass-button border-white/10 text-gray-300"
                        >
                            <User className="h-4 w-4 mr-2" />
                            عميل
                        </Button>
                        <Button
                            className="h-12 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white font-bold text-lg shadow-lg shadow-green-500/20"
                            onClick={handlePayment}
                        >
                            دفع (F12)
                            <CreditCard className="ml-2 h-5 w-5" />
                        </Button>
                    </div>
                </div>

            </div>
        </div>
    )
}
