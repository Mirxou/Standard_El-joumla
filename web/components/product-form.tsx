"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Plus, Package, Save, Loader2 } from "lucide-react"
import { toast } from "sonner"
import { supabase } from "@/lib/supabase"
import { fetchFromAPI } from "@/lib/db/client"

interface ProductFormProps {
    product?: any | null
    onSaved?: () => void
}

export default function ProductForm({ product, onSaved }: ProductFormProps) {
    const [open, setOpen] = useState(false)
    const [saving, setSaving] = useState(false)
    const [categories, setCategories] = useState<any[]>([])
    const [loadingCats, setLoadingCats] = useState(false)

    const isEditMode = !!product

    const [formData, setFormData] = useState({
        name: "",
        barcode: "",
        category_id: "",
        selling_price: "0",
        cost_price: "0",
        min_stock: "10",
        current_stock: "0",
        unit: "قطعة",
        description: "",
    })

    useEffect(() => {
        if (open) {
            loadCategories()
        }
    }, [open])

    useEffect(() => {
        if (product) {
            setFormData({
                name: product.name || "",
                barcode: product.barcode || product.sku || "",
                category_id: product.category_id ? Number(product.category_id).toString() : "",
                selling_price: product.selling_price?.toString() || product.price?.toString() || "0",
                cost_price: product.cost_price?.toString() || "0",
                min_stock: product.min_stock?.toString() || "10",
                current_stock: product.current_stock?.toString() || product.stock?.toString() || "0",
                unit: product.unit || "قطعة",
                description: product.description || "",
            })
            setOpen(true)
        } else {
            resetForm()
        }
    }, [product])

    async function loadCategories() {
        setLoadingCats(true)
        try {
            const { data, error } = await supabase.from('categories').select('*').eq('is_active', true)
            if (error) throw error
            const cats = Array.isArray(data) ? data : (data?.categories || [])
            setCategories(cats)
        } catch (err) {
            console.error("Error loading categories:", err)
        } finally {
            setLoadingCats(false)
        }
    }

    const resetForm = () => {
        setFormData({
            name: "",
            barcode: "",
            category_id: "",
            selling_price: "0",
            cost_price: "0",
            min_stock: "10",
            current_stock: "0",
            unit: "قطعة",
            description: "",
        })
    }

    const handleChange = (field: string, value: string) => {
        setFormData(prev => ({ ...prev, [field]: value }))
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!formData.name.trim()) {
            toast.error("الرجاء إدخال اسم المنتج")
            return
        }

        setSaving(true)
        try {
            const payload = {
                name: formData.name.trim(),
                barcode: formData.barcode.trim() || null,
                category_id: formData.category_id ? parseInt(formData.category_id) : null,
                selling_price: parseFloat(formData.selling_price) || 0,
                cost_price: parseFloat(formData.cost_price) || 0,
                min_stock: parseInt(formData.min_stock) || 0,
                current_stock: parseInt(formData.current_stock) || 0,
                unit: formData.unit,
                description: formData.description.trim() || null,
                is_active: true
            }

            let error;
            if (isEditMode) {
                const { error: err } = await supabase.from('products').update(payload).eq('id', product.id)
                error = err
            } else {
                const { error: err } = await supabase.from('products').insert(payload)
                error = err
            }

            if (error) throw error

            toast.success(isEditMode ? "تم تحديث المنتج بنجاح" : "تم إضافة المنتج بنجاح")
            setOpen(false)
            resetForm()
            if (onSaved) onSaved()
        } catch (err) {
            console.error("Error saving product:", err)
            toast.error("حدث خطأ أثناء حفظ المنتج")
        } finally {
            setSaving(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={(v) => {
            setOpen(v)
            if (!v && isEditMode && onSaved) onSaved()
        }}>
            {!isEditMode && (
                <DialogTrigger asChild>
                    <Button className="bg-blue-600 hover:bg-blue-700">
                        <Plus className="ml-2 h-4 w-4" /> إضافة منتج
                    </Button>
                </DialogTrigger>
            )}
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Package className="h-5 w-5 text-blue-600" />
                        {isEditMode ? "تعديل المنتج" : "إضافة منتج جديد"}
                    </DialogTitle>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-4 pt-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="prod-name">اسم المنتج *</Label>
                            <Input
                                id="prod-name"
                                value={formData.name}
                                onChange={(e) => handleChange("name", e.target.value)}
                                placeholder="مثال: زيت زيتون 1 لتر"
                                required
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="prod-barcode">الباركود / SKU</Label>
                            <Input
                                id="prod-barcode"
                                value={formData.barcode}
                                onChange={(e) => handleChange("barcode", e.target.value)}
                                placeholder="رقم الباركود"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="prod-cat">الفئة</Label>
                            <Select value={formData.category_id} onValueChange={(v) => handleChange("category_id", v)}>
                                <SelectTrigger id="prod-cat">
                                    <SelectValue placeholder={loadingCats ? "جاري التحميل..." : "اختر الفئة"} />
                                </SelectTrigger>
                                <SelectContent>
                                    {categories.map((cat) => (
                                        <SelectItem key={cat.id} value={cat.id.toString()}>
                                            {cat.name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="prod-unit">الوحدة</Label>
                            <Input
                                id="prod-unit"
                                value={formData.unit}
                                onChange={(e) => handleChange("unit", e.target.value)}
                                placeholder="مثال: قطعة، صندوق، كجم"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="prod-cost">سعر التكلفة</Label>
                            <Input
                                id="prod-cost"
                                type="number"
                                step="0.01"
                                value={formData.cost_price}
                                onChange={(e) => handleChange("cost_price", e.target.value)}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="prod-price">سعر البيع *</Label>
                            <Input
                                id="prod-price"
                                type="number"
                                step="0.01"
                                value={formData.selling_price}
                                onChange={(e) => handleChange("selling_price", e.target.value)}
                                required
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="prod-stock">المخزون الحالي</Label>
                            <Input
                                id="prod-stock"
                                type="number"
                                value={formData.current_stock}
                                onChange={(e) => handleChange("current_stock", e.target.value)}
                                disabled={isEditMode} // يفضل تغيير المخزون من حركات المخزون
                            />
                            {isEditMode && <p className="text-[10px] text-gray-400">لتغيير المخزون، استخدم شاشة "حركات المخزون"</p>}
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="prod-min">الحد الأدنى</Label>
                            <Input
                                id="prod-min"
                                type="number"
                                value={formData.min_stock}
                                onChange={(e) => handleChange("min_stock", e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="prod-desc">الوصف</Label>
                        <Textarea
                            id="prod-desc"
                            value={formData.description}
                            onChange={(e) => handleChange("description", e.target.value)}
                            placeholder="وصف إضافي للمنتج..."
                            rows={3}
                        />
                    </div>

                    <div className="flex justify-end gap-3 pt-4 border-t">
                        <Button type="button" variant="outline" onClick={() => setOpen(false)} disabled={saving}>
                            إلغاء
                        </Button>
                        <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={saving}>
                            <Save className={`h-4 w-4 ml-2 ${saving ? 'animate-spin' : ''}`} />
                            {isEditMode ? "حفظ التعديلات" : "إضافة المنتج"}
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    )
}
