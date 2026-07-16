import type React from "react"
import type { Metadata } from "next"
import { Toaster } from "@/components/ui/sonner"
import { AuthProvider } from "@/lib/auth-context"
import { NotificationProvider } from "@/lib/notifications/notification-context"
import ErrorBoundary from "@/components/error-boundary"
import "./globals.css"

export const metadata: Metadata = {
  title: "Standard - نظام إدارة المخزون المتكامل",
  description: "نظام إدارة مخزون متكامل لتجارة المواد الغذائية والصحة والنظافة والجمال والإلكترونيات",
  generator: 'v0.app'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ar" dir="rtl">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Cairo:wght@200;300;400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="arabic-text" suppressHydrationWarning>
        <ErrorBoundary>
          <AuthProvider>
            <NotificationProvider>
              {children}
            </NotificationProvider>
          </AuthProvider>
        </ErrorBoundary>
        <Toaster position="bottom-left" richColors theme="dark" />
      </body>
    </html>
  )
}
