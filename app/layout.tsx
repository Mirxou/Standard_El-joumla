import type React from "react"
import type { Metadata } from "next"
import { Inter, Cairo, Noto_Kufi_Arabic } from "next/font/google"
import "./globals.css"
import { APP_CONFIG } from "@/lib/app-config"
import { isRTLLocale } from "@/lib/utils"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
})

const cairo = Cairo({
  subsets: ["arabic", "latin"],
  variable: "--font-cairo",
  display: "swap",
})

const notoKufiArabic = Noto_Kufi_Arabic({
  subsets: ["arabic"],
  variable: "--font-noto-kufi",
  display: "swap",
})

export const metadata: Metadata = {
  title: "Standard Bot Ultra",
  description: "Professional wholesale management with real-time alerts and smart tracking",
  generator: "v0.dev",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const locale = APP_CONFIG.DEFAULT_LOCALE
  const dir = isRTLLocale(locale) ? "rtl" : "ltr"
  return (
    <html lang={locale} dir={dir} className="dark">
      <body className={`${inter.variable} ${cairo.variable} ${notoKufiArabic.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  )
}
