"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Plus, FolderPlus, Save } from "lucide-react"
import { toast } from "sonner"
import { supabase } from "@/lib/supabase"

interface CategoryFormProps {
    category?: any | null
    onSaved?: () => void
}

export default function CategoryForm({ category, onSaved }: CategoryFormProps) {
    const [open, setOpen] = useState(false)
    const [saving, setSaving] = useState(false)
    const isEditMode = !!category

    const [name, setName] = useState("")
    const [description, setDescription] = useState("")
    const [isActive, setIsActive] = useState(true)

    useEffect(() => {
        if (category) {
            setName(category.name || "")
            setDescription(category.description || "")
            setIsActive(category.status === "active")
            setOpen(true)
        } else {
            resetForm()
        }
    }, [category])

    const resetForm = () => {
        setName("")
        setDescription("")
        setIsActive(true)
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!name.trim()) {
            toast.error("الرجاء إدخال اسم الفئة")
            return
        }

        setSaving(true)
        try {
            const payload = {
                name: name.trim(),
                description: description.trim(),
                is_active: isActive
            }

            let error;
            if (isEditMode) {
                const { error: err } = await supabase.from('categories').update(payload).eq('id', category.id)
                error = err
            } else {
                const { error: err } = await supabase.from('categories').insert(payload)
                error = err
            }

            if (error) throw error

            toast.success(isEditMode ? "تم تحديث الفئة بنجاح" : "تم إضافة الفئة بنجاح")
            setOpen(false)
            resetForm()
            if (onSaved) onSaved()
        } catch (err) {
            console.error("Error saving category:", err)
            toast.error("حدث خطأ أثناء حفظ الفئة")
        } finally {
            setSaving(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={(v) => {
            setOpen(v)
            if (!v && isEditMode && onSaved) onSaved() // Clear selection on close
        }}>
            {!isEditMode && (
                <DialogTrigger asChild>
                    <Button className="bg-blue-600 hover:bg-blue-700">
                        <Plus className="ml-2 h-4 w-4" /> إضافة فئة جديدة
                    </Button>
                </DialogTrigger>
            )}
            <DialogContent>
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <FolderPlus className="h-5 w-5 text-blue-600" />
                        {isEditMode ? "تعديل الفئة" : "إضافة فئة جديدة"}
                    </DialogTitle>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-4 pt-4">
                    <div className="space-y-2">
                        <Label htmlFor="category-name">اسم الفئة *</Label>
                        <Input
                            id="category-name"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="مثال: مشروبات، إلكترونيات..."
                            required
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="category-desc">الوصف</Label>
                        <Textarea
                            id="category-desc"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="وصف مختصر للفئة..."
                            rows={3}
                        />
                    </div>

                    <div className="flex justify-end gap-3 pt-4 border-t">
                        <Button type="button" variant="outline" onClick={() => setOpen(false)} disabled={saving}>
                            إلغاء
                        </Button>
                        <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={saving}>
                            <Save className={`h-4 w-4 ml-2 ${saving ? 'animate-spin' : ''}`} />
                            {isEditMode ? "حفظ التعديلات" : "إضافة الفئة"}
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    )
}
