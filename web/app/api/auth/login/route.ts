import { NextResponse } from "next/server"
import { API_CONFIG, getFullURL } from "@/lib/config/api"

export async function POST(request: Request) {
  try {
    const payload = await request.json()
    const username = payload.username || payload.email
    const password = payload.password

    const backendResponse = await fetch(getFullURL(API_CONFIG.ENDPOINTS.AUTH.LOGIN), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    })

    const data = await backendResponse.json().catch(() => null)

    if (!backendResponse.ok) {
      return NextResponse.json(
        {
          success: false,
          error: data?.detail || data?.error || "البريد الإلكتروني أو كلمة المرور غير صحيحة",
        },
        { status: backendResponse.status }
      )
    }

    const response = NextResponse.json(data, { status: 200 })
    if (data?.access_token) {
      response.cookies.set("auth-token", data.access_token, {
        path: "/",
        httpOnly: false,
        sameSite: "lax",
        secure: process.env.NODE_ENV === "production",
        maxAge: data?.expires_in || 86400,
      })
    }
    return response
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
