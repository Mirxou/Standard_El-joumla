"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Brain, TrendingUp, AlertCircle, Lightbulb, RefreshCw, Loader2 } from 'lucide-react'
import { getAIRecommendations } from "@/lib/actions/ai"

export default function AIInsights() {
  const [recommendations, setRecommendations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const loadRecommendations = async () => {
    setLoading(true)
    try {
      const result = await getAIRecommendations()
      if (result.success) {
        setRecommendations(result.data || [])
      }
    } catch (error) {
      console.error('[v0] Error loading AI recommendations:', error)
    }
    setLoading(false)
  }

  useEffect(() => {
    loadRecommendations()
  }, [])

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'medium':
        return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'reorder':
        return <TrendingUp className="h-5 w-5" />
      case 'alert':
        return <AlertCircle className="h-5 w-5" />
      default:
        return <Lightbulb className="h-5 w-5" />
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-br from-purple-500 to-pink-500 p-3 rounded-xl">
            <Brain className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">رؤى الذكاء الاصطناعي</h2>
            <p className="text-sm text-gray-600">توصيات ذكية مبنية على تحليل البيانات</p>
          </div>
        </div>
        <Button onClick={loadRecommendations} disabled={loading} className="gap-2">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          تحديث
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
        </div>
      ) : recommendations.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center h-64 text-center">
            <Brain className="h-16 w-16 text-gray-300 mb-4" />
            <p className="text-gray-600">لا توجد توصيات حالياً</p>
            <p className="text-sm text-gray-500 mt-2">سيتم تحليل بياناتك وتقديم توصيات قريباً</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {recommendations.map((rec, index) => (
            <Card key={rec.id || index} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg ${getPriorityColor(rec.priority)}`}>
                      {getCategoryIcon(rec.category)}
                    </div>
                    <div>
                      <CardTitle className="text-lg">{rec.title}</CardTitle>
                      <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
                    </div>
                  </div>
                  <Badge className={getPriorityColor(rec.priority)}>
                    {rec.priority === 'high' ? 'عاجل' : rec.priority === 'medium' ? 'متوسط' : 'منخفض'}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <p className="text-sm font-semibold text-blue-900 mb-1">الإجراء المقترح:</p>
                    <p className="text-sm text-blue-800">{rec.action}</p>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                    <p className="text-sm font-semibold text-green-900 mb-1">التأثير المتوقع:</p>
                    <p className="text-sm text-green-800">{rec.impact}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
