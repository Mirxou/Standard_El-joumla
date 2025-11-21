"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import type { Message } from "@/lib/types"
import { usePiNetworkAuthentication } from "./use-pi-network-authentication"
import { APP_CONFIG, BACKEND_CONFIG } from "@/lib/app-config"

// Helper function to create messages
const createMessage = (text: Message["text"], sender: Message["sender"], id?: Message["id"]): Message => ({
  id: id || Date.now().toString(),
  text,
  sender,
  timestamp: new Date(),
})

export const useChatbot = () => {
  const { isAuthenticated, authMessage, piAccessToken, reinitialize } = usePiNetworkAuthentication()

  const [messages, setMessages] = useState<Message[]>([createMessage(APP_CONFIG.WELCOME_MESSAGE, "ai", "1")])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const thinkingTimerRef = useRef<NodeJS.Timeout | null>(null)

  const showThinking = () => {
    const thinkingMessage = createMessage("Thinking... (0)", "ai", "thinking")
    setMessages((prev) => [...prev, thinkingMessage])

    let seconds = 0
    thinkingTimerRef.current = setInterval(() => {
      seconds += 1
      setMessages((prevMessages) =>
        prevMessages.map((msg) => (msg.id === "thinking" ? { ...msg, text: `Thinking... (${seconds})` } : msg)),
      )
    }, 1000)
  }

  const hideThinking = () => {
    if (thinkingTimerRef.current) {
      clearInterval(thinkingTimerRef.current)
      thinkingTimerRef.current = null
    }
    setMessages((prev) => prev.filter((msg) => msg.id !== "thinking"))
  }

  const sendMessage = async () => {
    if (!isAuthenticated || !input.trim()) return

    const userMessage = createMessage(input.trim(), "user")
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    showThinking()

    try {
      const response = await fetch(`${BACKEND_CONFIG.BASE_URL}/v1/chat/default`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        mode: "cors",
        body: JSON.stringify({ message: userMessage.text }),
      })

      hideThinking()

      if (response.status === 429) {
        const errorData = await response.json()
        const errorMessage = createMessage(
          errorData.error_type === "daily_limit_exceeded"
            ? errorData.error
            : "Too many requests. Please try again later.",
          "ai",
        )
        setMessages((prev) => [...prev, errorMessage])
        return
      }

      const data = await response.json()

      if (data.messages && Array.isArray(data.messages)) {
        const aiMsg = data.messages.reverse().find((m: any) => m.sender === "ai")
        const botMessage = createMessage(aiMsg ? aiMsg.text : "No AI response received.", "ai")
        setMessages((prev) => [...prev, botMessage])
      } else {
        const errorMessage = createMessage("No response from backend.", "ai")
        setMessages((prev) => [...prev, errorMessage])
      }
    } catch (error) {
      hideThinking()
      console.error("[v0] Chat error:", error)
      const errorMessage = createMessage("Error contacting backend.", "ai")
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleImageUpload = () => {
    if (isLoading || !isAuthenticated) return

    const input = document.createElement("input")
    input.type = "file"
    input.accept = "image/*"
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (!file) return

      setIsLoading(true)
      showThinking()

      try {
        const formData = new FormData()
        formData.append("image", file)

        const uploadResponse = await fetch(BACKEND_CONFIG.UPLOAD_URL, {
          method: "POST",
          credentials: "include",
          mode: "cors",
          body: formData,
        })

        if (!uploadResponse.ok) {
          throw new Error("Image upload failed")
        }

        const { url } = await uploadResponse.json()

        const imageMessage = createMessage(`[صورة / Image]: ${url}`, "user")
        setMessages((prev) => [...prev, imageMessage])

        const response = await fetch(`${BACKEND_CONFIG.BASE_URL}/v1/chat/default`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          mode: "cors",
          body: JSON.stringify({ message: url, type: "image" }),
        })

        hideThinking()

        if (response.ok) {
          const data = await response.json()
          if (data.messages && Array.isArray(data.messages)) {
            const aiMsg = data.messages.reverse().find((m: any) => m.sender === "ai")
            const botMessage = createMessage(aiMsg ? aiMsg.text : "تم استلام الصورة / Image received.", "ai")
            setMessages((prev) => [...prev, botMessage])
          }
        }
      } catch (error) {
        hideThinking()
        console.error("[v0] Upload error:", error)
        const errorMessage = createMessage("فشل رفع الصورة / Image upload failed.", "ai")
        setMessages((prev) => [...prev, errorMessage])
      } finally {
        setIsLoading(false)
      }
    }

    input.click()
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value)
  }

  useEffect(() => {
    return () => {
      if (thinkingTimerRef.current) {
        clearInterval(thinkingTimerRef.current)
      }
    }
  }, [])

  return {
    messages,
    input,
    isLoading,
    isAuthenticated,
    authMessage,
    sendMessage,
    handleKeyPress,
    handleInputChange,
    handleImageUpload,
    reinitialize,
  }
}
