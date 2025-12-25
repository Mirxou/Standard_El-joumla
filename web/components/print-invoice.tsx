"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Printer, Download } from 'lucide-react'

interface InvoiceData {
  invoice_number: string
  customer_name: string
  invoice_date: string
  total_amount: number
  items: Array<{
    product_name: string
    quantity: number
    unit_price: number
    line_total: number
  }>
}

interface PrintInvoiceProps {
  invoice: InvoiceData
}

export default function PrintInvoice({ invoice }: PrintInvoiceProps) {
  const handlePrint = () => {
    window.print()
  }

  const handleDownloadPDF = () => {
    // في الإنتاج، استخدم مكتبة مثل jsPDF
    alert('سيتم تنزيل الفاتورة قريباً')
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2 no-print">
        <Button onClick={handlePrint} className="gap-2">
          <Printer className="h-4 w-4" />
          طباعة
        </Button>
        <Button onClick={handleDownloadPDF} variant="outline" className="gap-2">
          <Download className="h-4 w-4" />
          تنزيل PDF
        </Button>
      </div>

      <Card className="print-only">
        <CardContent className="p-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold">Standard | شعارنا للأبد</h1>
            <p className="text-gray-600">نظام إدارة المخزون المتكامل</p>
          </div>

          <div className="grid grid-cols-2 gap-8 mb-8">
            <div>
              <h2 className="font-bold mb-2">معلومات الفاتورة</h2>
              <p>رقم الفاتورة: {invoice.invoice_number}</p>
              <p>التاريخ: {new Date(invoice.invoice_date).toLocaleDateString('ar-SA')}</p>
            </div>
            <div>
              <h2 className="font-bold mb-2">معلومات العميل</h2>
              <p>الاسم: {invoice.customer_name}</p>
            </div>
          </div>

          <table className="w-full mb-8">
            <thead>
              <tr className="border-b-2">
                <th className="text-right p-2">المنتج</th>
                <th className="text-right p-2">الكمية</th>
                <th className="text-right p-2">السعر</th>
                <th className="text-right p-2">المجموع</th>
              </tr>
            </thead>
            <tbody>
              {invoice.items.map((item, index) => (
                <tr key={index} className="border-b">
                  <td className="p-2">{item.product_name}</td>
                  <td className="p-2">{item.quantity}</td>
                  <td className="p-2">{item.unit_price.toFixed(2)} ر.س</td>
                  <td className="p-2">{item.line_total.toFixed(2)} ر.س</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="text-left">
            <p className="text-2xl font-bold">
              الإجمالي: {invoice.total_amount.toFixed(2)} ر.س
            </p>
          </div>

          <div className="mt-8 text-center text-sm text-gray-600">
            <p>شكراً لتعاملكم معنا</p>
            <p>للاستفسار: info@standard.com | 0500000000</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
