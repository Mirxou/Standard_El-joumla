"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import { Plus, Warehouse, MapPin, Users, Package } from "lucide-react"
import { toast } from "sonner"
import { warehousesService } from "@/lib/api/services/warehouses"

interface CreateWarehouseProps {
  onSaved?: () => void;
}

export default function CreateWarehouse({ onSaved }: CreateWarehouseProps) {
  const [open, setOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState({
    name: "",
    location: "",
    address: "",
    city: "",
    manager: "",
    phone: "",
    email: "",
    capacity: "",
    description: "",
    categories: [] as string[],
  })

  const availableCategories = [
    "مواد غذائية",
    "منتجات النظافة",
    "صحة وجمال",
    "إلكترونيات",
    "حلويات",
    "مشروبات",
    "منتجات العناية",
    "أجهزة ذكية",
    "مأكولات خفيفة",
    "أدوات منزلية",
  ]

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleCategoryToggle = (category: string) => {
    setFormData((prev) => ({
      ...prev,
      categories: prev.categories.includes(category)
        ? prev.categories.filter((c) => c !== category)
        : [...prev.categories, category],
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.name.trim()) {
      toast.error("الرجاء إدخال اسم المستودع")
      return
    }

    if (!formData.location.trim()) {
      toast.error("الرجاء إدخال الموقع")
      return
    }

    if (!formData.manager.trim()) {
      toast.error("الرجاء إدخال اسم المدير")
      return
    }

    if (!formData.capacity || parseInt(formData.capacity) <= 0) {
      toast.error("الرجاء إدخال السعة الإجمالية بشكل صحيح")
      return
    }

    if (formData.categories.length === 0) {
      toast.error("الرجاء اختيار فئة واحدة على الأقل")
      return
    }

    // Generate a random code for now if not provided (Backend requires it)
    const warehouseCode = `WH-${Math.floor(Math.random() * 10000)}`

    const payload = {
      code: warehouseCode,
      name: formData.name,
      address: formData.address,
      city: formData.city,
      manager_name: formData.manager,
      phone: formData.phone,
      email: formData.email,
      capacity: parseInt(formData.capacity),
      notes: formData.description,
      // Backend: warehouse_type default is 'main'
    }

    try {
      setIsSubmitting(true)
      const result = await warehousesService.create(payload)

      if (!result) {
        throw new Error("فشل إنشاء المستودع")
      }

      toast.success("تم إضافة المستودع بنجاح!")

      // إعادة تعيين النموذج
      setFormData({
        name: "",
        location: "",
        address: "",
        city: "",
        manager: "",
        phone: "",
        email: "",
        capacity: "",
        description: "",
        categories: [], // Note: Categories are not yet part of the Warehouse model in backend explicitly as a list string, storing in metadata if needed? 
        // Current backend implementation doesn't have 'categories' field. 
        // We will ignore for now or add to notes.
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
          إضافة مستودع جديد
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl">
            <Warehouse className="h-5 w-5 text-blue-600" />
            إضافة مستودع جديد
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* معلومات أساسية */}
          <div className="bg-blue-50 p-4 rounded-lg space-y-4">
            <h3 className="font-semibold text-blue-900 flex items-center gap-2">
              <Warehouse className="h-4 w-4" />
              المعلومات الأساسية
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <Label htmlFor="warehouse-name">اسم المستودع *</Label>
                <Input
                  id="warehouse-name"
                  value={formData.name}
                  onChange={(e) => handleChange("name", e.target.value)}
                  placeholder="المستودع الرئيسي"
                  required
                />
              </div>

              <div>
                <Label htmlFor="city">المدينة *</Label>
                <Input
                  id="city"
                  value={formData.city}
                  onChange={(e) => handleChange("city", e.target.value)}
                  placeholder="الرياض"
                  required
                />
              </div>

              <div>
                <Label htmlFor="location">الحي/المنطقة *</Label>
                <Input
                  id="location"
                  value={formData.location}
                  onChange={(e) => handleChange("location", e.target.value)}
                  placeholder="حي الصناعية"
                  required
                />
              </div>

              <div className="col-span-2">
                <Label htmlFor="address">العنوان التفصيلي</Label>
                <Input
                  id="address"
                  value={formData.address}
                  onChange={(e) => handleChange("address", e.target.value)}
                  placeholder="شارع الملك فهد، مبنى رقم 123"
                />
              </div>
            </div>
          </div>

          {/* معلومات المدير */}
          <div className="bg-green-50 p-4 rounded-lg space-y-4">
            <h3 className="font-semibold text-green-900 flex items-center gap-2">
              <Users className="h-4 w-4" />
              معلومات المدير
            </h3>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="manager">اسم المدير *</Label>
                <Input
                  id="manager"
                  value={formData.manager}
                  onChange={(e) => handleChange("manager", e.target.value)}
                  placeholder="أحمد محمد"
                  required
                />
              </div>

              <div>
                <Label htmlFor="phone">رقم الجوال *</Label>
                <Input
                  id="phone"
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => handleChange("phone", e.target.value)}
                  placeholder="05XXXXXXXX"
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
                  placeholder="manager@example.com"
                />
              </div>
            </div>
          </div>

          {/* السعة والتخزين */}
          <div className="bg-purple-50 p-4 rounded-lg space-y-4">
            <h3 className="font-semibold text-purple-900 flex items-center gap-2">
              <Package className="h-4 w-4" />
              السعة والتخزين
            </h3>

            <div>
              <Label htmlFor="capacity">السعة الإجمالية (عدد القطع) *</Label>
              <Input
                id="capacity"
                type="number"
                min="1"
                value={formData.capacity}
                onChange={(e) => handleChange("capacity", e.target.value)}
                placeholder="10000"
                required
              />
              <p className="text-xs text-gray-500 mt-1">أقصى عدد من القطع يمكن تخزينها في المستودع</p>
            </div>

            <div>
              <Label>الفئات المخزنة *</Label>
              <div className="grid grid-cols-2 gap-3 mt-2">
                {availableCategories.map((category) => (
                  <div key={category} className="flex items-center space-x-2 space-x-reverse">
                    <Checkbox
                      id={`category-${category}`}
                      checked={formData.categories.includes(category)}
                      onCheckedChange={() => handleCategoryToggle(category)}
                    />
                    <Label htmlFor={`category-${category}`} className="text-sm font-normal cursor-pointer">
                      {category}
                    </Label>
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-2">اختر فئة واحدة أو أكثر</p>
            </div>
          </div>

          {/* الوصف */}
          <div>
            <Label htmlFor="description">وصف المستودع</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => handleChange("description", e.target.value)}
              placeholder="معلومات إضافية عن المستودع، المرافق، شروط التخزين، إلخ..."
              rows={3}
            />
          </div>

          {/* أزرار الإجراءات */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              إلغاء
            </Button>
            <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={isSubmitting}>
              {isSubmitting ? "جاري الحفظ..." :
                <> <Warehouse className="h-4 w-4 ml-2" /> إضافة المستودع </>
              }
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
