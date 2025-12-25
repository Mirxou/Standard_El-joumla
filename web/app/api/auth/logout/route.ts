import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    // في التطبيق الحقيقي، ستكون هنا عملية تسجيل الخروج
    // await supabase.auth.signOut()

    return NextResponse.json({
      success: true,
      message: "تم تسجيل الخروج بنجاح",
    })
  } catch (error) {
    console.error("Logout error:", error)
    return NextResponse.json(
      {
        success: false,
        error: "حدث خطأ أثناء تسجيل الخروج",
      },
      { status: 500 }
    )
  }
}
