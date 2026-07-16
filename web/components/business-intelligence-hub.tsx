"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  Brain,
  TrendingUp,
  Target,
  Lightbulb,
  AlertCircle,
  CheckCircle,
  Clock,
  Package,
  BarChart3,
  Zap,
} from "lucide-react"

export default function BusinessIntelligenceHub() {
  const [selectedInsight, setSelectedInsight] = useState("market-opportunities")

  const aiInsights = {
    "market-opportunities": {
      title: "فرص السوق الذكية",
      priority: "عالية",
      confidence: 92,
      insights: [
        {
          type: "opportunity",
          title: "نمو قطاع مستحضرات التجميل",
          description: "زيادة 35% في الطلب على منتجات العناية الطبيعية في المنطقة",
          action: "توسيع مجموعة المنتجات الطبيعية",
          impact: "متوقع زيادة الإيرادات بـ 25%",
        },
        {
          type: "trend",
          title: "التجارة الإلكترونية في الجزائر",
          description: "نمو 45% في المبيعات الإلكترونية خلال العام الماضي",
          action: "تطوير منصة التجارة الإلكترونية",
          impact: "وصول لـ 50,000 عميل جديد محتمل",
        },
      ],
    },
    "operational-optimization": {
      title: "تحسين العمليات",
      priority: "متوسطة",
      confidence: 88,
      insights: [
        {
          type: "efficiency",
          title: "تحسين إدارة المخزون",
          description: "يمكن تقليل تكاليف التخزين بـ 18% من خلال تحسين دورة المخزون",
          action: "تطبيق نظام Just-in-Time للمنتجات سريعة الحركة",
          impact: "توفير 45,000 ر.س شهرياً",
        },
        {
          type: "automation",
          title: "أتمتة عمليات الطلب",
          description: "أتمتة 70% من عمليات معالجة الطلبات لتوفير الوقت والتكلفة",
          action: "تطوير نظام معالجة الطلبات التلقائي",
          impact: "تقليل وقت المعالجة بـ 60%",
        },
      ],
    },
    "risk-management": {
      title: "إدارة المخاطر",
      priority: "حرجة",
      confidence: 85,
      insights: [
        {
          type: "risk",
          title: "مخاطر سلسلة التوريد",
          description: "اعتماد 60% على مورد واحد في فئة الإلكترونيات",
          action: "تنويع قاعدة الموردين وإقامة شراكات احتياطية",
          impact: "تقليل مخاطر انقطاع التوريد بـ 80%",
        },
        {
          type: "compliance",
          title: "متطلبات الامتثال",
          description: "تغييرات قادمة في لوائح سلامة الأغذية",
          action: "تحديث أنظمة تتبع الجودة والامتثال",
          impact: "ضمان الامتثال الكامل وتجنب الغرامات",
        },
      ],
    },
  }

  const performanceMetrics = [
    {
      title: "كفاءة العمليات",
      current: 78,
      target: 85,
      trend: "up",
      description: "تحسن مستمر في كفاءة العمليات التشغيلية",
    },
    {
      title: "رضا العملاء",
      current: 4.6,
      target: 4.8,
      trend: "up",
      description: "تقييمات إيجابية متزايدة من العملاء",
      isRating: true,
    },
    {
      title: "نمو الإيرادات",
      current: 23,
      target: 30,
      trend: "up",
      description: "نمو قوي في الإيرادات الشهرية",
      suffix: "%",
    },
    {
      title: "هامش الربح",
      current: 32.4,
      target: 35,
      trend: "stable",
      description: "هامش ربح صحي مع إمكانية للتحسين",
      suffix: "%",
    },
  ]

  const currentInsight = aiInsights[selectedInsight as keyof typeof aiInsights]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Brain className="h-6 w-6 text-purple-600" />
            مركز الذكاء التجاري
          </h1>
          <p className="text-gray-600">رؤى ذكية مدعومة بالذكاء الاصطناعي لاتخاذ قرارات استراتيجية</p>
        </div>
        <Badge className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2">
          <Zap className="h-4 w-4 ml-1" />
          مدعوم بالذكاء الاصطناعي
        </Badge>
      </div>

      {/* مؤشرات الأداء الذكية */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {performanceMetrics.map((metric, index) => (
          <Card key={index} className="hover:shadow-lg transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">{metric.title}</h3>
                <div className="flex items-center gap-1">
                  {metric.trend === "up" ? (
                    <TrendingUp className="h-4 w-4 text-green-500" />
                  ) : metric.trend === "down" ? (
                    <TrendingUp className="h-4 w-4 text-red-500 rotate-180" />
                  ) : (
                    <div className="w-4 h-4 bg-gray-400 rounded-full"></div>
                  )}
                </div>
              </div>
              <div className="space-y-3">
                <div className="text-2xl font-bold text-gray-900">
                  {metric.isRating ? metric.current : metric.current}
                  {metric.suffix || ""}
                  {metric.isRating && "/5"}
                </div>
                <div className="flex justify-between text-sm text-gray-600">
                  <span>
                    الهدف: {metric.target}
                    {metric.suffix || ""}
                    {metric.isRating && "/5"}
                  </span>
                </div>
                <Progress
                  value={metric.isRating ? (metric.current / 5) * 100 : (metric.current / metric.target) * 100}
                  className="h-2"
                />
                <p className="text-xs text-gray-600">{metric.description}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* فئات الرؤى الذكية */}
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-yellow-600" />
            الرؤى الاستراتيجية المدعومة بالذكاء الاصطناعي
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2 mb-6">
            {Object.entries(aiInsights).map(([key, insight]) => (
              <Button
                key={key}
                variant={selectedInsight === key ? "default" : "outline"}
                onClick={() => setSelectedInsight(key)}
                className={`${
                  selectedInsight === key
                    ? "bg-purple-600 hover:bg-purple-700"
                    : "hover:bg-purple-50 hover:border-purple-300"
                }`}
              >
                {insight.title}
                <Badge
                  className={`mr-2 ${
                    insight.priority === "عالية"
                      ? "bg-red-100 text-red-800"
                      : insight.priority === "حرجة"
                        ? "bg-red-200 text-red-900"
                        : "bg-orange-100 text-orange-800"
                  }`}
                >
                  {insight.priority}
                </Badge>
              </Button>
            ))}
          </div>

          <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-900">{currentInsight.title}</h3>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">مستوى الثقة:</span>
                <Badge className="bg-green-100 text-green-800">{currentInsight.confidence}%</Badge>
              </div>
            </div>

            <div className="grid gap-4">
              {currentInsight.insights.map((insight, index) => (
                <div key={index} className="bg-white rounded-lg p-4 border border-gray-200">
                  <div className="flex items-start gap-3">
                    <div
                      className={`p-2 rounded-lg ${
                        insight.type === "opportunity"
                          ? "bg-green-100"
                          : insight.type === "risk"
                            ? "bg-red-100"
                            : insight.type === "trend"
                              ? "bg-blue-100"
                              : "bg-purple-100"
                      }`}
                    >
                      {insight.type === "opportunity" ? (
                        <Target className="h-5 w-5 text-green-600" />
                      ) : insight.type === "risk" ? (
                        <AlertCircle className="h-5 w-5 text-red-600" />
                      ) : insight.type === "trend" ? (
                        <TrendingUp className="h-5 w-5 text-blue-600" />
                      ) : (
                        <BarChart3 className="h-5 w-5 text-purple-600" />
                      )}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 mb-2">{insight.title}</h4>
                      <p className="text-gray-700 mb-3">{insight.description}</p>
                      <div className="bg-gray-50 rounded-lg p-3 mb-3">
                        <p className="text-sm font-medium text-gray-800 mb-1">الإجراء المقترح:</p>
                        <p className="text-sm text-gray-700">{insight.action}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        <span className="text-sm font-medium text-green-700">التأثير المتوقع:</span>
                        <span className="text-sm text-gray-700">{insight.impact}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* خطة العمل الذكية */}
      <Card className="shadow-lg bg-gradient-to-r from-green-50 to-blue-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-green-800">
            <Target className="h-5 w-5" />
            خطة العمل الذكية - الأولويات القادمة
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg p-4 border-2 border-green-200">
              <div className="flex items-center gap-2 mb-3">
                <Clock className="h-5 w-5 text-green-600" />
                <h3 className="font-semibold text-green-800">الأسبوع القادم</h3>
              </div>
              <ul className="space-y-2 text-sm">
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  تحليل أداء الموردين الحاليين
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  مراجعة مستويات المخزون الحرجة
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  تحديث استراتيجية التسعير
                </li>
              </ul>
            </div>

            <div className="bg-white rounded-lg p-4 border-2 border-blue-200">
              <div className="flex items-center gap-2 mb-3">
                <Package className="h-5 w-5 text-blue-600" />
                <h3 className="font-semibold text-blue-800">الشهر القادم</h3>
              </div>
              <ul className="space-y-2 text-sm">
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  إطلاق خط منتجات التجميل الطبيعية
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  تطوير شراكات جديدة مع الموردين
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  تحسين نظام إدارة المخزون
                </li>
              </ul>
            </div>

            <div className="bg-white rounded-lg p-4 border-2 border-purple-200">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="h-5 w-5 text-purple-600" />
                <h3 className="font-semibold text-purple-800">الربع القادم</h3>
              </div>
              <ul className="space-y-2 text-sm">
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                  التوسع إلى مدن جديدة في الجزائر
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                  إطلاق منصة التجارة الإلكترونية
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                  تطوير تطبيق الهاتف المحمول
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
