"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Plus, ShoppingCart, Trash2, Calendar as CalendarIcon, Search } from "lucide-react"
import { toast } from "sonner"
import { apiClient } from "@/lib/api/client"
import { API_CONFIG } from "@/lib/config/api"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Calendar } from "@/components/ui/calendar"
import { cn } from "@/lib/utils"
import { format } from "date-fns"
import { ar } from "date-fns/locale"

interface CreatePurchaseProps {
    onSaved?: () => void;
}

export default function CreatePurchase({ onSaved }: CreatePurchaseProps) {
    const [open, setOpen] = useState(false)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [suppliers, setSuppliers] = useState<any[]>([])
    const [products, setProducts] = useState<any[]>([])

    // Form State
    const [supplierId, setSupplierId] = useState("")
    const [purchaseDate, setPurchaseDate] = useState<Date | undefined>(new Date())
    const [expectedDate, setExpectedDate] = useState<Date | undefined>()
    const [paymentTerms, setPaymentTerms] = useState("نقدي")
    const [notes, setNotes] = useState("")

    // Items State
    const [items, setItems] = useState<any[]>([])
    const [currentItem, setCurrentItem] = useState({
        productId: "",
        quantity: 1,
        unitCost: 0
    })

    useEffect(() => {
        if (open) {
            loadSuppliers()
            loadProducts()
        }
    }, [open])

    const loadSuppliers = async () => {
        try {
            const data = await apiClient.get<any[]>(API_CONFIG.ENDPOINTS.SUPPLIERS)
            const suppliersArray = Array.isArray(data) ? data : (data as any)?.items || (data as any)?.suppliers || []
            setSuppliers(suppliersArray)
        } catch (error: any) {
            console.error("Error loading suppliers:", error)
            setSuppliers([])
        }
    }

    const loadProducts = async () => {
        try {
            const data = await apiClient.get<any>(API_CONFIG.ENDPOINTS.PRODUCTS)
            const productsArray = Array.isArray(data) ? data : (data as any)?.products || (data as any)?.items || []
            setProducts(productsArray)
        } catch (error: any) {
            console.error("Error loading products:", error)
            setProducts([])
        }
    }

    const handleAddItem = () => {
        if (!currentItem.productId) {
            toast.error("الرجاء اختيار منتج")
            return
        }
        const product = products.find(p => p.id === parseInt(currentItem.productId))
        if (!product) return

        const newItem = {
            id: Date.now(), // Temp ID
            product_id: product.id,
            product_name: product.name,
            quantity: currentItem.quantity,
            unit_cost: currentItem.unitCost || product.cost_price,
            total: (currentItem.quantity) * (currentItem.unitCost || product.cost_price)
        }

        setItems([...items, newItem])
        setCurrentItem({ productId: "", quantity: 1, unitCost: 0 }) // Reset
    }

    const handleRemoveItem = (id: number) => {
        setItems(items.filter(i => i.id !== id))
    }

    const calculateTotal = () => {
        return items.reduce((sum, item) => sum + item.total, 0)
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!supplierId) {
            toast.error("الرجاء اختيار المورد")
            return
        }

        if (items.length === 0) {
            toast.error("الرجاء إضافة منتجات للفاتورة")
            return
        }

        try {
            setIsSubmitting(true)

            const payload = {
                supplier_id: parseInt(supplierId),
                purchase_date: purchaseDate ? format(purchaseDate, "yyyy-MM-dd") : null,
                expected_delivery_date: expectedDate ? format(expectedDate, "yyyy-MM-dd") : null,
                payment_terms: paymentTerms,
                notes: notes,
                items: items.map(i => ({
                    product_id: i.product_id,
                    quantity: i.quantity,
                    unit_cost: i.unit_cost
                }))
            }

            const result = await apiClient.post('/api/v1/purchases', payload)

            if (!result || (result as any).error) {
                throw new Error((result as any)?.error || "فشل إنشاء أمر الشراء")
            }

            toast.success("تم إنشاء أمر الشراء بنجاح!")
            setOpen(false)
            setItems([])
            setSupplierId("")
            if (onSaved) onSaved()

        } catch (e: any) {
            toast.error(e.message || "حدث خطأ أثناء الحفظ")
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button className="bg-blue-600 hover:bg-blue-700">
                    <Plus className="h-4 w-4 ml-2" />
                    أمر شراء جديد
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2 text-xl">
                        <ShoppingCart className="h-5 w-5 text-blue-600" />
                        إنشاء أمر شراء جديد
                    </DialogTitle>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Header Info */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg">
                        <div>
                            <Label>المورد *</Label>
                            <Select value={supplierId} onValueChange={setSupplierId}>
                                <SelectTrigger className="bg-white">
                                    <SelectValue placeholder="اختر المورد" />
                                </SelectTrigger>
                                <SelectContent>
                                    {suppliers.map(s => (
                                        <SelectItem key={s.id} value={s.id.toString()}>{s.name}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div>
                            <Label>تاريخ الشراء</Label>
                            <Popover>
                                <PopoverTrigger asChild>
                                    <Button
                                        variant={"outline"}
                                        className={cn(
                                            "w-full justify-start text-left font-normal bg-white",
                                            !purchaseDate && "text-muted-foreground"
                                        )}
                                    >
                                        <CalendarIcon className="mr-2 h-4 w-4" />
                                        {purchaseDate ? format(purchaseDate, "PPP", { locale: ar }) : <span>اختر تاريخ</span>}
                                    </Button>
                                </PopoverTrigger>
                                <PopoverContent className="w-auto p-0">
                                    <Calendar
                                        mode="single"
                                        selected={purchaseDate}
                                        onSelect={setPurchaseDate}
                                        initialFocus
                                    />
                                </PopoverContent>
                            </Popover>
                        </div>
                        <div>
                            <Label>شروط الدفع</Label>
                            <Select value={paymentTerms} onValueChange={setPaymentTerms}>
                                <SelectTrigger className="bg-white">
                                    <SelectValue placeholder="شروط الدفع" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="نقدي">نقدي</SelectItem>
                                    <SelectItem value="آجل 30 يوم">آجل 30 يوم</SelectItem>
                                    <SelectItem value="آجل 60 يوم">آجل 60 يوم</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div>
                            <Label>تاريخ التوصيل المتوقع</Label>
                            <Popover>
                                <PopoverTrigger asChild>
                                    <Button
                                        variant={"outline"}
                                        className={cn(
                                            "w-full justify-start text-left font-normal bg-white",
                                            !expectedDate && "text-muted-foreground"
                                        )}
                                    >
                                        <CalendarIcon className="mr-2 h-4 w-4" />
                                        {expectedDate ? format(expectedDate, "PPP", { locale: ar }) : <span>اختر تاريخ</span>}
                                    </Button>
                                </PopoverTrigger>
                                <PopoverContent className="w-auto p-0">
                                    <Calendar
                                        mode="single"
                                        selected={expectedDate}
                                        onSelect={setExpectedDate}
                                        initialFocus
                                    />
                                </PopoverContent>
                            </Popover>
                        </div>
                    </div>

                    {/* Items Section */}
                    <div className="border rounded-lg p-4">
                        <h3 className="font-semibold mb-3">المنتجات</h3>

                        {/* Add Item Form */}
                        <div className="flex flex-wrap gap-2 items-end mb-4 bg-blue-50 p-3 rounded-lg">
                            <div className="flex-1 min-w-[200px]">
                                <Label className="text-xs mb-1 block">المنتج</Label>
                                <Select value={currentItem.productId} onValueChange={(val) => setCurrentItem({ ...currentItem, productId: val })}>
                                    <SelectTrigger className="bg-white h-9">
                                        <SelectValue placeholder="اختر المنتج" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {products.map(p => (
                                            <SelectItem key={p.id} value={p.id.toString()}>{p.name}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="w-24">
                                <Label className="text-xs mb-1 block">الكمية</Label>
                                <Input
                                    type="number"
                                    className="bg-white h-9"
                                    min="1"
                                    value={currentItem.quantity}
                                    onChange={(e) => setCurrentItem({ ...currentItem, quantity: parseInt(e.target.value) || 1 })}
                                />
                            </div>
                            <div className="w-32">
                                <Label className="text-xs mb-1 block">سعر الشراء (للوحدة)</Label>
                                <Input
                                    type="number"
                                    className="bg-white h-9"
                                    min="0"
                                    step="0.01"
                                    value={currentItem.unitCost}
                                    onChange={(e) => setCurrentItem({ ...currentItem, unitCost: parseFloat(e.target.value) || 0 })}
                                />
                            </div>
                            <Button type="button" onClick={handleAddItem} className="h-9 bg-blue-600 hover:bg-blue-700">
                                <Plus className="h-4 w-4" />
                            </Button>
                        </div>

                        {/* Items Table */}
                        {items.length > 0 ? (
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead className="bg-gray-100">
                                        <tr>
                                            <th className="p-2 text-right">المنتج</th>
                                            <th className="p-2 text-center">الكمية</th>
                                            <th className="p-2 text-center">السعر</th>
                                            <th className="p-2 text-center">الإجمالي</th>
                                            <th className="p-2 text-center"></th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {items.map((item) => (
                                            <tr key={item.id} className="border-b">
                                                <td className="p-2">{item.product_name}</td>
                                                <td className="p-2 text-center">{item.quantity}</td>
                                                <td className="p-2 text-center">{item.unit_cost}</td>
                                                <td className="p-2 text-center">{item.total.toLocaleString()}</td>
                                                <td className="p-2 text-center">
                                                    <Button type="button" variant="ghost" size="sm" onClick={() => handleRemoveItem(item.id)} className="text-red-500 hover:text-red-700">
                                                        <Trash2 className="h-4 w-4" />
                                                    </Button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                    <tfoot className="bg-gray-50 font-bold">
                                        <tr>
                                            <td colSpan={3} className="p-2 text-left pl-4">المجموع الكلي:</td>
                                            <td className="p-2 text-center text-blue-600">{calculateTotal().toLocaleString()} ر.س</td>
                                            <td></td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        ) : (
                            <div className="text-center py-8 text-gray-400 border-2 border-dashed rounded-lg">
                                لا توجد منتجات مضافة
                            </div>
                        )}
                    </div>

                    <div className="flex justify-end gap-3 pt-4 border-t">
                        <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                            إلغاء
                        </Button>
                        <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={isSubmitting}>
                            {isSubmitting ? "جاري الحفظ..." : "تأكيد الطلب"}
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    )
}
