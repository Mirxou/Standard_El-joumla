"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Plus, Trash2, FileText, ShoppingCart, Calculator } from "lucide-react"
import { toast } from "sonner"
import { saveInvoice, updateInvoice, type Invoice, type InvoiceItem } from "@/lib/invoice-storage"

interface CreateInvoiceProps {
  invoice?: Invoice | null
  onSaved?: () => void
}

export default function CreateInvoice({ invoice, onSaved }: CreateInvoiceProps) {
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const isEditMode = !!invoice

  // فتح الـ Dialog تلقائياً عند التعديل
  useEffect(() => {
    if (invoice) {
      setOpen(true)
    }
  }, [invoice])

  const handleDialogChange = (isOpen: boolean) => {
    setOpen(isOpen)
    // إذا تم إغلاق الـ Dialog في وضع التعديل، نلغي التعديل
    if (!isOpen && isEditMode && onSaved) {
      onSaved()
    }
  }
  const [customerName, setCustomerName] = useState("")
  const [customerPhone, setCustomerPhone] = useState("")
  const [paymentMethod, setPaymentMethod] = useState("نقدي")
  const [notes, setNotes] = useState("")
  const [discount, setDiscount] = useState(0)
  const [status, setStatus] = useState<"مدفوعة" | "معلقة" | "ملغية" | "paid" | "pending" | "cancelled">("مدفوعة")
  const [items, setItems] = useState<InvoiceItem[]>([
    { id: "1", productName: "", quantity: 1, price: 0, total: 0 }
  ])

  // تحديث البيانات عند التعديل
  useEffect(() => {
    if (invoice) {
      setCustomerName(invoice.customerName)
      setCustomerPhone(invoice.customerPhone)
      setPaymentMethod(invoice.paymentMethod)
      setNotes(invoice.notes)
      setDiscount(invoice.discount)
      setStatus(invoice.status)
      setItems(invoice.items)
    }
  }, [invoice])

  const addItem = () => {
    const newItem: InvoiceItem = {
      id: Date.now().toString(),
      productName: "",
      quantity: 1,
      price: 0,
      total: 0,
    }
    setItems([...items, newItem])
  }

  const removeItem = (id: string) => {
    if (items.length > 1) {
      setItems(items.filter((item) => item.id !== id))
    }
  }

  const updateItem = (id: string, field: keyof InvoiceItem, value: string | number) => {
    setItems(
      items.map((item) => {
        if (item.id === id) {
          const updated = { ...item, [field]: value }
          if (field === "quantity" || field === "price") {
            updated.total = updated.quantity * updated.price
          }
          return updated
        }
        return item
      }),
    )
  }

  const calculateSubtotal = () => {
    return items.reduce((sum, item) => sum + item.total, 0)
  }

  const calculateTax = () => {
    return calculateSubtotal() * 0.15 // 15% VAT
  }

  const calculateTotal = () => {
    return calculateSubtotal() + calculateTax() - discount
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!customerName.trim()) {
      toast.error("الرجاء إدخال اسم العميل")
      return
    }

    if (items.some((item) => !item.productName.trim() || item.quantity <= 0 || item.price <= 0)) {
      toast.error("الرجاء التأكد من إدخال جميع بيانات المنتجات بشكل صحيح")
      return
    }

    setSaving(true)
    try {
      const invoiceData = {
        customerName,
        customerPhone,
        paymentMethod,
        notes,
        status,
        date: new Date().toISOString().split("T")[0],
        time: new Date().toLocaleTimeString("ar-SA", { hour: "2-digit", minute: "2-digit" }),
        items,
        subtotal: calculateSubtotal(),
        tax: calculateTax(),
        discount,
        total: calculateTotal(),
      }

      let result;
      if (isEditMode && invoice) {
        // تحديث فاتورة موجودة
        result = await updateInvoice(invoice.id, invoiceData)
        if (result) toast.success("تم تحديث الفاتورة بنجاح!")
      } else {
        // إنشاء فاتورة جديدة
        result = await saveInvoice(invoiceData)
        if (result) toast.success("تم إنشاء الفاتورة بنجاح!")
      }

      if (result) {
        // إعادة تعيين النموذج
        resetForm()
        setOpen(false)

        // إعلام المكون الأب بالتحديث
        if (onSaved) {
          onSaved()
        }
      } else {
        toast.error("فشل حفظ الفاتورة")
      }
    } catch (error) {
      console.error("Error saving invoice:", error)
      toast.error("حدث خطأ أثناء حفظ الفاتورة")
    } finally {
      setSaving(false)
    }
  }

  const resetForm = () => {
    if (!isEditMode) {
      setCustomerName("")
      setCustomerPhone("")
      setPaymentMethod("نقدي")
      setNotes("")
      setDiscount(0)
      setStatus("مدفوعة")
      setItems([{ id: "1", productName: "", quantity: 1, price: 0, total: 0 }])
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleDialogChange}>
      {!isEditMode && (
        <DialogTrigger asChild>
          <Button className="bg-green-600 hover:bg-green-700">
            <Plus className="h-4 w-4 ml-2" />
            فاتورة جديدة
          </Button>
        </DialogTrigger>
      )}
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl">
            <FileText className="h-5 w-5 text-green-600" />
            {isEditMode ? "تعديل الفاتورة" : "إنشاء فاتورة جديدة"}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* معلومات العميل */}
          <div className="bg-blue-50 p-4 rounded-lg space-y-4">
            <h3 className="font-semibold text-blue-900 flex items-center gap-2">
              <ShoppingCart className="h-4 w-4" />
              معلومات العميل
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="customer-name">اسم العميل *</Label>
                <Input
                  id="customer-name"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  placeholder="أدخل اسم العميل"
                  required
                />
              </div>
              <div>
                <Label htmlFor="customer-phone">رقم الجوال</Label>
                <Input
                  id="customer-phone"
                  value={customerPhone}
                  onChange={(e) => setCustomerPhone(e.target.value)}
                  placeholder="05XXXXXXXX"
                  type="tel"
                />
              </div>
            </div>
          </div>

          {/* المنتجات */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">المنتجات</h3>
              <Button type="button" onClick={addItem} variant="outline" size="sm">
                <Plus className="h-4 w-4 ml-1" />
                إضافة منتج
              </Button>
            </div>

            <div className="space-y-3">
              {items.map((item, index) => (
                <div key={item.id} className="grid grid-cols-12 gap-3 items-end p-3 bg-gray-50 rounded-lg">
                  <div className="col-span-1 text-center">
                    <Label className="text-xs">#</Label>
                    <p className="text-sm font-semibold mt-2">{index + 1}</p>
                  </div>

                  <div className="col-span-5">
                    <Label htmlFor={`product-${item.id}`}>اسم المنتج *</Label>
                    <Input
                      id={`product-${item.id}`}
                      value={item.productName}
                      onChange={(e) => updateItem(item.id, "productName", e.target.value)}
                      placeholder="اسم المنتج"
                      required
                    />
                  </div>

                  <div className="col-span-2">
                    <Label htmlFor={`quantity-${item.id}`}>الكمية *</Label>
                    <Input
                      id={`quantity-${item.id}`}
                      type="number"
                      min="1"
                      value={item.quantity}
                      onChange={(e) => updateItem(item.id, "quantity", parseInt(e.target.value) || 0)}
                      required
                    />
                  </div>

                  <div className="col-span-2">
                    <Label htmlFor={`price-${item.id}`}>السعر *</Label>
                    <Input
                      id={`price-${item.id}`}
                      type="number"
                      step="0.01"
                      min="0"
                      value={item.price}
                      onChange={(e) => updateItem(item.id, "price", parseFloat(e.target.value) || 0)}
                      required
                    />
                  </div>

                  <div className="col-span-2">
                    <Label>المجموع</Label>
                    <div className="h-10 flex items-center justify-center bg-green-100 rounded-md font-semibold text-green-700">
                      {item.total.toFixed(2)}
                    </div>
                  </div>

                  {items.length > 1 && (
                    <div className="col-span-12 md:col-span-auto flex items-end">
                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        onClick={() => removeItem(item.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* الحسابات */}
          <div className="bg-gray-50 p-4 rounded-lg space-y-3">
            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
              <Calculator className="h-4 w-4" />
              ملخص الفاتورة
            </h3>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>المجموع الفرعي:</span>
                <span className="font-semibold">{calculateSubtotal().toFixed(2)} ر.س</span>
              </div>

              <div className="flex justify-between text-sm">
                <span>ضريبة القيمة المضافة (15%):</span>
                <span className="font-semibold">{calculateTax().toFixed(2)} ر.س</span>
              </div>

              <div className="flex justify-between items-center text-sm">
                <span>الخصم:</span>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    max={calculateSubtotal()}
                    value={discount}
                    onChange={(e) => setDiscount(parseFloat(e.target.value) || 0)}
                    className="w-32 h-8"
                  />
                  <span>ر.س</span>
                </div>
              </div>

              <div className="border-t pt-2 mt-2">
                <div className="flex justify-between text-lg font-bold text-green-600">
                  <span>الإجمالي النهائي:</span>
                  <span>{calculateTotal().toFixed(2)} ر.س</span>
                </div>
              </div>
            </div>
          </div>

          {/* طريقة الدفع والملاحظات */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="payment-method">طريقة الدفع</Label>
              <Select value={paymentMethod} onValueChange={setPaymentMethod}>
                <SelectTrigger id="payment-method">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="نقدي">نقدي</SelectItem>
                  <SelectItem value="بطاقة ائتمان">بطاقة ائتمان</SelectItem>
                  <SelectItem value="بطاقة مدى">بطاقة مدى</SelectItem>
                  <SelectItem value="تحويل بنكي">تحويل بنكي</SelectItem>
                  <SelectItem value="آجل">آجل</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="status">حالة الفاتورة</Label>
              <Select value={status} onValueChange={(val) => setStatus(val as any)}>
                <SelectTrigger id="status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="مدفوعة">مدفوعة</SelectItem>
                  <SelectItem value="معلقة">معلقة</SelectItem>
                  <SelectItem value="ملغية">ملغية</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label htmlFor="notes">ملاحظات</Label>
            <Textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="ملاحظات إضافية (اختياري)"
              rows={2}
            />
          </div>

          {/* أزرار الإجراءات */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button type="button" variant="outline" onClick={() => setOpen(false)} disabled={saving}>
              إلغاء
            </Button>
            <Button type="submit" className="bg-green-600 hover:bg-green-700" disabled={saving}>
              <ShoppingCart className={`h-4 w-4 ml-2 ${saving ? 'animate-spin' : ''}`} />
              {isEditMode ? "حفظ التعديلات" : "إنشاء وحفظ الفاتورة"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
