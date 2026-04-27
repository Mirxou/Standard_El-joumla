import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const response = NextResponse.json({
      success: true,
      message: "تم تسجيل الخروج بنجاح",
    })

    response.cookies.set("auth-token", "", { path: "/", maxAge: 0 })
    return response
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
