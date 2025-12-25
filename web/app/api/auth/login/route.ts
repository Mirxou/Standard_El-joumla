import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const { email, password } = await request.json()

    // في التطبيق الحقيقي، ستكون هنا عملية المصادقة مع قاعدة البيانات
    // const { data, error } = await supabase.auth.signInWithPassword({
    //   email,
    //   password,
    // })

    // التحقق من البيانات (Demo)
    if (email === "admin@standard.com" && password === "123456") {
      const user = {
        id: 1,
        email,
        name: "أحمد محمد",
        role: "مدير النظام",
        avatar: null,
        token: "demo-token-" + Date.now(),
      }

      return NextResponse.json({
        success: true,
        data: user,
        message: "تم تسجيل الدخول بنجاح",
      })
    }

    return NextResponse.json(
      {
        success: false,
        error: "البريد الإلكتروني أو كلمة المرور غير صحيحة",
      },
      { status: 401 }
    )
  } catch (error) {
    console.error("Login error:", error)
    return NextResponse.json(
      {
        success: false,
        error: "حدث خطأ أثناء تسجيل الدخول",
      },
      { status: 500 }
    )
  }
}
