"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Globe, MapPin, Target, Truck, CreditCard, BarChart3, Package, ArrowRight, Zap } from "lucide-react"

export default function MarketExpansionDashboard() {
  const [selectedMarket, setSelectedMarket] = useState("algeria")

  const marketData = {
    algeria: {
      name: "السوق الجزائري",
      regions: ["قسنطينة", "الجزائر العاصمة", "وهران", "عنابة"],
      potential: 85,
      competition: "متوسط",
      regulations: "مألوف",
    },
    maghreb: {
      name: "دول المغرب العربي",
      regions: ["تونس", "المغرب", "ليبيا"],
      potential: 92,
      competition: "عالي",
      regulations: "متشابه",
    },
    gulf: {
      name: "دول الخليج العربي",
      regions: ["السعودية", "الإمارات", "قطر", "الكويت"],
      potential: 96,
      competition: "عالي جداً",
      regulations: "صارم",
    },
  }

  const expansionMetrics = [
    {
      title: "جاهزية التوسع",
      value: 78,
      target: 85,
      color: "bg-blue-500",
      description: "النظام جاهز للتوسع الإقليمي",
    },
    {
      title: "قوة العلامة التجارية",
      value: 65,
      target: 80,
      color: "bg-green-500",
      description: "Standard تكتسب قوة في السوق المحلي",
    },
    {
      title: "كفاءة سلسلة التوريد",
      value: 82,
      target: 90,
      color: "bg-purple-500",
      description: "شبكة موردين قوية ومتنوعة",
    },
    {
      title: "الاستعداد التقني",
      value: 94,
      target: 95,
      color: "bg-orange-500",
      description: "منصة تقنية متطورة وقابلة للتوسع",
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Globe className="h-6 w-6 text-blue-600" />
            خطة التوسع الاستراتيجي
          </h1>
          <p className="text-gray-600">من زيغود يوسف، قسنطينة إلى الأسواق الإقليمية والعالمية</p>
        </div>
        <Badge className="bg-gradient-to-r from-blue-600 to-green-600 text-white px-4 py-2">
          <Zap className="h-4 w-4 ml-1" />
          جاهز للنمو
        </Badge>
      </div>

      {/* مؤشرات جاهزية التوسع */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {expansionMetrics.map((metric, index) => (
          <Card key={index} className="hover:shadow-lg transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">{metric.title}</h3>
                <div className={`w-3 h-3 rounded-full ${metric.color}`}></div>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span>الحالي: {metric.value}%</span>
                  <span>الهدف: {metric.target}%</span>
                </div>
                <Progress value={metric.value} className="h-3" />
                <p className="text-xs text-gray-600">{metric.description}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* خريطة الأسواق المستهدفة */}
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="h-5 w-5 text-green-600" />
            الأسواق المستهدفة للتوسع
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {Object.entries(marketData).map(([key, market]) => (
              <div
                key={key}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  selectedMarket === key ? "border-blue-500 bg-blue-50" : "border-gray-200 hover:border-gray-300"
                }`}
                onClick={() => setSelectedMarket(key)}
              >
                <h3 className="font-semibold text-lg mb-3">{market.name}</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">إمكانات السوق:</span>
                    <span className="font-semibold text-green-600">{market.potential}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">مستوى المنافسة:</span>
                    <span className="font-semibold">{market.competition}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">التنظيمات:</span>
                    <span className="font-semibold">{market.regulations}</span>
                  </div>
                  <div className="mt-3">
                    <p className="text-xs text-gray-500 mb-1">المناطق الرئيسية:</p>
                    <div className="flex flex-wrap gap-1">
                      {market.regions.map((region, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs">
                          {region}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* استراتيجية التوسع حسب الفئات */}
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-purple-600" />
            استراتيجية التوسع حسب فئات المنتجات
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                category: "المواد الغذائية",
                priority: "عالية",
                readiness: 85,
                strategy: "التركيز على المنتجات المحلية والتقليدية",
                challenges: ["شهادات الجودة", "سلسلة التبريد"],
                opportunities: ["الطلب المتزايد", "المنتجات الأصيلة"],
              },
              {
                category: "مستحضرات التجميل",
                priority: "متوسطة",
                readiness: 72,
                strategy: "شراكات مع العلامات التجارية العالمية",
                challenges: ["التنظيمات الصحية", "المنافسة الشديدة"],
                opportunities: ["نمو السوق", "الوعي بالجمال"],
              },
              {
                category: "الإلكترونيات",
                priority: "عالية",
                readiness: 78,
                strategy: "التجارة الإلكترونية والتوزيع الذكي",
                challenges: ["التقلبات التقنية", "خدمة ما بعد البيع"],
                opportunities: ["التحول الرقمي", "الطلب المتزايد"],
              },
            ].map((item, index) => (
              <div key={index} className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold">{item.category}</h3>
                  <Badge
                    className={item.priority === "عالية" ? "bg-red-100 text-red-800" : "bg-orange-100 text-orange-800"}
                  >
                    {item.priority}
                  </Badge>
                </div>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>الجاهزية:</span>
                      <span className="font-semibold">{item.readiness}%</span>
                    </div>
                    <Progress value={item.readiness} className="h-2" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-1">الاستراتيجية:</p>
                    <p className="text-xs text-gray-600">{item.strategy}</p>
                  </div>
                  <div className="grid grid-cols-1 gap-2">
                    <div>
                      <p className="text-xs font-medium text-red-700">التحديات:</p>
                      <ul className="text-xs text-red-600">
                        {item.challenges.map((challenge, idx) => (
                          <li key={idx}>• {challenge}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-green-700">الفرص:</p>
                      <ul className="text-xs text-green-600">
                        {item.opportunities.map((opportunity, idx) => (
                          <li key={idx}>• {opportunity}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* خطة التكامل التقني */}
      <Card className="shadow-lg bg-gradient-to-r from-blue-50 to-purple-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-blue-600" />
            خطة التكامل التقني للتوسع
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              {
                title: "بوابات الدفع",
                icon: CreditCard,
                status: "قيد التطوير",
                progress: 60,
                description: "تكامل مع بوابات الدفع المحلية والدولية",
              },
              {
                title: "خدمات الشحن",
                icon: Truck,
                status: "مخطط",
                progress: 30,
                description: "شراكات مع شركات الشحن الإقليمية",
              },
              {
                title: "أنظمة المحاسبة",
                icon: BarChart3,
                status: "جاهز",
                progress: 90,
                description: "تكامل مع أنظمة المحاسبة المعتمدة",
              },
              {
                title: "نقاط البيع",
                icon: Package,
                status: "قيد التطوير",
                progress: 45,
                description: "أنظمة POS متطورة للمتاجر الفيزيائية",
              },
            ].map((integration, index) => (
              <div key={index} className="p-4 bg-white rounded-lg border">
                <div className="flex items-center gap-3 mb-3">
                  <div className="bg-blue-100 p-2 rounded-lg">
                    <integration.icon className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm">{integration.title}</h3>
                    <Badge
                      variant="outline"
                      className={`text-xs ${
                        integration.status === "جاهز"
                          ? "text-green-700 border-green-300"
                          : integration.status === "قيد التطوير"
                            ? "text-blue-700 border-blue-300"
                            : "text-orange-700 border-orange-300"
                      }`}
                    >
                      {integration.status}
                    </Badge>
                  </div>
                </div>
                <Progress value={integration.progress} className="h-2 mb-2" />
                <p className="text-xs text-gray-600">{integration.description}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* الخطوات التالية */}
      <Card className="shadow-lg border-2 border-green-200 bg-green-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-green-800">
            <ArrowRight className="h-5 w-5" />
            الخطوات التالية للتوسع
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-green-800 mb-3">المرحلة الأولى (3-6 أشهر)</h3>
              <ul className="space-y-2 text-sm text-green-700">
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  تعزيز الحضور في قسنطينة والمناطق المجاورة
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  تطوير شراكات مع موردين إضافيين
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  إطلاق متجر إلكتروني متكامل
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  تحسين سلسلة التوريد والخدمات اللوجستية
                </li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-green-800 mb-3">المرحلة الثانية (6-12 شهر)</h3>
              <ul className="space-y-2 text-sm text-green-700">
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  التوسع إلى المدن الجزائرية الكبرى
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  تطوير خطوط منتجات خاصة بالعلامة التجارية
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  إقامة شراكات إقليمية في المغرب العربي
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  تطوير تطبيق محمول متقدم
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
