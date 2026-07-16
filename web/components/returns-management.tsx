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
    Clock,
    XCircle,
    RefreshCw,
    DollarSign
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
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { apiClient } from "@/lib/api/client"
import { API_CONFIG } from "@/lib/config/api"
import { toast } from "sonner"
import CreateReturn from "./create-return"

export default function ReturnsManagement() {
    const [searchTerm, setSearchTerm] = useState("")
    const [selectedStatus, setSelectedStatus] = useState("all")
    const [returns, setReturns] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [detailsDialogOpen, setDetailsDialogOpen] = useState(false)
    const [selectedReturn, setSelectedReturn] = useState<any | null>(null)
    const [approvalDialogOpen, setApprovalDialogOpen] = useState(false)
    const [returnToApprove, setReturnToApprove] = useState<any | null>(null)
    const [refundDialogOpen, setRefundDialogOpen] = useState(false)
    const [returnToRefund, setReturnToRefund] = useState<any | null>(null)
    const [refundAmount, setRefundAmount] = useState(0)
    const [refundMethod, setRefundMethod] = useState("نقدي")

    const loadReturns = async () => {
        try {
            setLoading(true)
            const data = await apiClient.get<any>(API_CONFIG.ENDPOINTS.RETURNS)
            const returnsArray = Array.isArray(data) ? data : (data as any)?.items || (data as any)?.returns || []
            setReturns(returnsArray)
        } catch (error: any) {
            console.error("Failed to load returns", error)
            toast.error("فشل تحميل المرتجعات")
            setReturns([])
        } finally {
            setLoading(false)
        }
    }

    const loadReturnDetails = async (returnId: number) => {
        try {
            const returnData = await apiClient.get<any>(`${API_CONFIG.ENDPOINTS.RETURNS}/${returnId}`)
            setSelectedReturn(returnData)
            setDetailsDialogOpen(true)
        } catch (error: any) {
            console.error("Failed to load return details", error)
            toast.error("فشل تحميل تفاصيل المرتجع")
        }
    }

    const handleApproveReturn = async (returnItem: any, approved: boolean) => {
        setReturnToApprove({ ...returnItem, approved })
        setApprovalDialogOpen(true)
    }

    const confirmApproveReturn = async () => {
        if (!returnToApprove) return
        
        try {
            await apiClient.put(`${API_CONFIG.ENDPOINTS.RETURNS}/${returnToApprove.id}`, {
                status: returnToApprove.approved ? 'APPROVED' : 'REJECTED'
            })
            toast.success(returnToApprove.approved ? "تم الموافقة على المرتجع" : "تم رفض المرتجع")
            setApprovalDialogOpen(false)
            setReturnToApprove(null)
            await loadReturns()
        } catch (error: any) {
            console.error("Failed to approve/reject return", error)
            toast.error("فشل تحديث حالة المرتجع")
        }
    }

    const handleProcessRefund = (returnItem: any) => {
        setReturnToRefund(returnItem)
        setRefundAmount(returnItem.total_amount || 0)
        setRefundDialogOpen(true)
    }

    const confirmProcessRefund = async () => {
        if (!returnToRefund) return
        
        try {
            await apiClient.post(`${API_CONFIG.ENDPOINTS.RETURNS}/${returnToRefund.id}/refund`, {
                amount: refundAmount,
                method: refundMethod,
                notes: `استرداد لمرتجع ${returnToRefund.return_number}`
            })
            toast.success("تم معالجة الاسترداد بنجاح")
            setRefundDialogOpen(false)
            setReturnToRefund(null)
            await loadReturns()
        } catch (error: any) {
            console.error("Failed to process refund", error)
            toast.error("فشل معالجة الاسترداد")
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
                <div className="flex gap-2">
                    <Button variant="outline" onClick={loadReturns}>
                        <RefreshCw className="h-4 w-4 ml-2" />
                        تحديث
                    </Button>
                    <CreateReturn onSaved={loadReturns} />
                </div>
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
                                            <DropdownMenuItem onClick={() => loadReturnDetails(ret.id)}>
                                                <Eye className="h-4 w-4 ml-2" />
                                                عرض التفاصيل
                                            </DropdownMenuItem>
                                            {(ret.status === "PENDING" || ret.status === "معلق") && (
                                                <>
                                                    <DropdownMenuItem onClick={() => handleApproveReturn(ret, true)}>
                                                        <CheckCircle2 className="h-4 w-4 ml-2" />
                                                        الموافقة
                                                    </DropdownMenuItem>
                                                    <DropdownMenuItem onClick={() => handleApproveReturn(ret, false)}>
                                                        <XCircle className="h-4 w-4 ml-2" />
                                                        الرفض
                                                    </DropdownMenuItem>
                                                </>
                                            )}
                                            {(ret.status === "APPROVED" || ret.status === "موافق عليه") && (
                                                <DropdownMenuItem onClick={() => handleProcessRefund(ret)}>
                                                    <DollarSign className="h-4 w-4 ml-2" />
                                                    معالجة الاسترداد
                                                </DropdownMenuItem>
                                            )}
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Dialog لعرض تفاصيل المرتجع */}
            <Dialog open={detailsDialogOpen} onOpenChange={setDetailsDialogOpen}>
                <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>تفاصيل المرتجع</DialogTitle>
                    </DialogHeader>
                    {selectedReturn && (
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <p className="text-sm text-gray-500">رقم المرتجع</p>
                                    <p className="font-semibold">{selectedReturn.return_number}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500">التاريخ</p>
                                    <p className="font-semibold">{selectedReturn.return_date || selectedReturn.created_at}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500">النوع</p>
                                    <p className="font-semibold">
                                        {selectedReturn.return_type === "SALE_RETURN" ? "مرتجع مبيعات" : "مرتجع مشتريات"}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500">الحالة</p>
                                    <Badge className={getStatusColor(selectedReturn.status)}>
                                        {selectedReturn.status === "PENDING" ? "معلق" :
                                            selectedReturn.status === "APPROVED" ? "موافق عليه" :
                                                selectedReturn.status === "REJECTED" ? "مرفوض" :
                                                    selectedReturn.status === "COMPLETED" ? "مكتمل" : selectedReturn.status}
                                    </Badge>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500">العميل/المورد</p>
                                    <p className="font-semibold">{selectedReturn.customer_name || selectedReturn.supplier_name || "غير محدد"}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500">المجموع</p>
                                    <p className="font-semibold text-lg">{selectedReturn.total_amount?.toLocaleString()} ر.س</p>
                                </div>
                            </div>

                            {selectedReturn.return_reason && (
                                <div className="border-t pt-4">
                                    <p className="text-sm text-gray-500 mb-1">سبب الإرجاع</p>
                                    <p className="bg-orange-50 p-3 rounded">{selectedReturn.return_reason}</p>
                                </div>
                            )}

                            {selectedReturn.items && selectedReturn.items.length > 0 && (
                                <div className="border-t pt-4">
                                    <h3 className="font-semibold mb-3">المنتجات المرتجعة</h3>
                                    <div className="space-y-2">
                                        {selectedReturn.items.map((item: any, index: number) => (
                                            <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                                                <div>
                                                    <p className="font-medium">{item.product_name || `منتج #${item.product_id}`}</p>
                                                    <p className="text-sm text-gray-500">
                                                        الكمية: {item.quantity} × {item.unit_price} ر.س
                                                        {item.return_reason && ` - السبب: ${item.return_reason}`}
                                                    </p>
                                                </div>
                                                <p className="font-semibold">{(item.quantity * item.unit_price).toLocaleString()} ر.س</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {selectedReturn.notes && (
                                <div className="border-t pt-4">
                                    <p className="text-sm text-gray-500 mb-1">ملاحظات</p>
                                    <p className="bg-blue-50 p-3 rounded">{selectedReturn.notes}</p>
                                </div>
                            )}
                        </div>
                    )}
                </DialogContent>
            </Dialog>

            {/* Dialog للموافقة/الرفض */}
            <AlertDialog open={approvalDialogOpen} onOpenChange={setApprovalDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>
                            {returnToApprove?.approved ? "الموافقة على المرتجع" : "رفض المرتجع"}
                        </AlertDialogTitle>
                        <AlertDialogDescription>
                            {returnToApprove?.approved 
                                ? "هل أنت متأكد من الموافقة على هذا المرتجع؟ سيتم تحديث حالة المرتجع إلى 'موافق عليه'."
                                : "هل أنت متأكد من رفض هذا المرتجع؟ سيتم تحديث حالة المرتجع إلى 'مرفوض'."}
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel onClick={() => setReturnToApprove(null)}>إلغاء</AlertDialogCancel>
                        <AlertDialogAction 
                            onClick={confirmApproveReturn} 
                            className={returnToApprove?.approved ? "bg-green-600 hover:bg-green-700" : "bg-red-600 hover:bg-red-700"}
                        >
                            {returnToApprove?.approved ? "موافقة" : "رفض"}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            {/* Dialog لمعالجة الاسترداد */}
            <Dialog open={refundDialogOpen} onOpenChange={setRefundDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>معالجة الاسترداد</DialogTitle>
                    </DialogHeader>
                    {returnToRefund && (
                        <div className="space-y-4">
                            <div>
                                <p className="text-sm text-gray-500 mb-1">رقم المرتجع</p>
                                <p className="font-semibold">{returnToRefund.return_number}</p>
                            </div>
                            <div>
                                <Label>مبلغ الاسترداد (ر.س)</Label>
                                <Input
                                    type="number"
                                    value={refundAmount}
                                    onChange={(e) => setRefundAmount(parseFloat(e.target.value) || 0)}
                                    min={0}
                                    max={returnToRefund.total_amount}
                                />
                                <p className="text-xs text-gray-500 mt-1">
                                    المبلغ الأقصى: {returnToRefund.total_amount?.toLocaleString()} ر.س
                                </p>
                            </div>
                            <div>
                                <Label>طريقة الاسترداد</Label>
                                <Select value={refundMethod} onValueChange={setRefundMethod}>
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="نقدي">نقدي</SelectItem>
                                        <SelectItem value="تحويل بنكي">تحويل بنكي</SelectItem>
                                        <SelectItem value="شيك">شيك</SelectItem>
                                        <SelectItem value="رصيد في الحساب">رصيد في الحساب</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="flex gap-2 justify-end">
                                <Button variant="outline" onClick={() => setRefundDialogOpen(false)}>
                                    إلغاء
                                </Button>
                                <Button onClick={confirmProcessRefund} className="bg-green-600 hover:bg-green-700">
                                    معالجة الاسترداد
                                </Button>
                            </div>
                        </div>
                    )}
                </DialogContent>
            </Dialog>
        </div>
    )
}
