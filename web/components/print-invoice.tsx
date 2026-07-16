"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Printer, Download, X } from 'lucide-react'
import { generateInvoicePDF } from "@/lib/utils/pdf-generator"
import type { Invoice } from "@/lib/invoice-storage"

interface PrintInvoiceProps {
  invoice: Invoice | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export default function PrintInvoice({ invoice, open, onOpenChange }: PrintInvoiceProps) {
  if (!invoice) return null

  const handlePrint = () => {
    window.print()
  }

  const handleDownloadPDF = () => {
    try {
      generateInvoicePDF({
        id: invoice.id,
        invoiceNumber: invoice.invoiceNumber,
        customerName: invoice.customerName,
        customerPhone: invoice.customerPhone,
        date: invoice.date,
        time: invoice.time,
        items: invoice.items.map(item => ({
          name: item.productName,
          quantity: item.quantity,
          price: item.price,
          total: item.total,
        })),
        subtotal: invoice.subtotal,
        tax: invoice.tax,
        discount: invoice.discount,
        total: invoice.total,
        paymentMethod: invoice.paymentMethod,
        notes: invoice.notes,
      })
    } catch (error) {
      console.error("Error generating PDF:", error)
      alert("حدث خطأ أثناء إنشاء ملف PDF")
    }
  }

  return (
    <>
      <style jsx global>{`
        @media print {
          .no-print {
            display: none !important;
          }
          .print-only {
            display: block !important;
          }
          body {
            margin: 0;
            padding: 0;
          }
          .print-container {
            padding: 20px;
            background: white;
          }
        }
        @media screen {
          .print-only {
            display: none;
          }
        }
      `}</style>
      
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto print-container">
          <DialogHeader className="no-print">
            <div className="flex items-center justify-between">
              <DialogTitle className="text-xl font-bold">طباعة الفاتورة</DialogTitle>
              <div className="flex gap-2">
                <Button onClick={handlePrint} className="gap-2">
                  <Printer className="h-4 w-4" />
                  طباعة
                </Button>
                <Button onClick={handleDownloadPDF} variant="outline" className="gap-2">
                  <Download className="h-4 w-4" />
                  تنزيل PDF
                </Button>
                <Button onClick={() => onOpenChange(false)} variant="ghost" size="sm">
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </DialogHeader>

          <div className="print-only">
            <Card>
              <CardContent className="p-8">
                <div className="text-center mb-8">
                  <h1 className="text-3xl font-bold">Standard | شعارنا للأبد</h1>
                  <p className="text-gray-600">نظام إدارة المخزون المتكامل</p>
                </div>

                <div className="grid grid-cols-2 gap-8 mb-8">
                  <div>
                    <h2 className="font-bold mb-2">معلومات الفاتورة</h2>
                    <p>رقم الفاتورة: {invoice.invoiceNumber}</p>
                    <p>التاريخ: {new Date(invoice.date).toLocaleDateString('ar-SA')}</p>
                    <p>الوقت: {invoice.time}</p>
                  </div>
                  <div>
                    <h2 className="font-bold mb-2">معلومات العميل</h2>
                    <p>الاسم: {invoice.customerName}</p>
                    {invoice.customerPhone && <p>الجوال: {invoice.customerPhone}</p>}
                  </div>
                </div>

                <table className="w-full mb-8 border-collapse">
                  <thead>
                    <tr className="border-b-2 border-gray-300">
                      <th className="text-right p-3 bg-gray-100">#</th>
                      <th className="text-right p-3 bg-gray-100">اسم المنتج</th>
                      <th className="text-right p-3 bg-gray-100">الكمية</th>
                      <th className="text-right p-3 bg-gray-100">السعر</th>
                      <th className="text-right p-3 bg-gray-100">المجموع</th>
                    </tr>
                  </thead>
                  <tbody>
                    {invoice.items.map((item, index) => (
                      <tr key={index} className="border-b border-gray-200">
                        <td className="p-3 text-center">{index + 1}</td>
                        <td className="p-3">{item.productName}</td>
                        <td className="p-3 text-center">{item.quantity}</td>
                        <td className="p-3 text-left">{item.price.toFixed(2)} ر.س</td>
                        <td className="p-3 text-left">{item.total.toFixed(2)} ر.س</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <div className="flex justify-end mb-4">
                  <div className="w-64 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>المجموع الفرعي:</span>
                      <span className="font-semibold">{invoice.subtotal.toFixed(2)} ر.س</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>ضريبة القيمة المضافة (15%):</span>
                      <span className="font-semibold">{invoice.tax.toFixed(2)} ر.س</span>
                    </div>
                    {invoice.discount > 0 && (
                      <div className="flex justify-between text-sm text-green-600">
                        <span>الخصم:</span>
                        <span className="font-semibold">-{invoice.discount.toFixed(2)} ر.س</span>
                      </div>
                    )}
                    <div className="flex justify-between text-lg font-bold border-t pt-2 mt-2">
                      <span>الإجمالي:</span>
                      <span className="text-green-600">{invoice.total.toFixed(2)} ر.س</span>
                    </div>
                  </div>
                </div>

                <div className="mb-4">
                  <p className="text-sm text-gray-600">
                    <strong>طريقة الدفع:</strong> {invoice.paymentMethod}
                  </p>
                  <p className="text-sm text-gray-600">
                    <strong>الحالة:</strong> {invoice.status}
                  </p>
                </div>

                {invoice.notes && (
                  <div className="bg-blue-50 rounded-lg p-4 mb-4">
                    <p className="text-sm text-blue-800">
                      <strong>ملاحظات:</strong> {invoice.notes}
                    </p>
                  </div>
                )}

                <div className="mt-8 text-center text-sm text-gray-600 border-t pt-4">
                  <p>شكراً لتعاملكم معنا</p>
                  <p>للاستفسارات: info@standard.com | 0500000000</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
