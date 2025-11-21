"""
نماذج الجرد الدوري والتسويات
Physical Count and Stock Adjustment Models
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from enum import Enum


class CountStatus(Enum):
    """حالات الجرد"""
    DRAFT = "draft"  # مسودة
    IN_PROGRESS = "in_progress"  # قيد التنفيذ
    COMPLETED = "completed"  # مكتمل
    APPROVED = "approved"  # معتمد
    CANCELLED = "cancelled"  # ملغى


class AdjustmentType(Enum):
    """أنواع التسويات"""
    COUNT_ADJUSTMENT = "count_adjustment"  # تسوية جرد
    DAMAGE = "damage"  # تالف
    EXPIRY = "expiry"  # منتهي الصلاحية
    THEFT = "theft"  # سرقة
    LOSS = "loss"  # فقد
    FOUND = "found"  # وجدت
    CORRECTION = "correction"  # تصحيح
    TRANSFER = "transfer"  # تحويل
    OTHER = "other"  # أخرى


class AdjustmentStatus(Enum):
    """حالات التسوية"""
    PENDING = "pending"  # معلقة
    APPROVED = "approved"  # معتمدة
    REJECTED = "rejected"  # مرفوضة
    APPLIED = "applied"  # مطبقة


@dataclass
class PhysicalCount:
    """نموذج الجرد الدوري"""
    
    # المعلومات الأساسية
    id: Optional[int] = None
    count_number: str = ""  # رقم الجرد
    count_date: date = field(default_factory=date.today)
    scheduled_date: Optional[date] = None  # التاريخ المخطط
    
    # التفاصيل
    description: str = ""
    location: Optional[str] = None  # الموقع/المستودع
    counted_by: Optional[int] = None  # المستخدم الذي قام بالجرد
    counted_by_name: Optional[str] = None
    
    # الحالة والموافقة
    status: CountStatus = CountStatus.DRAFT
    approved_by: Optional[int] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    # الإحصائيات
    total_items: int = 0  # عدد الأصناف
    counted_items: int = 0  # الأصناف المجردة
    items_with_variance: int = 0  # أصناف بها فروقات
    total_variance_value: Decimal = Decimal('0.00')  # قيمة الفروقات
    
    # التواريخ
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # العلاقات
    items: List['CountItem'] = field(default_factory=list)
    notes: str = ""
    
    def __post_init__(self):
        """تحويل النصوص إلى Enums"""
        if isinstance(self.status, str):
            self.status = CountStatus(self.status)
    
    @property
    def status_label(self) -> str:
        """تسمية الحالة بالعربية"""
        labels = {
            CountStatus.DRAFT: "مسودة",
            CountStatus.IN_PROGRESS: "قيد التنفيذ",
            CountStatus.COMPLETED: "مكتمل",
            CountStatus.APPROVED: "معتمد",
            CountStatus.CANCELLED: "ملغى"
        }
        return labels.get(self.status, "غير معروف")
    
    @property
    def completion_percentage(self) -> float:
        """نسبة الإنجاز"""
        if self.total_items == 0:
            return 0.0
        return (self.counted_items / self.total_items) * 100
    
    @property
    def is_complete(self) -> bool:
        """هل اكتمل الجرد"""
        return self.counted_items == self.total_items
    
    @property
    def has_variances(self) -> bool:
        """هل يوجد فروقات"""
        return self.items_with_variance > 0
    
    @property
    def requires_approval(self) -> bool:
        """يحتاج موافقة"""
        return self.status == CountStatus.COMPLETED and not self.approved_at
    
    @property
    def is_editable(self) -> bool:
        """قابل للتعديل"""
        return self.status in [CountStatus.DRAFT, CountStatus.IN_PROGRESS]
    
    def calculate_statistics(self) -> None:
        """حساب الإحصائيات من العناصر"""
        if not self.items:
            return
        
        self.total_items = len(self.items)
        self.counted_items = sum(1 for item in self.items if item.is_counted)
        self.items_with_variance = sum(1 for item in self.items if item.has_variance)
        self.total_variance_value = sum(
            (item.variance_value or Decimal('0.00')) for item in self.items
        )
    
    def start_count(self) -> bool:
        """بدء الجرد"""
        if self.status == CountStatus.DRAFT:
            self.status = CountStatus.IN_PROGRESS
            return True
        return False
    
    def complete_count(self) -> bool:
        """إكمال الجرد"""
        if self.status == CountStatus.IN_PROGRESS and self.is_complete:
            self.status = CountStatus.COMPLETED
            self.completed_at = datetime.now()
            return True
        return False
    
    def approve(self, user_id: int, user_name: str) -> bool:
        """اعتماد الجرد"""
        if self.status == CountStatus.COMPLETED:
            self.status = CountStatus.APPROVED
            self.approved_by = user_id
            self.approved_by_name = user_name
            self.approved_at = datetime.now()
            return True
        return False
    
    def cancel(self) -> bool:
        """إلغاء الجرد"""
        if self.status != CountStatus.APPROVED:
            self.status = CountStatus.CANCELLED
            return True
        return False


@dataclass
class CountItem:
    """عنصر في الجرد"""
    
    # المعلومات الأساسية
    id: Optional[int] = None
    count_id: Optional[int] = None
    product_id: int = 0
    
    # معلومات المنتج
    product_code: str = ""
    product_name: str = ""
    product_barcode: Optional[str] = None
    
    # الكميات
    system_quantity: Decimal = Decimal('0.00')  # الكمية في النظام
    counted_quantity: Optional[Decimal] = None  # الكمية المجردة
    variance_quantity: Decimal = Decimal('0.00')  # الفرق
    
    # القيم
    unit_cost: Decimal = Decimal('0.00')  # تكلفة الوحدة
    system_value: Decimal = Decimal('0.00')  # القيمة في النظام
    counted_value: Decimal = Decimal('0.00')  # القيمة المجردة
    variance_value: Decimal = Decimal('0.00')  # قيمة الفرق
    
    # التفاصيل
    location: Optional[str] = None  # الموقع
    batch_number: Optional[str] = None  # رقم الدفعة
    notes: str = ""
    
    # الحالة
    is_counted: bool = False
    requires_recount: bool = False  # يحتاج إعادة عد
    
    # التواريخ
    counted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    @property
    def has_variance(self) -> bool:
        """هل يوجد فرق"""
        return abs(self.variance_quantity) > Decimal('0.01')
    
    @property
    def variance_percentage(self) -> float:
        """نسبة الفرق"""
        if self.system_quantity == 0:
            return 0.0
        return float((self.variance_quantity / self.system_quantity) * 100)
    
    @property
    def is_shortage(self) -> bool:
        """نقص"""
        return self.variance_quantity < 0
    
    @property
    def is_surplus(self) -> bool:
        """فائض"""
        return self.variance_quantity > 0
    
    def update_counted_quantity(self, quantity: Decimal) -> None:
        """تحديث الكمية المجردة"""
        self.counted_quantity = quantity
        self.is_counted = True
        self.counted_at = datetime.now()
        self.calculate_variance()
    
    def calculate_variance(self) -> None:
        """حساب الفرق"""
        if self.counted_quantity is not None:
            self.variance_quantity = self.counted_quantity - self.system_quantity
            self.counted_value = self.counted_quantity * self.unit_cost
            self.variance_value = self.variance_quantity * self.unit_cost
        else:
            self.variance_quantity = Decimal('0.00')
            self.variance_value = Decimal('0.00')


@dataclass
class StockAdjustment:
    """نموذج تسوية المخزون"""
    
    # المعلومات الأساسية
    id: Optional[int] = None
    adjustment_number: str = ""  # رقم التسوية
    adjustment_date: date = field(default_factory=date.today)
    
    # النوع والسبب
    adjustment_type: AdjustmentType = AdjustmentType.CORRECTION
    reason: str = ""
    
    # المنتج
    product_id: int = 0
    product_code: str = ""
    product_name: str = ""
    
    # الكميات
    quantity_before: Decimal = Decimal('0.00')  # الكمية قبل
    adjustment_quantity: Decimal = Decimal('0.00')  # كمية التسوية (+/-)
    quantity_after: Decimal = Decimal('0.00')  # الكمية بعد
    
    # القيم
    unit_cost: Decimal = Decimal('0.00')
    adjustment_value: Decimal = Decimal('0.00')  # قيمة التسوية
    
    # التفاصيل
    location: Optional[str] = None
    batch_number: Optional[str] = None
    count_id: Optional[int] = None  # مرتبط بجرد
    
    # الحالة والموافقة
    status: AdjustmentStatus = AdjustmentStatus.PENDING
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    approved_by: Optional[int] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    # التواريخ
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None
    
    # ملاحظات
    notes: str = ""
    
    def __post_init__(self):
        """تحويل النصوص إلى Enums"""
        if isinstance(self.adjustment_type, str):
            self.adjustment_type = AdjustmentType(self.adjustment_type)
        if isinstance(self.status, str):
            self.status = AdjustmentStatus(self.status)
    
    @property
    def type_label(self) -> str:
        """تسمية النوع بالعربية"""
        labels = {
            AdjustmentType.COUNT_ADJUSTMENT: "تسوية جرد",
            AdjustmentType.DAMAGE: "تالف",
            AdjustmentType.EXPIRY: "منتهي الصلاحية",
            AdjustmentType.THEFT: "سرقة",
            AdjustmentType.LOSS: "فقد",
            AdjustmentType.FOUND: "وجدت",
            AdjustmentType.CORRECTION: "تصحيح",
            AdjustmentType.TRANSFER: "تحويل",
            AdjustmentType.OTHER: "أخرى"
        }
        return labels.get(self.adjustment_type, "غير معروف")
    
    @property
    def status_label(self) -> str:
        """تسمية الحالة بالعربية"""
        labels = {
            AdjustmentStatus.PENDING: "معلقة",
            AdjustmentStatus.APPROVED: "معتمدة",
            AdjustmentStatus.REJECTED: "مرفوضة",
            AdjustmentStatus.APPLIED: "مطبقة"
        }
        return labels.get(self.status, "غير معروف")
    
    @property
    def is_increase(self) -> bool:
        """زيادة"""
        return self.adjustment_quantity > 0
    
    @property
    def is_decrease(self) -> bool:
        """نقص"""
        return self.adjustment_quantity < 0
    
    @property
    def requires_approval(self) -> bool:
        """يحتاج موافقة"""
        return self.status == AdjustmentStatus.PENDING
    
    @property
    def is_editable(self) -> bool:
        """قابل للتعديل"""
        return self.status == AdjustmentStatus.PENDING
    
    @property
    def can_be_applied(self) -> bool:
        """يمكن تطبيقه"""
        return self.status == AdjustmentStatus.APPROVED and not self.applied_at
    
    def calculate_after_quantity(self) -> None:
        """حساب الكمية بعد التسوية"""
        self.quantity_after = self.quantity_before + self.adjustment_quantity
        self.adjustment_value = self.adjustment_quantity * self.unit_cost
    
    def approve(self, user_id: int, user_name: str) -> bool:
        """اعتماد التسوية"""
        if self.status == AdjustmentStatus.PENDING:
            self.status = AdjustmentStatus.APPROVED
            self.approved_by = user_id
            self.approved_by_name = user_name
            self.approved_at = datetime.now()
            return True
        return False
    
    def reject(self, user_id: int, user_name: str, reason: str) -> bool:
        """رفض التسوية"""
        if self.status == AdjustmentStatus.PENDING:
            self.status = AdjustmentStatus.REJECTED
            self.approved_by = user_id
            self.approved_by_name = user_name
            self.approved_at = datetime.now()
            self.rejection_reason = reason
            return True
        return False
    
    def mark_applied(self) -> bool:
        """وضع علامة مطبقة"""
        if self.status == AdjustmentStatus.APPROVED:
            self.status = AdjustmentStatus.APPLIED
            self.applied_at = datetime.now()
            return True
        return False
