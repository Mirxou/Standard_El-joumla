"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Plus, UserPlus, MapPin, Phone, Mail, FileText, DollarSign } from "lucide-react"
import { toast } from "sonner"
import { apiClient } from "@/lib/api/client"
import { API_CONFIG } from "@/lib/config/api"

interface CreateSupplierProps {
    onSaved?: () => void;
}

export default function CreateSupplier({ onSaved }: CreateSupplierProps) {
    const [open, setOpen] = useState(false)
    const [isSubmitting, setIsSubmitting] = useState(false)

    const [formData, setFormData] = useState({
        name: "",
        contact_person: "",
        phone: "",
        email: "",
        address: "",
        tax_number: "",
        credit_limit: "",
        notes: ""
    })

    const handleChange = (field: string, value: string) => {
        setFormData((prev) => ({ ...prev, [field]: value }))
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!formData.name.trim()) {
            toast.error("الرجاء إدخال اسم المورد")
            return
        }

        if (!formData.phone.trim()) {
            toast.error("الرجاء إدخال رقم الهاتف")
            return
        }

        try {
            setIsSubmitting(true)

            const payload = {
                name: formData.name,
                contact_person: formData.contact_person,
                phone: formData.phone,
                email: formData.email || null,
                address: formData.address || null,
                tax_number: formData.tax_number || null,
                credit_limit: parseFloat(formData.credit_limit) || 0.0,
                is_active: true
            }

            const result = await apiClient.post(API_CONFIG.ENDPOINTS.SUPPLIERS, payload)

            if (result.error) throw new Error(result.error);

            toast.success("تم إضافة المورد بنجاح!")

            // Reset form
            setFormData({
                name: "",
                contact_person: "",
                phone: "",
                email: "",
                address: "",
                tax_number: "",
                credit_limit: "",
                notes: ""
            })
            setOpen(false)
            if (onSaved) onSaved()

        } catch (e: any) {
            toast.error(e.message || "حدث خطأ أثناء الاتصال بالخادم")
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button className="bg-blue-600 hover:bg-blue-700">
                    <Plus className="h-4 w-4 ml-2" />
                    إضافة مورد جديد
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2 text-xl">
                        <UserPlus className="h-5 w-5 text-blue-600" />
                        إضافة مورد جديد
                    </DialogTitle>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Basic Info */}
                    <div className="bg-blue-50 p-4 rounded-lg space-y-4">
                        <h3 className="font-semibold text-blue-900 flex items-center gap-2">
                            <FileText className="h-4 w-4" />
                            المعلومات الأساسية
                        </h3>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="col-span-2">
                                <Label htmlFor="name">اسم المورد / الشركة *</Label>
                                <Input
                                    id="name"
                                    value={formData.name}
                                    onChange={(e) => handleChange("name", e.target.value)}
                                    placeholder="شركة المثال للتوريد"
                                    required
                                />
                            </div>

                            <div>
                                <Label htmlFor="contact_person">الشخص المسؤول</Label>
                                <Input
                                    id="contact_person"
                                    value={formData.contact_person}
                                    onChange={(e) => handleChange("contact_person", e.target.value)}
                                    placeholder="أحمد محمد"
                                />
                            </div>

                            <div>
                                <Label htmlFor="tax_number">الرقم الضريبي</Label>
                                <Input
                                    id="tax_number"
                                    value={formData.tax_number}
                                    onChange={(e) => handleChange("tax_number", e.target.value)}
                                    placeholder="3000..."
                                />
                            </div>
                        </div>
                    </div>

                    {/* Contact Info */}
                    <div className="bg-green-50 p-4 rounded-lg space-y-4">
                        <h3 className="font-semibold text-green-900 flex items-center gap-2">
                            <Phone className="h-4 w-4" />
                            معلومات الاتصال
                        </h3>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <Label htmlFor="phone">رقم الهاتف *</Label>
                                <Input
                                    id="phone"
                                    value={formData.phone}
                                    onChange={(e) => handleChange("phone", e.target.value)}
                                    placeholder="05xxxxxxxx"
                                    required
                                />
                            </div>

                            <div>
                                <Label htmlFor="email">البريد الإلكتروني</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    value={formData.email}
                                    onChange={(e) => handleChange("email", e.target.value)}
                                    placeholder="info@example.com"
                                />
                            </div>

                            <div className="col-span-2">
                                <Label htmlFor="address">العنوان</Label>
                                <Input
                                    id="address"
                                    value={formData.address}
                                    onChange={(e) => handleChange("address", e.target.value)}
                                    placeholder="المدينة، الحي، الشارع"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Financial Info */}
                    <div className="bg-purple-50 p-4 rounded-lg space-y-4">
                        <h3 className="font-semibold text-purple-900 flex items-center gap-2">
                            <DollarSign className="h-4 w-4" />
                            المعلومات المالية
                        </h3>

                        <div>
                            <Label htmlFor="credit_limit">حد الائتمان (ر.س)</Label>
                            <Input
                                id="credit_limit"
                                type="number"
                                value={formData.credit_limit}
                                onChange={(e) => handleChange("credit_limit", e.target.value)}
                                placeholder="0.00"
                            />
                            <p className="text-xs text-gray-500 mt-1">الحد الأقصى للمديونية المسموح بها لهذا المورد</p>
                        </div>
                    </div>

                    <div className="flex justify-end gap-3 pt-4 border-t">
                        <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                            إلغاء
                        </Button>
                        <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={isSubmitting}>
                            {isSubmitting ? "جاري الحفظ..." :
                                <> <Plus className="h-4 w-4 ml-2" /> حفظ المورد </>
                            }
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    )
}
