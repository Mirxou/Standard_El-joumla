import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function isRTLLocale(locale?: string) {
  const l = (locale || "").toLowerCase()
  // Common RTL language codes
  const rtl = ["ar", "he", "fa", "ur", "ps" ]
  return rtl.includes(l)
}
