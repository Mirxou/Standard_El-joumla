"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
    ShoppingCart,
    Plus,
    Search,
    Filter,
    Download,
    Calendar,
    DollarSign,
    TrendingUp,
    Clock,
    MoreVertical,
    Eye,
    Trash2,
    FileText,
    User,
    Truck
} from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { fetchFromAPI } from "@/lib/db/client"
import { toast } from "sonner"
import CreatePurchase from "./create-purchase"

export default function PurchasesManagement() {
    const [searchTerm, setSearchTerm] = useState("")
    const [selectedStatus, setSelectedStatus] = useState("all")
    const [purchases, setPurchases] = useState<any[]>([])
    const [loading, setLoading] = useState(true)

    const loadPurchases = async () => {
        try {
            setLoading(true)
            const data = await fetchFromAPI('/purchases')
            if (Array.isArray(data)) {
                setPurchases(data)
            }
        } catch (e) {
            console.error("Failed to load purchases", e)
            toast.error("فشل تحميل المشتريات")
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        loadPurchases()
    }, [])

    const getStatusColor = (status: string) => {
        switch (status) {
            case "مستلمة":
                return "bg-green-100 text-green-800"
            case "معلقة":
                return "bg-yellow-100 text-yellow-800"
            case "جزئية":
                return "bg-blue-100 text-blue-800"
            case "ملغية":
                return "bg-red-100 text-red-800"
            default:
                return "bg-gray-100 text-gray-800"
        }
    }

    const getPaymentStatusColor = (status: string) => {
        switch (status) {
            case "مدفوعة": return "bg-green-100 text-green-800"
            case "غير مدفوعة": return "bg-red-100 text-red-800"
            case "مدفوعة جزئياً": return "bg-orange-100 text-orange-800"
            default: return "bg-gray-100 text-gray-800"
        }
    }

    const filteredPurchases = purchases.filter((purchase) => {
        const matchesSearch =
            purchase.invoice_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (purchase.supplier_name && purchase.supplier_name.toLowerCase().includes(searchTerm.toLowerCase()))

        const matchesStatus = selectedStatus === "all" || purchase.status === selectedStatus

        return matchesSearch && matchesStatus
    })

    // Calculate statistics
    const totalPurchases = purchases.reduce((sum, p) => sum + p.total_amount, 0)
    const pendingPurchases = purchases.filter(p => p.status === "معلقة").length
    const overduePurchases = purchases.filter(p => p.payment_status === "متأخرة").length

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">إدارة المشتريات</h1>
                    <p className="text-gray-600">تتبع أوامر الشراء والموردين والمدفوعات</p>
                </div>
                <CreatePurchase onSaved={loadPurchases} />
            </div>

            {/* Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-blue-800">إجمالي المشتريات (شهر)</CardTitle>
                        <DollarSign className="h-4 w-4 text-blue-600" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-blue-900">{totalPurchases.toLocaleString()} ر.س</div>
                        <p className="text-xs text-blue-600 mt-1">+12% من الشهر الماضي</p>
                    </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-yellow-800">أوامر معلقة</CardTitle>
                        <Clock className="h-4 w-4 text-yellow-600" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-yellow-900">{pendingPurchases}</div>
                        <p className="text-xs text-yellow-600 mt-1">بحاجة إلى متابعة</p>
                    </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium text-red-800">مدفوعات متأخرة</CardTitle>
                        <AlertTriangleIcon className="h-4 w-4 text-red-600" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-red-900">{overduePurchases}</div>
                        <p className="text-xs text-red-600 mt-1">تتطلب إجراء فوري</p>
                    </CardContent>
                </Card>
            </div>

            {/* Filters */}
            <div className="flex flex-col md:flex-row gap-4">
                <div className="relative flex-1">
                    <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <Input
                        placeholder="البحث برقم الفاتورة أو اسم المورد..."
                        className="pr-10"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                    <SelectTrigger className="w-full md:w-48">
                        <SelectValue placeholder="حالة الطلب" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">جميع الحالات</SelectItem>
                        <SelectItem value="معلقة">معلقة</SelectItem>
                        <SelectItem value="مستلمة">مستلمة</SelectItem>
                        <SelectItem value="ملغية">ملغية</SelectItem>
                    </SelectContent>
                </Select>
                <Button variant="outline">
                    <Filter className="h-4 w-4 ml-2" />
                    تصفية متقدمة
                </Button>
            </div>

            {/* Purchases List */}
            <Card>
                <CardHeader>
                    <CardTitle>سجل المشتريات</CardTitle>
                    <CardDescription>عرض تفصيلي لجميع عمليات الشراء</CardDescription>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="text-center py-8 text-gray-500">جاري التحميل...</div>
                    ) : filteredPurchases.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">لا توجد مشتريات مطابقة</div>
                    ) : (
                        <div className="space-y-4">
                            {filteredPurchases.map((purchase) => (
                                <div key={purchase.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                                    <div className="flex items-center gap-4">
                                        <div className="h-10 w-10 bg-purple-100 rounded-full flex items-center justify-center">
                                            <Truck className="h-5 w-5 text-purple-600" />
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <h3 className="font-semibold text-gray-900">
                                                    فاتورة #{purchase.invoice_number}
                                                </h3>
                                                <Badge className={getStatusColor(purchase.status)} variant="secondary">
                                                    {purchase.status}
                                                </Badge>
                                            </div>
                                            <div className="flex items-center gap-3 text-sm text-gray-500 mt-1">
                                                <div className="flex items-center gap-1">
                                                    <User className="h-3 w-3" />
                                                    {purchase.supplier_name || "مورد غير معروف"}
                                                </div>
                                                <div className="flex items-center gap-1">
                                                    <Calendar className="h-3 w-3" />
                                                    {purchase.purchase_date}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="text-left">
                                        <div className="font-bold text-gray-900">{purchase.total_amount.toLocaleString()} ر.س</div>
                                        <div className="flex items-center gap-2 justify-end mt-1">
                                            <Badge className={getPaymentStatusColor(purchase.payment_status)} variant="outline">
                                                {purchase.payment_status}
                                            </Badge>
                                        </div>
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
                                            <DropdownMenuItem className="text-blue-600">
                                                <Download className="h-4 w-4 ml-2" />
                                                تحميل الفاتورة
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

function AlertTriangleIcon({ className }: { className?: string }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
        >
            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
            <path d="M12 9v4" />
            <path d="M12 17h.01" />
        </svg>
    )
}
