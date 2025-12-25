"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Plus, RotateCcw, Trash2, Calendar as CalendarIcon, Search } from "lucide-react"
import { toast } from "sonner"
import { fetchFromAPI } from "@/lib/db/client"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Calendar } from "@/components/ui/calendar"
import { cn } from "@/lib/utils"
import { format } from "date-fns"
import { ar } from "date-fns/locale"

interface CreateReturnProps {
    onSaved?: () => void;
}

export default function CreateReturn({ onSaved }: CreateReturnProps) {
    const [open, setOpen] = useState(false)
    const [isSubmitting, setIsSubmitting] = useState(false)

    // Data State
    const [customers, setCustomers] = useState<any[]>([])
    const [suppliers, setSuppliers] = useState<any[]>([])
    const [products, setProducts] = useState<any[]>([])

    // Form State
    const [returnType, setReturnType] = useState("SALE_RETURN")
    const [customerId, setCustomerId] = useState("")
    const [supplierId, setSupplierId] = useState("")
    const [returnDate, setReturnDate] = useState<Date | undefined>(new Date())
    const [returnReason, setReturnReason] = useState("OTHER")
    const [notes, setNotes] = useState("")

    // Items State
    const [items, setItems] = useState<any[]>([])
    const [currentItem, setCurrentItem] = useState({
        productId: "",
        quantity: 1,
        unitPrice: 0
    })

    useEffect(() => {
        if (open) {
            loadData()
        }
    }, [open, returnType])

    const loadData = async () => {
        // Load Products
        try {
            const prodData = await fetchFromAPI('/products')
            if (prodData && Array.isArray(prodData.products)) setProducts(prodData.products)
        } catch (e) { console.error(e) }

        // Load Customers or Suppliers based on type
        if (returnType === "SALE_RETURN") {
            // We don't have a direct /customers endpoint exposed in routes.py yet (only users)
            // But assuming it might exist or we use "users" for simplified customer list
            // For now, I'll skip customer loading or mock it if strictly needed.
            // Actually, let's assume we can fetch users or customers.
            // Checked routes.py: `/users` exists. Let's use it as placeholder for customers.
        } else {
            try {
                const suppData = await fetchFromAPI('/suppliers')
                if (Array.isArray(suppData)) setSuppliers(suppData)
            } catch (e) { console.error(e) }
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
            id: Date.now(),
            product_id: product.id,
            product_name: product.name,
            quantity: currentItem.quantity,
            unit_price: currentItem.unitPrice || product.selling_price,
            total: (currentItem.quantity) * (currentItem.unitPrice || product.selling_price)
        }

        setItems([...items, newItem])
        setCurrentItem({ productId: "", quantity: 1, unitPrice: 0 })
    }

    const handleRemoveItem = (id: number) => {
        setItems(items.filter(i => i.id !== id))
    }

    const calculateTotal = () => {
        return items.reduce((sum, item) => sum + item.total, 0)
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (items.length === 0) {
            toast.error("الرجاء إضافة منتجات")
            return
        }

        try {
            setIsSubmitting(true)

            const payload = {
                return_type: returnType,
                customer_id: returnType === "SALE_RETURN" ? (customerId ? parseInt(customerId) : null) : null,
                supplier_id: returnType === "PURCHASE_RETURN" ? (supplierId ? parseInt(supplierId) : null) : null,
                return_date: returnDate ? format(returnDate, "yyyy-MM-dd") : null,
                return_reason: returnReason,
                notes: notes,
                items: items.map(i => ({
                    product_id: i.product_id,
                    quantity: i.quantity,
                    unit_price: i.unit_price
                }))
            }

            const result = await fetchFromAPI('/returns', {
                method: 'POST',
                body: payload
            });

            if (result.error) throw new Error(result.error);

            toast.success("تم إنشاء المرتجع بنجاح!")
            setOpen(false)
            setItems([])
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
                <Button className="bg-orange-600 hover:bg-orange-700">
                    <Plus className="h-4 w-4 ml-2" />
                    مرتجع جديد
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2 text-xl">
                        <RotateCcw className="h-5 w-5 text-orange-600" />
                        إنشاء مرتجع جديد
                    </DialogTitle>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Header Info */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg">
                        <div>
                            <Label>نوع المرتجع</Label>
                            <Select value={returnType} onValueChange={setReturnType}>
                                <SelectTrigger className="bg-white">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="SALE_RETURN">مرتجع مبيعات (من عميل)</SelectItem>
                                    <SelectItem value="PURCHASE_RETURN">مرتجع مشتريات (لمورد)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {returnType === "PURCHASE_RETURN" && (
                            <div>
                                <Label>المورد</Label>
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
                        )}

                        <div>
                            <Label>تاريخ المرتجع</Label>
                            <Popover>
                                <PopoverTrigger asChild>
                                    <Button
                                        variant={"outline"}
                                        className={cn(
                                            "w-full justify-start text-left font-normal bg-white",
                                            !returnDate && "text-muted-foreground"
                                        )}
                                    >
                                        <CalendarIcon className="mr-2 h-4 w-4" />
                                        {returnDate ? format(returnDate, "PPP", { locale: ar }) : <span>اختر تاريخ</span>}
                                    </Button>
                                </PopoverTrigger>
                                <PopoverContent className="w-auto p-0">
                                    <Calendar
                                        mode="single"
                                        selected={returnDate}
                                        onSelect={setReturnDate}
                                        initialFocus
                                    />
                                </PopoverContent>
                            </Popover>
                        </div>

                        <div>
                            <Label>سبب الإرجاع</Label>
                            <Select value={returnReason} onValueChange={setReturnReason}>
                                <SelectTrigger className="bg-white">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="DEFECTIVE">معيب / تالف</SelectItem>
                                    <SelectItem value="WRONG_ITEM">منتج خاطئ</SelectItem>
                                    <SelectItem value="CUSTOMER_REQUEST">طلب العميل</SelectItem>
                                    <SelectItem value="EXPIRED">منتهي الصلاحية</SelectItem>
                                    <SelectItem value="OTHER">أخرى</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    {/* Items Section */}
                    <div className="border rounded-lg p-4">
                        <h3 className="font-semibold mb-3">المنتجات المرتجعة</h3>

                        <div className="flex flex-wrap gap-2 items-end mb-4 bg-orange-50 p-3 rounded-lg">
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
                                <Label className="text-xs mb-1 block">السعر (للوحدة)</Label>
                                <Input
                                    type="number"
                                    className="bg-white h-9"
                                    min="0"
                                    step="0.01"
                                    value={currentItem.unitPrice}
                                    onChange={(e) => setCurrentItem({ ...currentItem, unitPrice: parseFloat(e.target.value) || 0 })}
                                />
                            </div>
                            <Button type="button" onClick={handleAddItem} className="h-9 bg-orange-600 hover:bg-orange-700">
                                <Plus className="h-4 w-4" />
                            </Button>
                        </div>

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
                                                <td className="p-2 text-center">{item.unit_price}</td>
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
                                            <td className="p-2 text-center text-orange-600">{calculateTotal().toLocaleString()} ر.س</td>
                                            <td></td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        ) : (
                            <div className="text-center py-8 text-gray-400 border-2 border-dashed rounded-lg">
                                لا توجد منتجات
                            </div>
                        )}
                    </div>

                    <div className="flex justify-end gap-3 pt-4 border-t">
                        <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                            إلغاء
                        </Button>
                        <Button type="submit" className="bg-orange-600 hover:bg-orange-700" disabled={isSubmitting}>
                            {isSubmitting ? "جاري الحفظ..." : "تأكيد المرتجع"}
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    )
}
