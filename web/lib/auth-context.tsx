"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { apiClient, getCookie, deleteCookie } from "@/lib/api/client"
import { API_CONFIG } from "@/lib/config/api"
import type { User, Company, AuthContextType, LoginResponse } from "@/lib/types"

// تصدير نوع AuthContextType للاستخدام الخارجي
export type { AuthContextType }

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [companies, setCompanies] = useState<Company[]>([])
  const [currentCompany, setCurrentCompany] = useState<Company | null>(null)
  const router = useRouter()
  const isProduction = process.env.NODE_ENV === 'production'

  const checkAuth = async () => {
    try {
      // في الإنتاج: قراءة من httpOnly cookie فقط (لا يمكن قراءة التوكن من JS لكن سيتم إرساله تلقائياً)
      // في التطوير: استخدام localStorage للتوافق
      const isProduction = process.env.NODE_ENV === 'production'
      
      let storedUser = localStorage.getItem("user")
      let token = localStorage.getItem("access_token")
      
      // في التطوير، نقرأ من cookie كـ fallback
      // في الإنتاج، httpOnly cookie لا يمكن قراءته لكن يتم إرساله تلقائياً مع الطلبات
      if (!token && !isProduction) {
        token = getCookie('access_token')
      }

      // في الإنتاج، إذا كان هناك user في localStorage بدون token، استخدمه
      // لكن apiClient لا يحتاج token لأن cookies ستُرسل تلقائياً
      if (storedUser && isProduction) {
        const user = JSON.parse(storedUser) as User
        setUser(user)
        // في الإنتاج، لا نحتاج apiClient.setToken() لأن httpOnly cookies تُرسل تلقائياً
        
        // تحديث قائمة الشركات
        await fetchCompanies()
      } else if (storedUser && token) {
        // في التطوير، نستخدم localStorage + apiClient.setToken()
        const user = JSON.parse(storedUser) as User
        setUser(user)
        apiClient.setToken(token)

        // تحديث قائمة الشركات
        await fetchCompanies()
      } else {
        // إذا لم يكن هناك مستخدم مسجل، نوجه لصفحة تسجيل الدخول
        if (typeof window !== 'undefined' && window.location.pathname !== "/login") {
          router.push("/login")
        }
      }
    } catch (error) {
      console.error("Error checking auth:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchCompanies = async () => {
    try {
      // في الإنتاج: httpOnly cookie يُرسل تلقائياً، لا حاجة لـ token من localStorage
      // في التطوير: نأخذ token من localStorage
      const isProduction = process.env.NODE_ENV === 'production'
      let token: string | null = null
      
      if (!isProduction) {
        token = localStorage.getItem('access_token')
      }

      // في الإنتاج، apiClient يرسل cookies تلقائياً بدون token صريح
      // في التطوير، نتحقق من وجود token
      if (!isProduction && !token) return

      const data = await apiClient.get<Company[]>(API_CONFIG.ENDPOINTS.AUTH.COMPANIES)
      setCompanies(data)

      // تحديد الشركة الحالية
      const storedCompanyId = localStorage.getItem("company_id")
      if (storedCompanyId) {
        const found = data.find((c) => c.id.toString() === storedCompanyId)
        if (found) {
          setCurrentCompany(found)
          apiClient.setCompanyId(storedCompanyId)
        } else if (data.length > 0) {
          selectCompany(data[0])
        }
      } else if (data.length > 0) {
        selectCompany(data[0])
      }
    } catch (e) {
      console.error("Error fetching companies", e)
    }
  }

  const selectCompany = async (company: Company) => {
    setCurrentCompany(company)
    apiClient.setCompanyId(company.id.toString())
    localStorage.setItem("company_id", company.id.toString())

    toast.success(`تم التحويل إلى شركة: ${company.name}`)

    // بدلاً من reload - جلب البيانات الجديدة
    // هذا يتم عبر dependency على currentCompany في المكونات
  }

  useEffect(() => {
    checkAuth()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      // إعداد البيانات للـ API
      const loginPayload = {
        username: email,
        password: password
      }

      const data = await apiClient.post<LoginResponse>(API_CONFIG.ENDPOINTS.AUTH.LOGIN, loginPayload)

      // تخزين التوكن والمعلومات - يدعم الاستجابة المسطحة من backend أو user المتداخلة
      const normalizedUser = data.user ?? {
        id: data.user_id || 0,
        email,
        username: data.username || email,
        full_name: data.full_name || data.username || email,
        name: data.full_name || data.username || email,
        role: data.role || (data.role_id === 1 ? "مدير النظام" : "مستخدم"),
        avatar: null,
        is_active: data.is_active ?? true,
        loggedInAt: new Date().toISOString(),
      }

      const userData: User = {
        id: normalizedUser.id,
        email: normalizedUser.email,
        username: normalizedUser.username,
        name: normalizedUser.name,
        full_name: normalizedUser.full_name,
        role: normalizedUser.role,
        avatar: normalizedUser.avatar,
        is_active: normalizedUser.is_active,
        loggedInAt: normalizedUser.loggedInAt,
      }

      // في التطوير: تخزين في localStorage
      // في الإنتاج: httpOnly cookie يُعيّن من الخادم، نحتاج localStorage للمعلومات غير الحساسة فقط
      const isProduction = process.env.NODE_ENV === 'production'
      
      localStorage.setItem("user", JSON.stringify(userData))
      
      if (!isProduction) {
        // في التطوير فقط: تخزين token في localStorage
        localStorage.setItem("access_token", data.access_token)
        if (data.refresh_token) {
          localStorage.setItem("refresh_token", data.refresh_token)
        }
        // تعيين التوكن في apiClient
        apiClient.setToken(data.access_token)
      }
      // في الإنتاج: لا حاجة لتعيين token في localStorage لأن httpOnly cookie يُرسل تلقائياً

      // تعيين Cookie للميدل وير - استخدام Secure و HttpOnly attributes في الإنتاج
      try {
        const expiresIn = data.expires_in || 86400
        // في الإنتاج، يجب استخدام HttpOnly cookies من الخادم
        // هذا للعرض فقط في التطوير
        const isProduction = process.env.NODE_ENV === 'production'
        const cookieOptions = isProduction 
          ? `; path=/; max-age=${expiresIn}; SameSite=Strict; Secure`
          : `; path=/; max-age=${expiresIn}`
        document.cookie = `auth-token=${data.access_token}${cookieOptions}`
      } catch { }

      setUser(userData)

      // جلب الشركات بعد تسجيل الدخول
      await fetchCompanies()

      toast.success("تم تسجيل الدخول بنجاح!")
      router.push("/")
    } catch (error: any) {
      console.error("Login error:", error)

      // تحسين رسائل الخطأ
      // تحسين معالجة الأخطاء
      let errorMessage = "حدث خطأ أثناء تسجيل الدخول"

      const errorMsg = error.message || "";

      if (errorMsg.includes("fetch") || errorMsg.includes("Failed to fetch") || errorMsg.includes("Network request failed")) {
        errorMessage = "لا يمكن الاتصال بالخادم. تأكد من تشغيل Backend API على http://localhost:8000"
      } else if (error.status === 401) {
        errorMessage = "اسم المستخدم أو كلمة المرور غير صحيحة"
      } else if (error.status === 404) {
        errorMessage = "الخادم غير متاح (404). تأكد من المسار الصحيح للـ API"
      } else if (error.status === 500) {
        errorMessage = "خطأ داخلي في الخادم (500). يرجى المحاولة لاحقاً"
      } else if (error.data?.detail) {
        errorMessage = error.data.detail
      } else if (errorMsg) {
        errorMessage = errorMsg
      }

      toast.error(errorMessage)
      throw error
    }
  }

  const logout = async () => {
    // Call logout API endpoint to clear server-side cookies
    try {
      await apiClient.post('/api/v1/auth/logout', {})
    } catch {
      // Continue even if API call fails
    }
    
    // Clear client-side storage
    localStorage.removeItem("user")
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    localStorage.removeItem("company_id")
    localStorage.removeItem("rememberMe")
    
    // Clear any remaining cookies
    deleteCookie('access_token')
    deleteCookie('refresh_token')
    deleteCookie('auth-token')
    
    setUser(null)
    toast.info("تم تسجيل الخروج بنجاح")
    router.push("/login")
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        companies,
        currentCompany,
        login,
        logout,
        checkAuth,
        selectCompany,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
