"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { apiClient } from "@/lib/api/client"
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

  const checkAuth = async () => {
    try {
      const storedUser = localStorage.getItem("user")
      const token = localStorage.getItem("access_token")

      if (storedUser && token) {
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
      const token = localStorage.getItem('access_token')
      
      if (!token) return

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

      // تخزين التوكن والمعلومات
      const userData: User = {
        id: data.user?.id || 0,
        email,
        username: data.user?.username || email,
        name: data.full_name || data.user?.full_name || data.user?.username || "مستخدم",
        full_name: data.full_name || "",
        role: data.user?.role || data.role || "مستخدم",
        avatar: null,
        is_active: true,
        loggedInAt: new Date().toISOString(),
      }

      localStorage.setItem("user", JSON.stringify(userData))
      localStorage.setItem("access_token", data.access_token)
      if (data.refresh_token) {
        localStorage.setItem("refresh_token", data.refresh_token)
      }

      // تعيين التوكن في العميل
      apiClient.setToken(data.access_token)

      // تعيين Cookie للميدل وير
      try {
        const expiresIn = data.expires_in || 86400
        document.cookie = `auth-token=${data.access_token}; path=/; max-age=${expiresIn}`
      } catch { }

      setUser(userData)

      // جلب الشركات بعد تسجيل الدخول
      await fetchCompanies()

      toast.success("تم تسجيل الدخول بنجاح!")
      router.push("/")
    } catch (error: any) {
      toast.error(error.message || "حدث خطأ أثناء تسجيل الدخول")
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem("user")
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    localStorage.removeItem("company_id")
    localStorage.removeItem("rememberMe")
    try {
      document.cookie = "auth-token=; path=/; max-age=0"
    } catch { }
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
