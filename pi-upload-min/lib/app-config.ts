// *** Configurable variables for the app ***
// Update is driven by environment variables for production readiness

// App Configuration
export const APP_CONFIG = {
  APP_ID: process.env.NEXT_PUBLIC_PI_APP_ID || "",

  WELCOME_MESSAGE:
    "مرحباً بك! 👋\nأنا Standard Bot، مساعدك الذكي لإدارة تجارة الجملة.\nكيف يمكنني مساعدتك اليوم؟",

  NAME: "Standard Bot Ultra",

  DESCRIPTION:
    "Empower your wholesale hustle with real-time stock alerts, smart inventory tracking & instant profit insights—all in one sleek, intuitive app.",

  DEFAULT_LOCALE: (process.env.NEXT_PUBLIC_DEFAULT_LOCALE || "ar").toLowerCase(),
} as const

// Colors Configuration
export const COLORS = {
  BACKGROUND: "#0b1220",
  PRIMARY: "#06b6d4",
} as const

// Pi Network Configuration
export const PI_NETWORK_CONFIG = {
  SDK_URL: "https://sdk.minepi.com/pi-sdk.js",
  SANDBOX: String(process.env.NEXT_PUBLIC_SANDBOX).toLowerCase() === "true", // Set via env var
} as const

// Backend Configuration - UPDATE THESE VALUES
export const BACKEND_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_STANDARD_API_BASE || "",
  API_KEY: process.env.NEXT_PUBLIC_STANDARD_API_KEY || "",
  UPLOAD_URL: process.env.NEXT_PUBLIC_STANDARD_UPLOAD_URL || "",
  MEDIA_BASE: process.env.NEXT_PUBLIC_STANDARD_MEDIA_BASE || "",
} as const

// Backend URLs - Auto-generated
export const BACKEND_URLS = {
  LOGIN: `${BACKEND_CONFIG.BASE_URL}/v1/login`,
  CHAT: `${BACKEND_CONFIG.BASE_URL}/v1/chat/default`,
  UPLOAD: BACKEND_CONFIG.UPLOAD_URL,
} as const
