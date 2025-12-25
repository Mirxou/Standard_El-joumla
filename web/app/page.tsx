"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { ArrowLeft, Package, BarChart3, Users, Settings } from "lucide-react"
import Dashboard from "@/components/dashboard"
import AuthGuard from "@/components/auth-guard"

export default function Home() {
  const [showWelcome, setShowWelcome] = useState(false) // تعطيل شاشة الترحيب للوصول المباشر
  const [currentTime, setCurrentTime] = useState<Date | null>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    setCurrentTime(new Date())
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  if (showWelcome) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 via-white to-green-500 flex items-center justify-center p-4">
        <Card className="w-full max-w-2xl shadow-2xl border-0 bg-white/80 backdrop-blur-sm">
          <CardContent className="p-12 text-center">
            <div className="animate-fadeIn">
              {/* الشعار */}
              <div className="mb-8">
                <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-blue-700 to-green-700 rounded-full flex items-center justify-center shadow-lg">
                  <Package className="w-12 h-12 text-white" />
                </div>
                <h1 className="text-4xl font-bold text-gray-800 mb-2">Standard | شعارنا للأبد</h1>
              </div>

              {/* الوصف */}
              <div className="mb-8 space-y-4">
                <h2 className="text-2xl font-bold text-gray-700">نظام إدارة المخزون المتكامل</h2>
                <p className="text-gray-600 leading-relaxed">
                  نظام شامل لإدارة المخزون والمبيعات والفواتير مع تقارير مرئية متقدمة
                  <br />
                  مخصص للتجارة في جميع الفئات: المواد الغذائية، الصحة، النظافة، الجمال، الإلكترونيات
                </p>
              </div>

              {/* الوقت والتاريخ */}
              <div className="mb-8 p-4 bg-gray-50 rounded-lg">
                {mounted && currentTime ? (
                  <>
                    <p className="text-lg font-semibold text-gray-700">
                      {currentTime.toLocaleDateString("ar-SA", {
                        weekday: "long",
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                      })}
                    </p>
                    <p className="text-2xl font-bold text-blue-700">{currentTime.toLocaleTimeString("ar-SA")}</p>
                  </>
                ) : (
                  <div className="h-16 flex items-center justify-center">
                    <div className="animate-pulse text-gray-400">جاري التحميل...</div>
                  </div>
                )}
              </div>

              {/* الميزات الرئيسية */}
              <div className="grid grid-cols-2 gap-4 mb-8">
                <div className="p-4 bg-blue-500 rounded-lg">
                  <Package className="w-8 h-8 text-white mx-auto mb-2" />
                  <p className="text-sm font-semibold text-white">إدارة المخزون</p>
                </div>
                <div className="p-4 bg-green-500 rounded-lg">
                  <BarChart3 className="w-8 h-8 text-white mx-auto mb-2" />
                  <p className="text-sm font-semibold text-white">تقارير الأرباح</p>
                </div>
                <div className="p-4 bg-purple-500 rounded-lg">
                  <Users className="w-8 h-8 text-white mx-auto mb-2" />
                  <p className="text-sm font-semibold text-white">إدارة العملاء</p>
                </div>
                <div className="p-4 bg-orange-500 rounded-lg">
                  <Settings className="w-8 h-8 text-white mx-auto mb-2" />
                  <p className="text-sm font-semibold text-white">إعدادات متقدمة</p>
                </div>
              </div>

              {/* زر الدخول */}
              <Button
                type="button"
                onClick={(e) => {
                  e.preventDefault()
                  setShowWelcome(false)
                }}
                className="bg-gradient-to-r from-blue-700 to-green-700 hover:from-blue-800 hover:to-green-800 text-white px-8 py-3 text-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer"
              >
                دخول النظام
                <ArrowLeft className="mr-2 h-5 w-5" />
              </Button>

              {/* معلومات إضافية */}
              <div className="mt-8 text-xs text-gray-500">
                <p>الإصدار 1.0.0 | تطوير محلي مع إمكانية التوسع الأونلاين</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return <Dashboard />
}
