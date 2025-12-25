import { NextResponse } from "next/server"

// نموذج بيانات المنتجات
const products = [
  {
    id: 1,
    name: "لابتوب HP ProBook",
    sku: "ELC-001",
    category: "إلكترونيات",
    quantity: 25,
    price: 3500,
    cost: 2800,
    supplier: "Tech Solutions",
    warehouse: "المستودع الرئيسي",
    status: "متوفر",
    image: null,
    barcode: "7891234567890",
    expiryDate: null,
  },
  {
    id: 2,
    name: "شامبو بانتين 400مل",
    sku: "BEA-002",
    category: "جمال",
    quantity: 150,
    price: 45,
    cost: 32,
    supplier: "Beauty Supplies Co",
    warehouse: "المستودع الفرعي",
    status: "متوفر",
    image: null,
    barcode: "6281234567891",
    expiryDate: "2025-12-31",
  },
  {
    id: 3,
    name: "معقم اليدين 500مل",
    sku: "HYG-003",
    category: "نظافة",
    quantity: 8,
    price: 25,
    cost: 18,
    supplier: "Hygiene Products Ltd",
    warehouse: "المستودع الرئيسي",
    status: "منخفض",
    image: null,
    barcode: "6281234567892",
    expiryDate: "2026-06-30",
  },
  {
    id: 4,
    name: "أرز بسمتي 5كجم",
    sku: "FOD-004",
    category: "مواد غذائية",
    quantity: 200,
    price: 55,
    cost: 42,
    supplier: "Food Distributors Inc",
    warehouse: "مستودع المواد الغذائية",
    status: "متوفر",
    image: null,
    barcode: "6281234567893",
    expiryDate: "2025-08-15",
  },
  {
    id: 5,
    name: "فيتامينات متعددة",
    sku: "HEA-005",
    category: "صحة",
    quantity: 3,
    price: 85,
    cost: 65,
    supplier: "Health Care Suppliers",
    warehouse: "المستودع الرئيسي",
    status: "حرج",
    image: null,
    barcode: "6281234567894",
    expiryDate: "2025-03-20",
  },
]

// GET: جلب جميع المنتجات
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const category = searchParams.get("category")
    const status = searchParams.get("status")
    const search = searchParams.get("search")

    let filteredProducts = [...products]

    // تصفية حسب الفئة
    if (category && category !== "all") {
      filteredProducts = filteredProducts.filter(p => p.category === category)
    }

    // تصفية حسب الحالة
    if (status && status !== "all") {
      filteredProducts = filteredProducts.filter(p => p.status === status)
    }

    // البحث
    if (search) {
      const searchLower = search.toLowerCase()
      filteredProducts = filteredProducts.filter(
        p =>
          p.name.toLowerCase().includes(searchLower) ||
          p.sku.toLowerCase().includes(searchLower) ||
          p.barcode.includes(searchLower)
      )
    }

    return NextResponse.json({
      success: true,
      data: filteredProducts,
      total: filteredProducts.length,
    })
  } catch (error) {
    console.error("Error fetching products:", error)
    return NextResponse.json(
      {
        success: false,
        error: "حدث خطأ أثناء جلب المنتجات",
      },
      { status: 500 }
    )
  }
}

// POST: إضافة منتج جديد
export async function POST(request: Request) {
  try {
    const body = await request.json()

    const newProduct = {
      id: products.length + 1,
      ...body,
      status: body.quantity > 20 ? "متوفر" : body.quantity > 5 ? "منخفض" : "حرج",
    }

    products.push(newProduct)

    return NextResponse.json({
      success: true,
      data: newProduct,
      message: "تم إضافة المنتج بنجاح",
    })
  } catch (error) {
    console.error("Error creating product:", error)
    return NextResponse.json(
      {
        success: false,
        error: "حدث خطأ أثناء إضافة المنتج",
      },
      { status: 500 }
    )
  }
}

// PUT: تحديث منتج
export async function PUT(request: Request) {
  try {
    const body = await request.json()
    const { id, ...updates } = body

    const index = products.findIndex(p => p.id === id)
    if (index === -1) {
      return NextResponse.json(
        {
          success: false,
          error: "المنتج غير موجود",
        },
        { status: 404 }
      )
    }

    products[index] = {
      ...products[index],
      ...updates,
      status: updates.quantity > 20 ? "متوفر" : updates.quantity > 5 ? "منخفض" : "حرج",
    }

    return NextResponse.json({
      success: true,
      data: products[index],
      message: "تم تحديث المنتج بنجاح",
    })
  } catch (error) {
    console.error("Error updating product:", error)
    return NextResponse.json(
      {
        success: false,
        error: "حدث خطأ أثناء تحديث المنتج",
      },
      { status: 500 }
    )
  }
}

// DELETE: حذف منتج
export async function DELETE(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const id = searchParams.get("id")

    if (!id) {
      return NextResponse.json(
        {
          success: false,
          error: "معرف المنتج مطلوب",
        },
        { status: 400 }
      )
    }

    const index = products.findIndex(p => p.id === parseInt(id))
    if (index === -1) {
      return NextResponse.json(
        {
          success: false,
          error: "المنتج غير موجود",
        },
        { status: 404 }
      )
    }

    products.splice(index, 1)

    return NextResponse.json({
      success: true,
      message: "تم حذف المنتج بنجاح",
    })
  } catch (error) {
    console.error("Error deleting product:", error)
    return NextResponse.json(
      {
        success: false,
        error: "حدث خطأ أثناء حذف المنتج",
      },
      { status: 500 }
    )
  }
}
