"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login")
    }
  }, [isAuthenticated, isLoading, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0f172a]">
        <div className="flex flex-col items-center gap-6">
          <div className="relative w-20 h-20">
            <div className="absolute inset-0 rounded-full border-4 border-cyan-500/20" />
            <div className="absolute inset-0 rounded-full border-4 border-cyan-500 border-t-transparent animate-spin" />
            <div className="absolute inset-4 rounded-full bg-cyan-500/10 blur-md animate-pulse" />
          </div>
          <p className="text-cyan-400/80 font-medium tracking-widest text-sm animate-pulse">جاري التحقق من الأمان...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return <>{children}</>
}
