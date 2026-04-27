"use client"

import { Component, ReactNode } from "react"
import { AlertTriangle, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { render } from "react-dom"

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: React.ErrorInfo | null
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Error caught by boundary:", error, errorInfo)
    this.setState({
      error,
      errorInfo,
    })
  }

  render() {

    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#0f172a] flex items-center justify-center p-4 font-cairo" dir="rtl">
          <div className="absolute inset-0 z-0 overflow-hidden">
            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-red-500/10 rounded-full blur-[120px] animate-pulse" />
            <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-purple-500/10 rounded-full blur-[120px]" />
          </div>

          <div className="relative z-10 glass-panel p-8 rounded-3xl max-w-md w-full text-center border-red-500/20 shadow-2xl shadow-red-500/10">
            <div className="w-20 h-20 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-6 animate-bounce">
              <AlertTriangle className="h-10 w-10 text-red-500" />
            </div>

            <h2 className="text-2xl font-bold text-white mb-2">عذراً، حدث خطأ غير متوقع</h2>
            <p className="text-gray-400 mb-6 leading-relaxed">
              واجهنا مشكلة في معالجة طلبك. لقد تم تسجيل الخطأ وسنعمل على حله قريباً.
            </p>

            {this.state.error && (
              <div className="p-4 bg-black/40 rounded-xl border border-red-500/20 text-right mb-6 overflow-hidden">
                <p className="text-xs font-mono text-red-400 break-all">
                  {this.state.error.toString()}
                </p>
              </div>
            )}

            <div className="flex gap-3">
              <Button
                onClick={() => window.location.reload()}
                className="flex-1 bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-500 hover:to-pink-500 text-white rounded-xl h-12 shadow-lg shadow-red-500/25"
              >
                <RefreshCw className="h-4 w-4 ml-2" />
                إعادة المحاولة
              </Button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
