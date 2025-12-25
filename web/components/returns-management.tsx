"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
    RotateCcw,
    Search,
    Filter,
    MoreVertical,
    Eye,
    Download,
    AlertOctagon,
    CheckCircle2,
    Clock
} from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { fetchFromAPI } from "@/lib/db/client"
import { toast } from "sonner"
import CreateReturn from "./create-return"

export default function ReturnsManagement() {
    const [searchTerm, setSearchTerm] = useState("")
    const [selectedStatus, setSelectedStatus] = useState("all")
    const [returns, setReturns] = useState<any[]>([])
    const [loading, setLoading] = useState(true)

    const loadReturns = async () => {
        try {
            setLoading(true)
            const data = await fetchFromAPI('/returns')
            if (Array.isArray(data)) {
                setReturns(data)
            }
        } catch (e) {
            console.error("Failed to load returns", e)
            toast.error("فشل تحميل المرتجعات")
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        loadReturns()
    }, [])

    const getStatusColor = (status: string) => {
        switch (status) {
            case "APPROVED":
            case "COMPLETED":
            case "موافق عليه":
            case "مكتمل":
                return "bg-green-100 text-green-800"
            case "PENDING":
            case "معلق":
                return "bg-yellow-100 text-yellow-800"
            case "REJECTED":
            case "مرفوض":
                return "bg-red-100 text-red-800"
            default:
                return "bg-gray-100 text-gray-800"
        }
    }

    const filteredReturns = returns.filter((ret) => {
        const matchesSearch =
            ret.return_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (ret.customer_name && ret.customer_name.toLowerCase().includes(searchTerm.toLowerCase()))

        const matchesStatus = selectedStatus === "all" || ret.status === selectedStatus

        return matchesSearch && matchesStatus
    })

    // Stats
    const totalReturns = returns.reduce((sum, r) => sum + r.total_amount, 0)
    const pendingReturns = returns.filter(r => r.status === "PENDING" || r.status === "معلق").length

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">إدارة المرتجعات</h1>
                    <p className="text-gray-600">معالجة وتتبع مرتجعات المبيعات والمشتريات</p>
                </div>
                <CreateReturn onSaved={loadReturns} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-orange-800">إجمالي المرتجعات</CardTitle>
                        <RotateCcw className="h-4 w-4 text-orange-600" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-orange-900">{totalReturns.toLocaleString()} ر.س</div>
                        <p className="text-xs text-orange-600 mt-1">القيمة الإجمالية</p>
                    </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-blue-800">طلبات معلقة</CardTitle>
                        <Clock className="h-4 w-4 text-blue-600" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-blue-900">{pendingReturns}</div>
                        <p className="text-xs text-blue-600 mt-1">بانتظار الموافقة</p>
                    </CardContent>
                </Card>
            </div>

            <div className="flex flex-col md:flex-row gap-4">
                <div className="relative flex-1">
                    <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <Input
                        placeholder="البحث برقم المرتجع أو اسم العميل..."
                        className="pr-10"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                    <SelectTrigger className="w-full md:w-48">
                        <SelectValue placeholder="حالة المرتجع" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">جميع الحالات</SelectItem>
                        <SelectItem value="PENDING">معلق</SelectItem>
                        <SelectItem value="APPROVED">موافق عليه</SelectItem>
                        <SelectItem value="REJECTED">مرفوض</SelectItem>
                        <SelectItem value="COMPLETED">مكتمل</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>سجل المرتجعات</CardTitle>
                    <CardDescription>عرض جميع عمليات الإرجاع</CardDescription>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="text-center py-8 text-gray-500">جاري التحميل...</div>
                    ) : filteredReturns.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">لا توجد مرتجعات</div>
                    ) : (
                        <div className="space-y-4">
                            {filteredReturns.map((ret) => (
                                <div key={ret.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                                    <div className="flex items-center gap-4">
                                        <div className="h-10 w-10 bg-orange-100 rounded-full flex items-center justify-center">
                                            <RotateCcw className="h-5 w-5 text-orange-600" />
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <h3 className="font-semibold text-gray-900">
                                                    {ret.return_number}
                                                </h3>
                                                <Badge className={getStatusColor(ret.status)} variant="secondary">
                                                    {ret.status === "PENDING" ? "معلق" :
                                                        ret.status === "APPROVED" ? "موافق عليه" :
                                                            ret.status === "COMPLETED" ? "مكتمل" : ret.status}
                                                </Badge>
                                            </div>
                                            <div className="flex items-center gap-3 text-sm text-gray-500 mt-1">
                                                <span>{ret.customer_name || ret.supplier_name || "عميل عام"}</span>
                                                <span>•</span>
                                                <span>{ret.return_date}</span>
                                                <span>•</span>
                                                <span className="text-xs bg-gray-100 px-2 py-0.5 rounded text-gray-600">
                                                    {ret.return_type === "SALE_RETURN" ? "مرتجع مبيعات" : "مرتجع مشتريات"}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="text-left">
                                        <div className="font-bold text-gray-900">{ret.total_amount.toLocaleString()} ر.س</div>
                                    </div>

                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <Button variant="ghost" size="icon">
                                                <MoreVertical className="h-4 w-4" />
                                            </Button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="end">
                                            <DropdownMenuItem>
                                                <Eye className="h-4 w-4 ml-2" />
                                                عرض التفاصيل
                                            </DropdownMenuItem>
                                            <DropdownMenuItem>
                                                <CheckCircle2 className="h-4 w-4 ml-2" />
                                                موافقة / رفض
                                            </DropdownMenuItem>
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
