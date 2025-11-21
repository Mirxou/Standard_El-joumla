"use client"

import { useState, useEffect } from "react"
import { PI_NETWORK_CONFIG, BACKEND_CONFIG } from "@/lib/app-config"

// Function to dynamically load Pi SDK script
const loadPiSDK = (): Promise<void> => {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script")
    script.src = PI_NETWORK_CONFIG.SDK_URL
    script.async = true

    script.onload = () => {
      console.info("✅ Pi SDK loaded successfully")
      resolve()
    }

    script.onerror = () => {
      console.error("❌ Failed to load Pi SDK")
      reject(new Error("Failed to load Pi SDK script"))
    }

    document.head.appendChild(script)
  })
}

export const usePiNetworkAuthentication = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [authMessage, setAuthMessage] = useState("جاري المصادقة... / Authenticating...")
  const [piAccessToken, setPiAccessToken] = useState<string | null>(null)

  // Utility: add timeouts to async steps to avoid hanging UI
  const withTimeout = async <T,>(promise: Promise<T>, ms: number, label: string): Promise<T> => {
    return await new Promise<T>((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error(`${label} timeout (${ms}ms)`)), ms)
      promise
        .then((v) => {
          clearTimeout(timer)
          resolve(v)
        })
        .catch((e) => {
          clearTimeout(timer)
          reject(e)
        })
    })
  }

  const authenticateWithPi = async (): Promise<string> => {
    console.log("🔐 Starting Pi Network authentication...")

    try {
      const piAuthResult = await window.Pi.authenticate(["username", "roles"])
      console.log("✅ Pi authentication successful")

      if (piAuthResult?.accessToken) {
        setPiAccessToken(piAuthResult.accessToken)
        console.log("✅ Access token received")
        return piAuthResult.accessToken
      }
      throw new Error("No access token received")
    } catch (error) {
      console.error("❌ Pi authentication error:", error)
      throw error
    }
  }

  const loginToBackend = async (piToken: string): Promise<void> => {
    console.log("🔐 Logging in to backend...")

    const response = await fetch(`${BACKEND_CONFIG.BASE_URL}/v1/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      mode: "cors",
      body: JSON.stringify({
        pi_auth_token: piToken,
      }),
    })

    if (!response.ok) {
      throw new Error(`Backend login failed: ${response.status}`)
    }

    console.log("✅ Backend login successful")
  }

  const initializePiAndAuthenticate = async () => {
    try {
      // Step 1: Load Pi SDK
      setAuthMessage("تحميل SDK... / Loading SDK...")
      console.log("📥 Loading Pi SDK from:", PI_NETWORK_CONFIG.SDK_URL)
      await withTimeout(loadPiSDK(), 8000, "Pi SDK load")

      // Step 2: Verify Pi object
      if (typeof window.Pi === "undefined") {
        throw new Error("Pi SDK not available - must use Pi Browser")
      }
      console.log("✅ Pi SDK available")

      // Step 3: Initialize Pi Network
      setAuthMessage("تهيئة Pi Network... / Initializing Pi...")
      console.log("⚙️ Initializing Pi Network (sandbox:", PI_NETWORK_CONFIG.SANDBOX, ")")
      await withTimeout(window.Pi.init({ version: "2.0", sandbox: PI_NETWORK_CONFIG.SANDBOX }), 5000, "Pi init")
      console.log("✅ Pi Network initialized")

      // Step 4: Authenticate with Pi
      setAuthMessage("جاري المصادقة... / Authenticating...")
      const token = await withTimeout(authenticateWithPi(), 10000, "Pi authenticate")

      // Step 5: Login to backend
      setAuthMessage("تسجيل الدخول... / Logging in...")
      await loginToBackend(token)

      // Success
      console.log("✅ Authentication complete!")
      setIsAuthenticated(true)
      setAuthMessage("متصل / Connected")
    } catch (err) {
      console.error("❌ Authentication failed:", err)

      let errorMessage = "فشل المصادقة / Authentication failed. "

      if (err instanceof Error) {
        if (err.message.includes("Backend login failed")) {
          errorMessage += "خطأ في الخادم / Backend error. "
        } else if (err.message.includes("Pi SDK not available")) {
          errorMessage += "يجب فتح التطبيق داخل Pi Browser / Open in Pi Browser. "
        } else if (err.message.includes("No access token")) {
          errorMessage += "فشل الحصول على رمز الوصول / Failed to get access token. "
        } else if (err.message.includes("timeout")) {
          errorMessage += "انتهت المهلة، تحقق من الشبكة أو استخدم Pi Browser / Timed out. Check network or use Pi Browser. "
        } else {
          errorMessage += err.message + " "
        }
      }

      errorMessage += "اضغط إعادة المحاولة / Press Retry."
      setAuthMessage(errorMessage)
    }
  }

  useEffect(() => {
    initializePiAndAuthenticate()
  }, [])

  return {
    isAuthenticated,
    authMessage,
    piAccessToken,
    reinitialize: initializePiAndAuthenticate,
  }
}
