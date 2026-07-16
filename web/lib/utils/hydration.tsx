'use client'

import React from 'react'

// Utility to prevent hydration errors
// يمنع أخطاء hydration عند استخدام البيانات الديناميكية

export function suppressHydrationWarning() {
  return { suppressHydrationWarning: true }
}

// Hook للتحقق من mounting في المتصفح
export function useIsMounted() {
  const [mounted, setMounted] = React.useState(false)
  
  React.useEffect(() => {
    setMounted(true)
  }, [])
  
  return mounted
}

// Component wrapper لمنع hydration errors
export function ClientOnly({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = React.useState(false)
  
  React.useEffect(() => {
    setMounted(true)
  }, [])
  
  if (!mounted) return null
  
  return <>{children}</>
}
