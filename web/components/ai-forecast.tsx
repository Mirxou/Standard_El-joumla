"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Brain } from "lucide-react"

export default function AIForecast() {
    return (
        <div className="space-y-6">
            <div className="flex items-center gap-3">
                <div className="bg-purple-100 p-2 rounded-lg">
                    <Brain className="h-6 w-6 text-purple-700" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">التنبؤ الذكي (AI Forecast)</h1>
                    <p className="text-gray-600">تحليل الاتجاهات المستقبلية باستخدام الذكاء الاصطناعي</p>
                </div>
            </div>

            <Card>
                <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                    <Brain className="h-16 w-16 text-gray-200 mb-4" />
                    <h3 className="text-lg font-medium text-gray-900">الميزة قيد التطوير</h3>
                    <p className="text-gray-500 max-w-md mt-2">
                        نحن نعمل على دمج خوارزميات الذكاء الاصطناعي للتنبؤ بالمبيعات والمخزون. ستكون هذه الميزة متاحة في التحديث القادم.
                    </p>
                </CardContent>
            </Card>
        </div>
    )
}
