"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Package, Mail, Lock, Eye, EyeOff, AlertCircle, ArrowRight, ShieldCheck } from "lucide-react"
import { toast } from "sonner"

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuth()
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [errors, setErrors] = useState({ email: "", password: "" })

  const validateForm = () => {
    const newErrors = { email: "", password: "" }
    let isValid = true

    if (!email) {
      newErrors.email = "اسم المستخدم أو البريد الإلكتروني مطلوب"
      isValid = false
    }

    if (!password) {
      newErrors.password = "كلمة المرور مطلوبة"
      isValid = false
    }

    setErrors(newErrors)
    return isValid
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    setIsLoading(true)

    try {
      await login(email, password)
      if (rememberMe) {
        localStorage.setItem("rememberMe", "true")
      }
      toast.success("تم تسجيل الدخول بنجاح!")
      // Redirection happens in login function usually, but let's be safe
      router.push("/dashboard")
    } catch (error: any) {
      const message = error?.message || "اسم المستخدم أو كلمة المرور غير صحيحة"
      toast.error(message)
      console.error(error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen relative overflow-hidden flex items-center justify-center p-4 bg-background" dir="rtl">
      {/* Dynamic Background Elements */}
      <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-primary/10 rounded-full blur-[120px] animate-pulse" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-500/10 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '2s' }} />
      
      <div className="w-full max-w-md relative z-10 animate-fadeIn">
        {/* Logo Section */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-primary to-blue-600 rounded-3xl mb-6 shadow-2xl shadow-primary/20 rotate-3 hover:rotate-0 transition-transform duration-500">
            <Package className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl font-black tracking-tight text-foreground mb-2">
            Standard <span className="text-primary">El-Joumla</span>
          </h1>
          <p className="text-muted-foreground font-medium">نظام إدارة الجملة والمخازن المتطور</p>
        </div>

        {/* Login Card with Glassmorphism */}
        <Card className="backdrop-blur-xl bg-card/80 border-border/50 shadow-2xl overflow-hidden">
          <div className="h-1.5 w-full bg-gradient-to-r from-primary via-blue-500 to-primary animate-gradient-x" />
          
          <CardHeader className="space-y-2 pb-6">
            <div className="flex justify-center mb-2">
              <div className="px-3 py-1 bg-primary/10 text-primary rounded-full text-xs font-bold flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5" />
                دخول آمن
              </div>
            </div>
            <CardTitle className="text-2xl font-bold text-center">أهلاً بك مجدداً</CardTitle>
            <CardDescription className="text-center font-medium">
              يرجى إدخال بيانات الاعتماد للوصول إلى النظام
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-5">
              {/* Username/Email Input */}
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-bold mr-1">اسم المستخدم أو البريد</Label>
                <div className="relative group">
                  <Mail className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted-foreground h-5 w-5 group-focus-within:text-primary transition-colors" />
                  <Input
                    id="email"
                    type="text"
                    placeholder="أدخل اسم المستخدم"
                    className={`h-12 pr-11 bg-background/50 border-border/50 focus:ring-primary/20 focus:border-primary transition-all ${errors.email ? "border-destructive ring-destructive/10" : ""}`}
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value)
                      setErrors({ ...errors, email: "" })
                    }}
                    disabled={isLoading}
                  />
                </div>
                {errors.email && (
                  <div className="flex items-center gap-1.5 text-destructive text-xs font-bold mt-1.5 px-1 animate-fadeIn">
                    <AlertCircle className="h-3.5 w-3.5" />
                    <span>{errors.email}</span>
                  </div>
                )}
              </div>

              {/* Password Input */}
              <div className="space-y-2">
                <div className="flex items-center justify-between px-1">
                  <Label htmlFor="password" className="text-sm font-bold">كلمة المرور</Label>
                </div>
                <div className="relative group">
                  <Lock className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted-foreground h-5 w-5 group-focus-within:text-primary transition-colors" />
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••••••"
                    className={`h-12 pr-11 pl-12 bg-background/50 border-border/50 focus:ring-primary/20 focus:border-primary transition-all ${errors.password ? "border-destructive ring-destructive/10" : ""}`}
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value)
                      setErrors({ ...errors, password: "" })
                    }}
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary transition-colors"
                    disabled={isLoading}
                    title={showPassword ? "إخفاء كلمة المرور" : "إظهار كلمة المرور"}
                  >
                    {showPassword ? (
                      <EyeOff className="h-5 w-5" />
                    ) : (
                      <Eye className="h-5 w-5" />
                    )}
                  </button>
                </div>
                {errors.password && (
                  <div className="flex items-center gap-1.5 text-destructive text-xs font-bold mt-1.5 px-1 animate-fadeIn">
                    <AlertCircle className="h-3.5 w-3.5" />
                    <span>{errors.password}</span>
                  </div>
                )}
              </div>

              {/* Remember Me & Forgot Password */}
              <div className="flex items-center justify-between px-1 py-1">
                <div className="flex items-center gap-2.5">
                  <Checkbox
                    id="remember"
                    checked={rememberMe}
                    onCheckedChange={(checked) => setRememberMe(checked as boolean)}
                    disabled={isLoading}
                    className="data-[state=checked]:bg-primary"
                  />
                  <Label htmlFor="remember" className="text-xs font-bold cursor-pointer text-muted-foreground hover:text-foreground transition-colors">
                    تذكرني على هذا الجهاز
                  </Label>
                </div>
                <Button
                  type="button"
                  variant="link"
                  className="text-xs font-bold text-primary hover:text-primary/80 p-0 h-auto"
                  disabled={isLoading}
                >
                  نسيت كلمة المرور؟
                </Button>
              </div>

              {/* Login Button */}
              <Button
                type="submit"
                className="w-full h-12 text-sm font-bold bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg shadow-primary/20 transition-all hover:scale-[1.01] active:scale-[0.99] group"
                disabled={isLoading}
              >
                {isLoading ? (
                  <div className="flex items-center gap-3">
                    <div className="w-5 h-5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                    <span>جاري التحقق من البيانات...</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-2">
                    <span>دخول آمن</span>
                    <ArrowRight className="w-4 h-4 mr-1 group-hover:-translate-x-1 transition-transform rtl:rotate-180" />
                  </div>
                )}
              </Button>
            </form>

            {/* Info Section */}
            <div className="mt-8 pt-6 border-t border-border/50 text-center">
              <p className="text-xs font-medium text-muted-foreground">
                في حال وجود مشكلة في الدخول، يرجى التواصل مع الدعم الفني
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="mt-8 flex justify-center gap-6">
          <p className="text-xs font-bold text-muted-foreground/60">© 2026 Mirxou Standard</p>
          <div className="flex gap-4">
            <button className="text-xs font-bold text-muted-foreground/60 hover:text-primary transition-colors">الدعم</button>
            <button className="text-xs font-bold text-muted-foreground/60 hover:text-primary transition-colors">الخصوصية</button>
          </div>
        </div>
      </div>
      
      <style jsx global>{`
        @keyframes gradient-x {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        .animate-gradient-x {
          background-size: 200% 200%;
          animation: gradient-x 3s ease infinite;
        }
      `}</style>
    </div>
  )
}
