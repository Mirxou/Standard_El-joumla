"""
Inventory Optimization Models - نماذج تحسين المخزون
تحليل ABC، الأرصدة الآمنة، وتتبع الدفعات
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional


class ABCCategory(Enum):
    """فئات تحليل ABC"""

    A = "A"  # عالية القيمة (70-80% من القيمة)
    B = "B"  # متوسطة القيمة (15-20% من القيمة)
    C = "C"  # منخفضة القيمة (5-10% من القيمة)


class ReorderStatus(Enum):
    """حالة إعادة الطلب"""

    NORMAL = "NORMAL"  # عادي
    APPROACHING = "APPROACHING"  # يقترب من نقطة الطلب
    REORDER = "REORDER"  # يحتاج إعادة طلب
    CRITICAL = "CRITICAL"  # حرج جداً
    STOCKOUT = "STOCKOUT"  # نفاذ المخزون


class BatchStatus(Enum):
    """حالة الدفعة"""

    ACTIVE = "ACTIVE"  # نشطة
    EXPIRED = "EXPIRED"  # منتهية الصلاحية
    EXPIRING_SOON = "EXPIRING_SOON"  # تقترب من الانتهاء
    DAMAGED = "DAMAGED"  # تالفة
    RECALLED = "RECALLED"  # مسحوبة


@dataclass
class ABCAnalysisResult:
    """نتيجة تحليل ABC لمنتج"""

    product_id: int
    product_code: str
    product_name: str

    # بيانات المبيعات
    annual_sales_quantity: Decimal = Decimal("0")
    annual_sales_value: Decimal = Decimal("0")
    average_unit_price: Decimal = Decimal("0")

    # بيانات المخزون
    current_stock: Decimal = Decimal("0")
    stock_value: Decimal = Decimal("0")

    # تحليل ABC
    abc_category: str = ABCCategory.C.value
    percentage_of_total_value: Decimal = Decimal("0")
    cumulative_percentage: Decimal = Decimal("0")
    rank: int = 0

    # المبيعات
    sales_frequency: int = 0  # عدد مرات البيع
    last_sale_date: Optional[date] = None
    days_since_last_sale: Optional[int] = None

    # التوصيات
    recommendations: List[str] = field(default_factory=list)
    priority_level: int = 1  # 1-5 (5 أعلى أولوية)

    # التواريخ
    analysis_date: date = field(default_factory=date.today)

    @property
    def category_label(self) -> str:
        """تسمية الفئة بالعربية"""
        labels = {
            ABCCategory.A.value: "فئة A - عالية القيمة",
            ABCCategory.B.value: "فئة B - متوسطة القيمة",
            ABCCategory.C.value: "فئة C - منخفضة القيمة",
        }
        return labels.get(self.abc_category, self.abc_category)

    @property
    def needs_attention(self) -> bool:
        """يحتاج انتباه"""
        # فئة A بدون مبيعات حديثة
        if self.abc_category == ABCCategory.A.value:
            if self.days_since_last_sale and self.days_since_last_sale > 30:
                return True

        # مخزون عالي القيمة راكد
        if self.stock_value > 10000 and self.days_since_last_sale and self.days_since_last_sale > 60:
            return True

        return False

    def generate_recommendations(self):
        """توليد التوصيات"""
        self.recommendations = []

        if self.abc_category == ABCCategory.A.value:
            self.recommendations.append("مراقبة دقيقة للمخزون - منتج عالي القيمة")
            self.recommendations.append("التأكد من توفره دائماً")
            self.recommendations.append("مراجعة الأسعار والعروض بانتظام")
            self.priority_level = 5

            if self.days_since_last_sale and self.days_since_last_sale > 30:
                self.recommendations.append("⚠️ لم يُباع منذ أكثر من شهر - مراجعة ضرورية")

        elif self.abc_category == ABCCategory.B.value:
            self.recommendations.append("مراقبة منتظمة")
            self.recommendations.append("الحفاظ على مستوى مخزون متوازن")
            self.priority_level = 3

        else:  # Category C
            self.recommendations.append("إدارة بسيطة")
            self.recommendations.append("يمكن تقليل المخزون لتوفير رأس المال")
            self.priority_level = 1

            if self.stock_value > 5000:
                self.recommendations.append("💡 مخزون زائد - يُنصح بالتخفيض")

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "product_id": self.product_id,
            "product_code": self.product_code,
            "product_name": self.product_name,
            "annual_sales_quantity": float(self.annual_sales_quantity),
            "annual_sales_value": float(self.annual_sales_value),
            "average_unit_price": float(self.average_unit_price),
            "current_stock": float(self.current_stock),
            "stock_value": float(self.stock_value),
            "abc_category": self.abc_category,
            "percentage_of_total_value": float(self.percentage_of_total_value),
            "cumulative_percentage": float(self.cumulative_percentage),
            "rank": self.rank,
            "sales_frequency": self.sales_frequency,
            "last_sale_date": (self.last_sale_date.isoformat() if self.last_sale_date else None),
            "days_since_last_sale": self.days_since_last_sale,
            "recommendations": self.recommendations,
            "priority_level": self.priority_level,
            "analysis_date": self.analysis_date.isoformat(),
        }


@dataclass
class SafetyStockConfig:
    """إعدادات الأرصدة الآمنة لمنتج"""

    id: Optional[int] = None
    product_id: int = 0
    product_code: str = ""
    product_name: str = ""

    # نقاط المخزون
    reorder_point: Decimal = Decimal("0")  # نقطة إعادة الطلب
    safety_stock: Decimal = Decimal("0")  # المخزون الآمن
    maximum_stock: Decimal = Decimal("0")  # الحد الأقصى
    minimum_stock: Decimal = Decimal("0")  # الحد الأدنى

    # بيانات الطلب
    average_daily_demand: Decimal = Decimal("0")  # الطلب اليومي المتوسط
    lead_time_days: int = 7  # مدة التوريد بالأيام
    service_level: Decimal = Decimal("95")  # مستوى الخدمة %

    # الحالة الحالية
    current_stock: Decimal = Decimal("0")
    reorder_status: str = ReorderStatus.NORMAL.value

    # كمية الطلب
    economic_order_quantity: Decimal = Decimal("0")  # EOQ
    suggested_order_quantity: Decimal = Decimal("0")

    # التكاليف
    holding_cost_percentage: Decimal = Decimal("20")  # تكلفة الحفظ %
    order_cost: Decimal = Decimal("50")  # تكلفة الطلب

    # التتبع
    last_reorder_date: Optional[date] = None
    last_stockout_date: Optional[date] = None
    stockout_count: int = 0

    # التفعيل
    is_active: bool = True
    auto_reorder_enabled: bool = False

    # التواريخ
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def status_label(self) -> str:
        """تسمية الحالة"""
        labels = {
            ReorderStatus.NORMAL.value: "عادي ✓",
            ReorderStatus.APPROACHING.value: "يقترب من نقطة الطلب ⚠️",
            ReorderStatus.REORDER.value: "يحتاج إعادة طلب 📦",
            ReorderStatus.CRITICAL.value: "حرج جداً ⛔",
            ReorderStatus.STOCKOUT.value: "نفاذ المخزون ❌",
        }
        return labels.get(self.reorder_status, self.reorder_status)

    @property
    def days_until_stockout(self) -> Optional[int]:
        """أيام حتى نفاذ المخزون"""
        if self.average_daily_demand > 0:
            days = float(self.current_stock / self.average_daily_demand)
            return int(days)
        return None

    @property
    def quantity_below_reorder(self) -> Decimal:
        """الكمية تحت نقطة الطلب"""
        diff = self.reorder_point - self.current_stock
        return max(diff, Decimal("0"))

    def calculate_reorder_point(self):
        """حساب نقطة إعادة الطلب"""
        # ROP = (Average Daily Demand × Lead Time) + Safety Stock
        self.reorder_point = (self.average_daily_demand * self.lead_time_days) + self.safety_stock

    def calculate_safety_stock(self, demand_std_dev: Optional[Decimal] = None):
        """حساب المخزون الآمن"""
        # Safety Stock = Z × σ × √LT
        # Z = Z-score based on service level (e.g., 1.65 for 95%)

        if demand_std_dev is None:
            # تقدير بسيط: 50% من الطلب اليومي × مدة التوريد
            self.safety_stock = self.average_daily_demand * self.lead_time_days * Decimal("0.5")
        else:
            # حساب أكثر دقة
            import math

            z_score = Decimal("1.65")  # 95% service level
            lead_time_sqrt = Decimal(str(math.sqrt(self.lead_time_days)))
            self.safety_stock = z_score * demand_std_dev * lead_time_sqrt

    def calculate_economic_order_quantity(self, annual_demand: Decimal, unit_cost: Decimal):
        """حساب كمية الطلب الاقتصادية (EOQ)"""
        # EOQ = √((2 × Annual Demand × Order Cost) / (Holding Cost per Unit))

        if unit_cost > 0 and self.holding_cost_percentage > 0:
            import math

            holding_cost_per_unit = unit_cost * (self.holding_cost_percentage / 100)

            if holding_cost_per_unit > 0:
                numerator = 2 * annual_demand * self.order_cost
                denominator = holding_cost_per_unit
                self.economic_order_quantity = Decimal(str(math.sqrt(float(numerator / denominator))))

    def update_reorder_status(self):
        """تحديث حالة إعادة الطلب"""
        if self.current_stock <= 0:
            self.reorder_status = ReorderStatus.STOCKOUT.value
        elif self.current_stock <= self.minimum_stock:
            self.reorder_status = ReorderStatus.CRITICAL.value
        elif self.current_stock <= self.reorder_point:
            self.reorder_status = ReorderStatus.REORDER.value
        elif self.current_stock <= self.reorder_point * Decimal("1.2"):
            self.reorder_status = ReorderStatus.APPROACHING.value
        else:
            self.reorder_status = ReorderStatus.NORMAL.value

    def calculate_suggested_order(self):
        """حساب كمية الطلب المقترحة"""
        if self.current_stock < self.reorder_point:
            # الطلب حتى الوصول للحد الأقصى
            shortage = self.maximum_stock - self.current_stock

            # استخدام EOQ أو الكمية الناقصة، أيهما أكبر
            if self.economic_order_quantity > 0:
                self.suggested_order_quantity = max(shortage, self.economic_order_quantity)
            else:
                self.suggested_order_quantity = shortage
        else:
            self.suggested_order_quantity = Decimal("0")

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_code": self.product_code,
            "product_name": self.product_name,
            "reorder_point": float(self.reorder_point),
            "safety_stock": float(self.safety_stock),
            "maximum_stock": float(self.maximum_stock),
            "minimum_stock": float(self.minimum_stock),
            "average_daily_demand": float(self.average_daily_demand),
            "lead_time_days": self.lead_time_days,
            "service_level": float(self.service_level),
            "current_stock": float(self.current_stock),
            "reorder_status": self.reorder_status,
            "economic_order_quantity": float(self.economic_order_quantity),
            "suggested_order_quantity": float(self.suggested_order_quantity),
            "holding_cost_percentage": float(self.holding_cost_percentage),
            "order_cost": float(self.order_cost),
            "last_reorder_date": (self.last_reorder_date.isoformat() if self.last_reorder_date else None),
            "last_stockout_date": (self.last_stockout_date.isoformat() if self.last_stockout_date else None),
            "stockout_count": self.stockout_count,
            "is_active": self.is_active,
            "auto_reorder_enabled": self.auto_reorder_enabled,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SafetyStockConfig":
        """إنشاء من قاموس"""
        # تحويل التواريخ
        if data.get("last_reorder_date"):
            data["last_reorder_date"] = date.fromisoformat(data["last_reorder_date"])
        if data.get("last_stockout_date"):
            data["last_stockout_date"] = date.fromisoformat(data["last_stockout_date"])
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        # تحويل Decimal
        decimal_fields = [
            "reorder_point",
            "safety_stock",
            "maximum_stock",
            "minimum_stock",
            "average_daily_demand",
            "service_level",
            "current_stock",
            "economic_order_quantity",
            "suggested_order_quantity",
            "holding_cost_percentage",
            "order_cost",
        ]
        for field in decimal_fields:  # noqa: F402
            if field in data and data[field] is not None:
                data[field] = Decimal(str(data[field]))

        return cls(**data)


@dataclass
class ProductBatch:
    """دفعة منتج مع تتبع الصلاحية والأرقام المتسلسلة"""

    id: Optional[int] = None
    product_id: int = 0
    product_code: str = ""
    product_name: str = ""

    # معلومات الدفعة
    batch_number: str = ""
    serial_numbers: List[str] = field(default_factory=list)

    # الكميات
    initial_quantity: Decimal = Decimal("0")
    current_quantity: Decimal = Decimal("0")
    remaining_quantity: Decimal = Decimal("0")
    reserved_quantity: Decimal = Decimal("0")
    available_quantity: Decimal = Decimal("0")

    # التواريخ
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    received_date: date = field(default_factory=date.today)

    # الموقع
    warehouse_location: str = ""
    rack_number: str = ""
    bin_number: str = ""

    # المورد
    supplier_id: Optional[int] = None
    supplier_name: str = ""
    purchase_order_number: str = ""

    # السعر
    unit_cost: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")

    # الحالة
    status: str = BatchStatus.ACTIVE.value

    # الملاحظات
    notes: str = ""
    quality_check_passed: bool = True

    # التتبع
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def is_expired(self) -> bool:
        """هل انتهت الصلاحية"""
        if self.expiry_date:
            return date.today() > self.expiry_date
        return False

    @property
    def is_expiring_soon(self) -> bool:
        """تقترب من انتهاء الصلاحية (خلال 30 يوم)"""
        if self.expiry_date:
            days_to_expiry = (self.expiry_date - date.today()).days
            return 0 < days_to_expiry <= 30
        return False

    @property
    def days_to_expiry(self) -> Optional[int]:
        """أيام حتى انتهاء الصلاحية"""
        if self.expiry_date:
            delta = self.expiry_date - date.today()
            return delta.days
        return None

    @property
    def days_in_stock(self) -> int:
        """أيام في المخزون"""
        delta = date.today() - self.received_date
        return delta.days

    @property
    def usage_percentage(self) -> Decimal:
        """نسبة الاستخدام"""
        if self.initial_quantity > 0:
            used = self.initial_quantity - self.current_quantity
            return (used / self.initial_quantity) * 100
        return Decimal("0")

    def update_status(self):
        """تحديث الحالة"""
        if self.is_expired:
            self.status = BatchStatus.EXPIRED.value
        elif self.is_expiring_soon:
            self.status = BatchStatus.EXPIRING_SOON.value
        elif self.current_quantity <= 0:
            self.status = BatchStatus.ACTIVE.value  # فارغة لكن لا تزال نشطة للسجل
        else:
            self.status = BatchStatus.ACTIVE.value

    def consume(self, quantity: Decimal) -> bool:
        """استهلاك كمية من الدفعة"""
        if quantity <= self.available_quantity:
            self.current_quantity -= quantity
            self.available_quantity = self.current_quantity - self.reserved_quantity
            self.update_status()
            self.updated_at = datetime.now()
            return True
        return False

    def reserve(self, quantity: Decimal) -> bool:
        """حجز كمية"""
        if quantity <= self.available_quantity:
            self.reserved_quantity += quantity
            self.available_quantity = self.current_quantity - self.reserved_quantity
            self.updated_at = datetime.now()
            return True
        return False

    def release_reservation(self, quantity: Decimal):
        """إلغاء حجز"""
        self.reserved_quantity = max(Decimal("0"), self.reserved_quantity - quantity)
        self.available_quantity = self.current_quantity - self.reserved_quantity
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_code": self.product_code,
            "product_name": self.product_name,
            "batch_number": self.batch_number,
            "serial_numbers": self.serial_numbers,
            "initial_quantity": float(self.initial_quantity),
            "current_quantity": float(self.current_quantity),
            "remaining_quantity": float(self.remaining_quantity),
            "reserved_quantity": float(self.reserved_quantity),
            "available_quantity": float(self.available_quantity),
            "manufacturing_date": (self.manufacturing_date.isoformat() if self.manufacturing_date else None),
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "received_date": self.received_date.isoformat(),
            "warehouse_location": self.warehouse_location,
            "rack_number": self.rack_number,
            "bin_number": self.bin_number,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "purchase_order_number": self.purchase_order_number,
            "unit_cost": float(self.unit_cost),
            "total_cost": float(self.total_cost),
            "status": self.status,
            "notes": self.notes,
            "quality_check_passed": self.quality_check_passed,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductBatch":
        """إنشاء من قاموس"""
        # تحويل التواريخ
        if data.get("manufacturing_date"):
            data["manufacturing_date"] = date.fromisoformat(data["manufacturing_date"])
        if data.get("expiry_date"):
            data["expiry_date"] = date.fromisoformat(data["expiry_date"])
        if data.get("received_date"):
            data["received_date"] = date.fromisoformat(data["received_date"])
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        # تحويل Decimal
        decimal_fields = [
            "initial_quantity",
            "current_quantity",
            "remaining_quantity",
            "reserved_quantity",
            "available_quantity",
            "unit_cost",
            "total_cost",
        ]
        for field in decimal_fields:  # noqa: F402
            if field in data and data[field] is not None:
                data[field] = Decimal(str(data[field]))

        return cls(**data)


@dataclass
class ReorderRecommendation:
    """توصية إعادة طلب"""

    product_id: int
    product_code: str
    product_name: str

    # الحالة الحالية
    current_stock: Decimal
    reorder_point: Decimal
    safety_stock: Decimal

    # التوصية
    suggested_quantity: Decimal
    priority: int  # 1-5
    urgency: str  # "URGENT", "HIGH", "MEDIUM", "LOW"

    # الأسباب
    reasons: List[str] = field(default_factory=list)

    # التقديرات
    estimated_stockout_date: Optional[date] = None
    estimated_cost: Decimal = Decimal("0")

    # المورد المقترح
    preferred_supplier_id: Optional[int] = None
    preferred_supplier_name: str = ""
    lead_time_days: int = 7

    # التاريخ
    recommendation_date: date = field(default_factory=date.today)

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "product_id": self.product_id,
            "product_code": self.product_code,
            "product_name": self.product_name,
            "current_stock": float(self.current_stock),
            "reorder_point": float(self.reorder_point),
            "safety_stock": float(self.safety_stock),
            "suggested_quantity": float(self.suggested_quantity),
            "priority": self.priority,
            "urgency": self.urgency,
            "reasons": self.reasons,
            "estimated_stockout_date": (
                self.estimated_stockout_date.isoformat() if self.estimated_stockout_date else None
            ),
            "estimated_cost": float(self.estimated_cost),
            "preferred_supplier_id": self.preferred_supplier_id,
            "preferred_supplier_name": self.preferred_supplier_name,
            "lead_time_days": self.lead_time_days,
            "recommendation_date": self.recommendation_date.isoformat(),
        }
