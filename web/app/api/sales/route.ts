import { NextResponse } from "next/server"

// Mock data للمبيعات
const salesData = [
  {
    id: "INV-2024-001",
    customerName: "أحمد محمد العلي",
    customerPhone: "0501234567",
    date: "2024-01-15",
    time: "14:30",
    items: [
      { name: "زيت الزيتون البكر", quantity: 2, price: 35.99, total: 71.98 },
      { name: "شامبو الأطفال", quantity: 1, price: 22.99, total: 22.99 },
    ],
    subtotal: 94.97,
    tax: 14.25,
    discount: 5.0,
    total: 104.22,
    status: "مدفوعة",
    paymentMethod: "نقدي",
    notes: "عميل مميز - خصم 5%",
  },
]

export async function GET() {
  try {
    return NextResponse.json({
      success: true,
      data: salesData,
      total: salesData.length,
    })
  } catch (error) {
    return NextResponse.json({ success: false, error: "فشل في جلب بيانات المبيعات" }, { status: 500 })
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json()

    // التحقق من صحة البيانات
    if (!body.customerName || !body.items || body.items.length === 0) {
      return NextResponse.json({ success: false, error: "بيانات الفاتورة غير مكتملة" }, { status: 400 })
    }

    // إنشاء فاتورة جديدة
    const newInvoice = {
      id: `INV-2024-${String(salesData.length + 1).padStart(3, "0")}`,
      ...body,
      date: new Date().toISOString().split("T")[0],
      time: new Date().toLocaleTimeString("ar-SA", { hour12: false }),
    }

    salesData.push(newInvoice)

    return NextResponse.json({
      success: true,
      message: "تم إنشاء الفاتورة بنجاح",
      data: newInvoice,
    })
  } catch (error) {
    return NextResponse.json({ success: false, error: "فشل في إنشاء الفاتورة" }, { status: 500 })
  }
}
