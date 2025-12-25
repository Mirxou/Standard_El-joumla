import { jsPDF } from 'jspdf'
import 'jspdf-autotable'

interface InvoiceData {
  id: string
  customerName: string
  customerPhone: string
  date: string
  time: string
  items: Array<{
    name: string
    quantity: number
    price: number
    total: number
  }>
  subtotal: number
  tax: number
  discount: number
  total: number
  paymentMethod: string
  notes?: string
}

export const generateInvoicePDF = (invoice: InvoiceData) => {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  })

  // إعدادات الخط العربي
  doc.setLanguage('ar')
  doc.setR2L(true)

  // الهيدر - اسم الشركة
  doc.setFillColor(37, 99, 235) // أزرق
  doc.rect(0, 0, 210, 40, 'F')
  
  doc.setTextColor(255, 255, 255)
  doc.setFontSize(24)
  doc.text('Standard', 105, 15, { align: 'center' })
  
  doc.setFontSize(12)
  doc.text('نظام إدارة المخزون المتكامل', 105, 25, { align: 'center' })
  doc.text('شعارنا للأبد', 105, 32, { align: 'center' })

  // معلومات الفاتورة
  doc.setTextColor(0, 0, 0)
  doc.setFontSize(16)
  doc.text('فاتورة ضريبية', 105, 50, { align: 'center' })

  doc.setFontSize(10)
  doc.text(`رقم الفاتورة: ${invoice.id}`, 20, 60)
  doc.text(`التاريخ: ${invoice.date}`, 20, 67)
  doc.text(`الوقت: ${invoice.time}`, 20, 74)

  // معلومات العميل
  doc.setFillColor(243, 244, 246)
  doc.rect(20, 80, 170, 25, 'F')
  
  doc.setFontSize(11)
  doc.setFont('helvetica', 'bold')
  doc.text('معلومات العميل:', 25, 87)
  
  doc.setFont('helvetica', 'normal')
  doc.text(`الاسم: ${invoice.customerName}`, 25, 94)
  if (invoice.customerPhone) {
    doc.text(`الجوال: ${invoice.customerPhone}`, 25, 101)
  }

  // جدول المنتجات
  const tableData = invoice.items.map((item, index) => [
    item.total.toFixed(2),
    item.price.toFixed(2),
    item.quantity.toString(),
    item.name,
    (index + 1).toString(),
  ])

  ;(doc as any).autoTable({
    startY: 115,
    head: [['المجموع (ر.س)', 'السعر (ر.س)', 'الكمية', 'اسم المنتج', '#']],
    body: tableData,
    theme: 'grid',
    styles: {
      font: 'helvetica',
      fontSize: 10,
      cellPadding: 5,
      halign: 'center',
    },
    headStyles: {
      fillColor: [59, 130, 246],
      textColor: 255,
      fontStyle: 'bold',
    },
    alternateRowStyles: {
      fillColor: [249, 250, 251],
    },
  })

  // الحسابات النهائية
  const finalY = (doc as any).lastAutoTable.finalY + 10

  doc.setFillColor(249, 250, 251)
  doc.rect(120, finalY, 70, 35, 'F')

  doc.setFontSize(10)
  doc.text('المجموع الفرعي:', 185, finalY + 7, { align: 'right' })
  doc.text(`${invoice.subtotal.toFixed(2)} ر.س`, 125, finalY + 7)

  doc.text('ضريبة القيمة المضافة (15%):', 185, finalY + 14, { align: 'right' })
  doc.text(`${invoice.tax.toFixed(2)} ر.س`, 125, finalY + 14)

  if (invoice.discount > 0) {
    doc.setTextColor(22, 163, 74)
    doc.text('الخصم:', 185, finalY + 21, { align: 'right' })
    doc.text(`-${invoice.discount.toFixed(2)} ر.س`, 125, finalY + 21)
    doc.setTextColor(0, 0, 0)
  }

  // المجموع النهائي
  doc.setFillColor(37, 99, 235)
  doc.rect(120, finalY + 25, 70, 10, 'F')
  doc.setTextColor(255, 255, 255)
  doc.setFontSize(12)
  doc.setFont('helvetica', 'bold')
  doc.text('الإجمالي:', 185, finalY + 32, { align: 'right' })
  doc.text(`${invoice.total.toFixed(2)} ر.س`, 125, finalY + 32)

  // طريقة الدفع
  doc.setTextColor(0, 0, 0)
  doc.setFontSize(10)
  doc.setFont('helvetica', 'normal')
  doc.text(`طريقة الدفع: ${invoice.paymentMethod}`, 20, finalY + 32)

  // الملاحظات
  if (invoice.notes) {
    doc.setFillColor(239, 246, 255)
    doc.rect(20, finalY + 40, 170, 15, 'F')
    doc.setFontSize(9)
    doc.text('ملاحظات:', 25, finalY + 47)
    doc.text(invoice.notes, 25, finalY + 53)
  }

  // الفوتر
  doc.setFillColor(243, 244, 246)
  doc.rect(0, 270, 210, 27, 'F')
  
  doc.setFontSize(9)
  doc.setTextColor(75, 85, 99)
  doc.text('شكراً لتعاملكم معنا', 105, 280, { align: 'center' })
  doc.text('للاستفسارات: info@standard.com | 0500000000', 105, 287, { align: 'center' })

  // حفظ PDF
  doc.save(`Invoice_${invoice.id}.pdf`)
}

// دالة لطباعة الفاتورة مباشرة
export const printInvoice = (invoice: InvoiceData) => {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  })

  // إعدادات الخط العربي
  doc.setLanguage('ar')
  doc.setR2L(true)

  // الهيدر - اسم الشركة
  doc.setFillColor(37, 99, 235)
  doc.rect(0, 0, 210, 40, 'F')
  
  doc.setTextColor(255, 255, 255)
  doc.setFontSize(24)
  doc.text('Standard', 105, 15, { align: 'center' })
  
  doc.setFontSize(12)
  doc.text('نظام إدارة المخزون المتكامل', 105, 25, { align: 'center' })
  doc.text('شعارنا للأبد', 105, 32, { align: 'center' })

  // معلومات الفاتورة
  doc.setTextColor(0, 0, 0)
  doc.setFontSize(16)
  doc.text('فاتورة ضريبية', 105, 50, { align: 'center' })

  doc.setFontSize(10)
  doc.text(`رقم الفاتورة: ${invoice.id}`, 20, 60)
  doc.text(`التاريخ: ${invoice.date}`, 20, 67)
  doc.text(`الوقت: ${invoice.time}`, 20, 74)

  // معلومات العميل
  doc.setFillColor(243, 244, 246)
  doc.rect(20, 80, 170, 25, 'F')
  
  doc.setFontSize(11)
  doc.setFont('helvetica', 'bold')
  doc.text('معلومات العميل:', 25, 87)
  
  doc.setFont('helvetica', 'normal')
  doc.text(`الاسم: ${invoice.customerName}`, 25, 94)
  if (invoice.customerPhone) {
    doc.text(`الجوال: ${invoice.customerPhone}`, 25, 101)
  }

  // جدول المنتجات
  const tableData = invoice.items.map((item, index) => [
    item.total.toFixed(2),
    item.price.toFixed(2),
    item.quantity.toString(),
    item.name,
    (index + 1).toString(),
  ])

  ;(doc as any).autoTable({
    startY: 115,
    head: [['المجموع (ر.س)', 'السعر (ر.س)', 'الكمية', 'اسم المنتج', '#']],
    body: tableData,
    theme: 'grid',
    styles: {
      font: 'helvetica',
      fontSize: 10,
      cellPadding: 5,
      halign: 'center',
    },
    headStyles: {
      fillColor: [59, 130, 246],
      textColor: 255,
      fontStyle: 'bold',
    },
    alternateRowStyles: {
      fillColor: [249, 250, 251],
    },
  })

  // الحسابات النهائية
  const finalY = (doc as any).lastAutoTable.finalY + 10

  doc.setFillColor(249, 250, 251)
  doc.rect(120, finalY, 70, 35, 'F')

  doc.setFontSize(10)
  doc.text('المجموع الفرعي:', 185, finalY + 7, { align: 'right' })
  doc.text(`${invoice.subtotal.toFixed(2)} ر.س`, 125, finalY + 7)

  doc.text('ضريبة القيمة المضافة (15%):', 185, finalY + 14, { align: 'right' })
  doc.text(`${invoice.tax.toFixed(2)} ر.س`, 125, finalY + 14)

  if (invoice.discount > 0) {
    doc.setTextColor(22, 163, 74)
    doc.text('الخصم:', 185, finalY + 21, { align: 'right' })
    doc.text(`-${invoice.discount.toFixed(2)} ر.س`, 125, finalY + 21)
    doc.setTextColor(0, 0, 0)
  }

  // المجموع النهائي
  doc.setFillColor(37, 99, 235)
  doc.rect(120, finalY + 25, 70, 10, 'F')
  doc.setTextColor(255, 255, 255)
  doc.setFontSize(12)
  doc.setFont('helvetica', 'bold')
  doc.text('الإجمالي:', 185, finalY + 32, { align: 'right' })
  doc.text(`${invoice.total.toFixed(2)} ر.س`, 125, finalY + 32)

  // طريقة الدفع
  doc.setTextColor(0, 0, 0)
  doc.setFontSize(10)
  doc.setFont('helvetica', 'normal')
  doc.text(`طريقة الدفع: ${invoice.paymentMethod}`, 20, finalY + 32)

  // الملاحظات
  if (invoice.notes) {
    doc.setFillColor(239, 246, 255)
    doc.rect(20, finalY + 40, 170, 15, 'F')
    doc.setFontSize(9)
    doc.text('ملاحظات:', 25, finalY + 47)
    doc.text(invoice.notes, 25, finalY + 53)
  }

  // الفوتر
  doc.setFillColor(243, 244, 246)
  doc.rect(0, 270, 210, 27, 'F')
  
  doc.setFontSize(9)
  doc.setTextColor(75, 85, 99)
  doc.text('شكراً لتعاملكم معنا', 105, 280, { align: 'center' })
  doc.text('للاستفسارات: info@standard.com | 0500000000', 105, 287, { align: 'center' })

  // طباعة مباشرة
  doc.autoPrint()
  window.open(doc.output('bloburl'), '_blank')
}
