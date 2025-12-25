import { NextResponse } from "next/server"

// نموذج بيانات المستخدمين
const users = [
  {
    id: 1,
    name: "أحمد محمد العلي",
    email: "ahmed@standard.com",
    phone: "0501234567",
    role: "admin",
    roleAr: "مدير النظام",
    status: "active",
    statusAr: "نشط",
    permissions: ["all"],
    createdAt: "2024-01-15",
    lastLogin: new Date().toISOString(),
  },
  {
    id: 2,
    name: "فاطمة سالم الحربي",
    email: "fatima@standard.com",
    phone: "0507654321",
    role: "accountant",
    roleAr: "محاسب",
    status: "active",
    statusAr: "نشط",
    permissions: ["sales", "reports"],
    createdAt: "2024-02-20",
    lastLogin: "2024-11-17T10:30:00",
  },
]

// GET: جلب جميع المستخدمين
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const role = searchParams.get("role")
    const status = searchParams.get("status")

    let filteredUsers = [...users]

    if (role && role !== "all") {
      filteredUsers = filteredUsers.filter(u => u.role === role)
    }

    if (status && status !== "all") {
      filteredUsers = filteredUsers.filter(u => u.status === status)
    }

    return NextResponse.json({
      success: true,
      data: filteredUsers,
      total: filteredUsers.length,
    })
  } catch (error) {
    console.error("Error fetching users:", error)
    return NextResponse.json(
      {
        success: false,
        error: "حدث خطأ أثناء جلب المستخدمين",
      },
      { status: 500 }
    )
  }
}

// POST: إضافة مستخدم جديد
export async function POST(request: Request) {
  try {
    const body = await request.json()

    const newUser = {
      id: users.length + 1,
      ...body,
      status: "active",
      statusAr: "نشط",
      createdAt: new Date().toISOString().split('T')[0],
      lastLogin: null,
    }

    users.push(newUser)

    return NextResponse.json({
      success: true,
      data: newUser,
      message: "تم إضافة المستخدم بنجاح",
    })
  } catch (error) {
    console.error("Error creating user:", error)
    return NextResponse.json(
      {
        success: false,
        error: "حدث خطأ أثناء إضافة المستخدم",
      },
      { status: 500 }
    )
  }
}
