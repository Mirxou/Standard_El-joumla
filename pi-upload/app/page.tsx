"use client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Send, User, Bot, ImageIcon, RefreshCw } from 'lucide-react'
import { useChatbot } from "@/hooks/use-chatbot"
import { useScrollToBottom } from "@/hooks/use-scroll-to-bottom"
import { APP_CONFIG } from "@/lib/app-config"

export default function ChatBot() {

  const {
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
  } = useChatbot()

  const { bottomRef } = useScrollToBottom([messages])

  if (!isAuthenticated) {
    return (
      <div className="fixed inset-0 bg-background z-50 flex items-center justify-center p-4 md:p-6">
        <div className="w-full max-w-2xl space-y-6">
          <div className="text-center space-y-4">
            <div className="text-2xl md:text-3xl font-bold text-primary">{APP_CONFIG.NAME}</div>
            <div className="text-sm md:text-base text-muted-foreground max-w-md mx-auto leading-relaxed px-4">
              {authMessage}
            </div>
            <div className="animate-spin rounded-full h-12 w-12 border-3 border-primary border-t-transparent mx-auto"></div>

            {authMessage.includes("Failed") && (
              <div className="flex justify-center pt-4">
                <Button onClick={reinitialize} variant="outline" className="gap-2">
                  <RefreshCw size={16} />
                  <span>إعادة المحاولة / Retry</span>
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-center min-h-screen p-4 md:p-6 bg-background">
      <Card className="w-full max-w-md h-[600px] md:h-[700px] flex flex-col shadow-soft rounded-3xl overflow-hidden border-0 animate-fade-in">
        <CardHeader className="bg-primary text-primary-foreground rounded-t-3xl py-6 px-6 space-y-2">
          <CardTitle className="text-center">
            <div className="text-xl md:text-2xl font-bold tracking-tight leading-tight">{APP_CONFIG.NAME}</div>
            {APP_CONFIG.DESCRIPTION && (
              <div className="text-sm md:text-base opacity-90 mt-3 font-normal leading-relaxed text-balance">
                {APP_CONFIG.DESCRIPTION}
              </div>
            )}
          </CardTitle>
        </CardHeader>

        <CardContent className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 bg-card scroll-smooth">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 animate-fade-in ${message.sender === "user" ? "flex-row-reverse" : "flex-row"}`}
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 transition-smooth ${
                  message.sender === "user" ? "bg-muted text-muted-foreground" : "bg-primary text-primary-foreground"
                }`}
              >
                {message.sender === "user" ? <User size={18} strokeWidth={1.5} /> : <Bot size={18} strokeWidth={1.5} />}
              </div>

              <div
                className={`max-w-[75%] px-4 py-3 rounded-2xl transition-smooth ${
                  message.sender === "user"
                    ? "bg-primary text-primary-foreground"
                    : message.id === "thinking"
                      ? "bg-muted text-muted-foreground italic"
                      : "bg-muted text-card-foreground"
                }`}
              >
                <div className="whitespace-pre-wrap text-sm md:text-base leading-relaxed text-pretty">
                  {message.text}
                </div>
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </CardContent>

        <CardFooter className="p-4 md:p-6 border-t bg-card">
          <div className="flex w-full gap-2 md:gap-3">
            <Button
              variant="outline"
              size="icon"
              className="flex-shrink-0 bg-transparent hover:bg-primary/10 hover:text-primary hover:border-primary transition-smooth"
              title="إرسال صورة / Send image"
              onClick={handleImageUpload}
              disabled={isLoading}
            >
              <ImageIcon size={18} strokeWidth={1.5} />
            </Button>

            <Input
              value={input}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              placeholder="اكتب رسالتك... / Type your message..."
              disabled={isLoading}
              className="flex-1 h-11 rounded-xl focus-ring-cyan transition-smooth"
            />

            <Button
              onClick={sendMessage}
              disabled={isLoading || !input.trim()}
              size="icon"
              className="flex-shrink-0 h-11 w-11 transition-smooth hover:scale-105 active:scale-95"
            >
              <Send size={18} strokeWidth={1.5} />
            </Button>
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}
