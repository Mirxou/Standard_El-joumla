import { NextResponse } from "next/server"

// Mock data - في التطبيق الحقيقي، ستكون هذه البيانات من قاعدة البيانات
const inventoryData = [
  {
    id: 1,
    name: "زيت الزيتون البكر الممتاز",
    category: "مواد غذائية",
    sku: "FOOD-001",
    barcode: "1234567890123",
    stock: 45,
    minStock: 20,
    maxStock: 100,
    buyPrice: 25.5,
    sellPrice: 35.99,
    warehouse: "المستودع الرئيسي",
    supplier: "شركة الزيوت المتميزة",
    expiryDate: "2024-12-31",
    status: "متوفر",
    lastUpdated: new Date().toISOString(),
  },
]

export async function GET() {
  try {
    return NextResponse.json({
      success: true,
      data: inventoryData,
      total: inventoryData.length,
    })
  } catch (error) {
    return NextResponse.json({ success: false, error: "فشل في جلب بيانات المخزون" }, { status: 500 })
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json()

    // التحقق من صحة البيانات
    if (!body.name || !body.sku || !body.buyPrice || !body.sellPrice) {
      return NextResponse.json({ success: false, error: "بيانات مطلوبة مفقودة" }, { status: 400 })
    }

    // إضافة المنتج الجديد
    const newProduct = {
      id: inventoryData.length + 1,
      ...body,
      lastUpdated: new Date().toISOString(),
    }

    inventoryData.push(newProduct)

    return NextResponse.json({
      success: true,
      message: "تم إضافة المنتج بنجاح",
      data: newProduct,
    })
  } catch (error) {
    return NextResponse.json({ success: false, error: "فشل في إضافة المنتج" }, { status: 500 })
  }
}
