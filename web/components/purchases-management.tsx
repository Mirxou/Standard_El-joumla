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
    Truck,
    CheckCircle,
    XCircle,
    RefreshCw
} from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { apiClient } from "@/lib/api/client"
import { API_CONFIG } from "@/lib/config/api"
import { toast } from "sonner"
import CreatePurchase from "./create-purchase"

export default function PurchasesManagement() {
    const [searchTerm, setSearchTerm] = useState("")
    const [selectedStatus, setSelectedStatus] = useState("all")
    const [purchases, setPurchases] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [detailsDialogOpen, setDetailsDialogOpen] = useState(false)
    const [selectedPurchase, setSelectedPurchase] = useState<any | null>(null)
    const [approvalDialogOpen, setApprovalDialogOpen] = useState(false)
    const [purchaseToApprove, setPurchaseToApprove] = useState<any | null>(null)

    const loadPurchases = async () => {
        try {
            setLoading(true)
            const data = await apiClient.get<any>(API_CONFIG.ENDPOINTS.PURCHASES)
            const purchasesArray = Array.isArray(data) ? data : (data as any)?.purchases || (data as any)?.items || []
            setPurchases(purchasesArray)
        } catch (error: any) {
            console.error("Failed to load purchases", error)
            toast.error("فشل تحميل المشتريات")
            setPurchases([])
        } finally {
            setLoading(false)
        }
    }

    const loadPurchaseDetails = async (purchaseId: number) => {
        try {
            const purchase = await apiClient.get<any>(`/api/v1/purchases/${purchaseId}`)
            setSelectedPurchase(purchase)
            setDetailsDialogOpen(true)
        } catch (error: any) {
            console.error("Failed to load purchase details", error)
            toast.error("فشل تحميل تفاصيل المشتريات")
        }
    }

    const handleApprovePurchase = async (purchase: any) => {
        setPurchaseToApprove(purchase)
        setApprovalDialogOpen(true)
    }

    const confirmApprovePurchase = async () => {
        if (!purchaseToApprove) return
        
        try {
            await apiClient.put(`/api/v1/purchases/${purchaseToApprove.id}`, {
                status: 'received',
                payment_status: 'paid'
            })
            toast.success("تم الموافقة على المشتريات بنجاح")
            setApprovalDialogOpen(false)
            setPurchaseToApprove(null)
            await loadPurchases()
        } catch (error: any) {
            console.error("Failed to approve purchase", error)
            toast.error("فشل الموافقة على المشتريات")
        }
    }

    const handleUpdateStatus = async (purchaseId: number, newStatus: string) => {
        try {
            await apiClient.put(`/api/v1/purchases/${purchaseId}`, { status: newStatus })
            toast.success("تم تحديث حالة المشتريات")
            await loadPurchases()
        } catch (error: any) {
            console.error("Failed to update purchase status", error)
            toast.error("فشل تحديث حالة المشتريات")
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
                <Button variant="outline" onClick={loadPurchases}>
                    <RefreshCw className="h-4 w-4 ml-2" />
                    تحديث
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
                                            <DropdownMenuItem onClick={() => loadPurchaseDetails(purchase.id)}>
                                                <Eye className="h-4 w-4 ml-2" />
                                                عرض التفاصيل
                                            </DropdownMenuItem>
                                            {purchase.status === "معلقة" && (
                                                <DropdownMenuItem onClick={() => handleApprovePurchase(purchase)}>
                                                    <CheckCircle className="h-4 w-4 ml-2" />
                                                    الموافقة
                                                </DropdownMenuItem>
                                            )}
                                            <DropdownMenuItem 
                                                onClick={() => handleUpdateStatus(purchase.id, "ملغية")}
                                                className="text-red-600"
                                            >
                                                <XCircle className="h-4 w-4 ml-2" />
                                                إلغاء
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

            {/* Dialog لعرض تفاصيل المشتريات */}
            <Dialog open={detailsDialogOpen} onOpenChange={setDetailsDialogOpen}>
                <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>تفاصيل المشتريات</DialogTitle>
                    </DialogHeader>
                    {selectedPurchase && (
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <p className="text-sm text-gray-500">رقم الفاتورة</p>
                                    <p className="font-semibold">{selectedPurchase.invoice_number}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500">التاريخ</p>
                                    <p className="font-semibold">{selectedPurchase.purchase_date}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500">المورد</p>
                                    <p className="font-semibold">{selectedPurchase.supplier_name || "غير محدد"}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500">الحالة</p>
                                    <Badge className={getStatusColor(selectedPurchase.status)}>
                                        {selectedPurchase.status}
                                    </Badge>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500">حالة الدفع</p>
                                    <Badge className={getPaymentStatusColor(selectedPurchase.payment_status)}>
                                        {selectedPurchase.payment_status}
                                    </Badge>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500">المجموع</p>
                                    <p className="font-semibold text-lg">{selectedPurchase.total_amount?.toLocaleString()} ر.س</p>
                                </div>
                            </div>
                            
                            {selectedPurchase.items && selectedPurchase.items.length > 0 && (
                                <div className="border-t pt-4">
                                    <h3 className="font-semibold mb-3">المنتجات</h3>
                                    <div className="space-y-2">
                                        {selectedPurchase.items.map((item: any, index: number) => (
                                            <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                                                <div>
                                                    <p className="font-medium">{item.product_name || `منتج #${item.product_id}`}</p>
                                                    <p className="text-sm text-gray-500">الكمية: {item.quantity} × {item.unit_cost} ر.س</p>
                                                </div>
                                                <p className="font-semibold">{(item.quantity * item.unit_cost).toLocaleString()} ر.س</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {selectedPurchase.notes && (
                                <div className="border-t pt-4">
                                    <p className="text-sm text-gray-500 mb-1">ملاحظات</p>
                                    <p className="bg-blue-50 p-3 rounded">{selectedPurchase.notes}</p>
                                </div>
                            )}
                        </div>
                    )}
                </DialogContent>
            </Dialog>

            {/* Dialog للموافقة على المشتريات */}
            <AlertDialog open={approvalDialogOpen} onOpenChange={setApprovalDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>الموافقة على المشتريات</AlertDialogTitle>
                        <AlertDialogDescription>
                            هل أنت متأكد من الموافقة على هذه المشتريات؟ سيتم تحديث حالة الطلب إلى "مستلمة" وحالة الدفع إلى "مدفوعة".
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel onClick={() => setPurchaseToApprove(null)}>إلغاء</AlertDialogCancel>
                        <AlertDialogAction onClick={confirmApprovePurchase} className="bg-green-600 hover:bg-green-700">
                            الموافقة
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
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
