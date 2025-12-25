import { NextResponse } from "next/server"

// نموذج بيانات الفواتير
const invoices = [
  {
    id: "INV-2024-001",
    customerName: "محمد أحمد السعيد",
    customerPhone: "0501234567",
    date: "2024-11-17",
    items: [
      { name: "لابتوب HP", quantity: 1, price: 3500, total: 3500 },
      { name: "شامبو بانتين", quantity: 5, price: 45, total: 225 },
    ],
    subtotal: 3725,
    tax: 558.75,
    discount: 100,
    total: 4183.75,
    paymentMethod: "نقدي",
    status: "مكتمل",
    notes: "عميل مميز",
  },
  {
    id: "INV-2024-002",
    customerName: "فاطمة عبدالله",
    customerPhone: "0559876543",
    date: "2024-11-17",
    items: [
      { name: "أرز بسمتي 5كجم", quantity: 10, price: 55, total: 550 },
      { name: "معقم اليدين", quantity: 3, price: 25, total: 75 },
    ],
    subtotal: 625,
    tax: 93.75,
    discount: 0,
    total: 718.75,
    paymentMethod: "بطاقة مدى",
    status: "مكتمل",
    notes: "",
  },
]

// GET: جلب جميع الفواتير
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const status = searchParams.get("status")
    const startDate = searchParams.get("startDate")
    const endDate = searchParams.get("endDate")

    let filteredInvoices = [...invoices]

    if (status && status !== "all") {
      filteredInvoices = filteredInvoices.filter(inv => inv.status === status)
    }

    if (startDate) {
      filteredInvoices = filteredInvoices.filter(inv => inv.date >= startDate)
    }

    if (endDate) {
      filteredInvoices = filteredInvoices.filter(inv => inv.date <= endDate)
    }

    // حساب الإحصائيات
    const stats = {
      totalRevenue: filteredInvoices.reduce((sum, inv) => sum + inv.total, 0),
      totalInvoices: filteredInvoices.length,
      avgInvoiceValue: filteredInvoices.length > 0 
        ? filteredInvoices.reduce((sum, inv) => sum + inv.total, 0) / filteredInvoices.length 
        : 0,
    }

    return NextResponse.json({
      success: true,
      data: filteredInvoices,
      stats,
      total: filteredInvoices.length,
    })
  } catch (error) {
    console.error("Error fetching invoices:", error)
    return NextResponse.json(
      {
        success: false,
        error: "حدث خطأ أثناء جلب الفواتير",
      },
      { status: 500 }
    )
  }
}

// POST: إنشاء فاتورة جديدة
export async function POST(request: Request) {
  try {
    const body = await request.json()

    const newInvoice = {
      id: `INV-2024-${String(invoices.length + 1).padStart(3, '0')}`,
      ...body,
      date: new Date().toISOString().split('T')[0],
      status: "مكتمل",
    }

    invoices.push(newInvoice)

    return NextResponse.json({
      success: true,
      data: newInvoice,
      message: "تم إنشاء الفاتورة بنجاح",
    })
  } catch (error) {
    console.error("Error creating invoice:", error)
    return NextResponse.json(
      {
        success: false,
        error: "حدث خطأ أثناء إنشاء الفاتورة",
      },
      { status: 500 }
    )
  }
}
