"""
نماذج التقارير المتقدمة
Advanced Reports Models

يوفر هذا الملف نماذج بيانات شاملة لنظام التقارير المتقدمة:
- تقارير المبيعات (Sales Reports)
- تقارير المخزون (Inventory Reports)
- تقارير المالية (Financial Reports)
- تقارير التحليلات (Analytics Reports)
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from enum import Enum


class ReportType(Enum):
    """أنواع التقارير"""
    SALES_SUMMARY = "sales_summary"                      # ملخص المبيعات
    SALES_DETAILED = "sales_detailed"                    # المبيعات التفصيلية
    SALES_BY_PRODUCT = "sales_by_product"                # المبيعات حسب المنتج
    SALES_BY_CUSTOMER = "sales_by_customer"              # المبيعات حسب العميل
    SALES_BY_CATEGORY = "sales_by_category"              # المبيعات حسب الفئة
    SALES_BY_EMPLOYEE = "sales_by_employee"              # المبيعات حسب الموظف
    
    INVENTORY_MOVEMENT = "inventory_movement"            # حركة المخزون
    INVENTORY_VALUATION = "inventory_valuation"          # تقييم المخزون
    INVENTORY_AGING = "inventory_aging"                  # أعمار المخزون
    INVENTORY_TURNOVER = "inventory_turnover"            # دوران المخزون
    INVENTORY_REORDER = "inventory_reorder"              # احتياجات الطلب
    INVENTORY_COUNT = "inventory_count"                  # تقارير الجرد
    
    FINANCIAL_INCOME = "financial_income"                # قائمة الدخل
    FINANCIAL_BALANCE = "financial_balance"              # الميزانية العمومية
    FINANCIAL_CASHFLOW = "financial_cashflow"            # التدفقات النقدية
    FINANCIAL_TRIAL_BALANCE = "financial_trial_balance"  # ميزان المراجعة
    FINANCIAL_LEDGER = "financial_ledger"                # دفتر الأستاذ
    FINANCIAL_PROFIT_LOSS = "financial_profit_loss"      # الأرباح والخسائر
    
    CUSTOMER_ANALYSIS = "customer_analysis"              # تحليل العملاء
    SUPPLIER_ANALYSIS = "supplier_analysis"              # تحليل الموردين
    PAYMENT_ANALYSIS = "payment_analysis"                # تحليل المدفوعات
    DEBT_ANALYSIS = "debt_analysis"                      # تحليل الديون


class ReportPeriod(Enum):
    """الفترات الزمنية للتقارير"""
    DAILY = "daily"                  # يومي
    WEEKLY = "weekly"                # أسبوعي
    MONTHLY = "monthly"              # شهري
    QUARTERLY = "quarterly"          # ربع سنوي
    YEARLY = "yearly"                # سنوي
    CUSTOM = "custom"                # مخصص


class ReportFormat(Enum):
    """صيغ التقارير"""
    PDF = "pdf"          # PDF
    EXCEL = "excel"      # Excel
    CSV = "csv"          # CSV
    HTML = "html"        # HTML
    JSON = "json"        # JSON


class ChartType(Enum):
    """أنواع الرسوم البيانية"""
    LINE = "line"                # خطي
    BAR = "bar"                  # أعمدة
    PIE = "pie"                  # دائري
    AREA = "area"                # مساحي
    SCATTER = "scatter"          # نقاط مبعثرة
    DONUT = "donut"              # حلقي


@dataclass
class ReportFilter:
    """فلاتر التقارير"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    period: ReportPeriod = ReportPeriod.MONTHLY
    
    customer_ids: List[int] = field(default_factory=list)
    supplier_ids: List[int] = field(default_factory=list)
    product_ids: List[int] = field(default_factory=list)
    category_ids: List[int] = field(default_factory=list)
    employee_ids: List[int] = field(default_factory=list)
    
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    
    include_returns: bool = True
    include_quotes: bool = False
    only_approved: bool = True
    
    group_by: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: str = "DESC"
    
    limit: Optional[int] = None


@dataclass
class SalesReportLine:
    """سطر تقرير المبيعات"""
    date: date
    invoice_number: str
    customer_name: str
    product_name: Optional[str] = None
    category_name: Optional[str] = None
    quantity: float = 0
    unit_price: float = 0
    discount: float = 0
    tax: float = 0
    total: float = 0
    profit: float = 0
    profit_margin: float = 0
    payment_method: Optional[str] = None
    employee_name: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class SalesReportSummary:
    """ملخص تقرير المبيعات"""
    period_start: date
    period_end: date
    
    total_sales: float = 0
    total_invoices: int = 0
    total_quantity: float = 0
    total_discount: float = 0
    total_tax: float = 0
    total_profit: float = 0
    
    average_invoice_value: float = 0
    average_profit_margin: float = 0
    
    cash_sales: float = 0
    credit_sales: float = 0
    card_sales: float = 0
    
    returns_count: int = 0
    returns_value: float = 0
    
    net_sales: float = 0
    
    top_products: List[Dict[str, Any]] = field(default_factory=list)
    top_customers: List[Dict[str, Any]] = field(default_factory=list)
    top_categories: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class InventoryReportLine:
    """سطر تقرير المخزون"""
    product_id: int
    product_code: str
    product_name: str
    category_name: str
    
    opening_quantity: float = 0
    purchases: float = 0
    sales: float = 0
    returns: float = 0
    adjustments: float = 0
    closing_quantity: float = 0
    
    unit_cost: float = 0
    total_value: float = 0
    
    reorder_point: Optional[float] = None
    safety_stock: Optional[float] = None
    
    days_in_stock: Optional[int] = None
    turnover_rate: Optional[float] = None
    
    status: str = "active"
    last_movement_date: Optional[date] = None


@dataclass
class InventoryReportSummary:
    """ملخص تقرير المخزون"""
    period_start: date
    period_end: date
    
    total_products: int = 0
    total_quantity: float = 0
    total_value: float = 0
    
    total_purchases: float = 0
    total_sales: float = 0
    total_adjustments: float = 0
    
    low_stock_items: int = 0
    out_of_stock_items: int = 0
    overstock_items: int = 0
    
    average_turnover_rate: float = 0
    total_inventory_days: float = 0
    
    by_category: List[Dict[str, Any]] = field(default_factory=list)
    slow_moving: List[Dict[str, Any]] = field(default_factory=list)
    fast_moving: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class FinancialReportLine:
    """سطر التقرير المالي"""
    account_code: str
    account_name: str
    account_type: str
    parent_account: Optional[str] = None
    
    opening_balance: float = 0
    debit: float = 0
    credit: float = 0
    closing_balance: float = 0
    
    percentage: float = 0
    level: int = 0


@dataclass
class FinancialReportSummary:
    """ملخص التقرير المالي"""
    period_start: date
    period_end: date
    report_type: ReportType
    
    total_assets: float = 0
    total_liabilities: float = 0
    total_equity: float = 0
    
    total_revenue: float = 0
    total_expenses: float = 0
    net_income: float = 0
    
    gross_profit: float = 0
    gross_profit_margin: float = 0
    
    operating_income: float = 0
    operating_margin: float = 0
    
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    debt_ratio: Optional[float] = None
    
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None


@dataclass
class ChartData:
    """بيانات الرسم البياني"""
    chart_type: ChartType
    title: str
    labels: List[str] = field(default_factory=list)
    datasets: List[Dict[str, Any]] = field(default_factory=list)
    
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    
    colors: List[str] = field(default_factory=list)
    show_legend: bool = True
    show_values: bool = True


@dataclass
class Report:
    """نموذج التقرير الشامل"""
    id: Optional[int] = None
    report_type: ReportType = ReportType.SALES_SUMMARY
    title: str = ""
    description: Optional[str] = None
    
    filters: Optional[ReportFilter] = None
    
    # بيانات التقرير
    sales_lines: List[SalesReportLine] = field(default_factory=list)
    sales_summary: Optional[SalesReportSummary] = None
    
    inventory_lines: List[InventoryReportLine] = field(default_factory=list)
    inventory_summary: Optional[InventoryReportSummary] = None
    
    financial_lines: List[FinancialReportLine] = field(default_factory=list)
    financial_summary: Optional[FinancialReportSummary] = None
    
    # الرسوم البيانية
    charts: List[ChartData] = field(default_factory=list)
    
    # معلومات التوليد
    generated_by: Optional[str] = None
    generated_at: Optional[datetime] = None
    format: ReportFormat = ReportFormat.PDF
    
    # ملاحظات
    notes: Optional[str] = None
    
    def __post_init__(self):
        """التهيئة بعد الإنشاء"""
        if not self.title and self.report_type:
            self.title = self._get_default_title()
        
        if not self.generated_at:
            self.generated_at = datetime.now()
    
    def _get_default_title(self) -> str:
        """الحصول على العنوان الافتراضي"""
        titles = {
            ReportType.SALES_SUMMARY: "تقرير ملخص المبيعات",
            ReportType.SALES_DETAILED: "تقرير المبيعات التفصيلي",
            ReportType.SALES_BY_PRODUCT: "تقرير المبيعات حسب المنتج",
            ReportType.SALES_BY_CUSTOMER: "تقرير المبيعات حسب العميل",
            ReportType.SALES_BY_CATEGORY: "تقرير المبيعات حسب الفئة",
            
            ReportType.INVENTORY_MOVEMENT: "تقرير حركة المخزون",
            ReportType.INVENTORY_VALUATION: "تقرير تقييم المخزون",
            ReportType.INVENTORY_AGING: "تقرير أعمار المخزون",
            ReportType.INVENTORY_TURNOVER: "تقرير دوران المخزون",
            
            ReportType.FINANCIAL_INCOME: "قائمة الدخل",
            ReportType.FINANCIAL_BALANCE: "الميزانية العمومية",
            ReportType.FINANCIAL_CASHFLOW: "قائمة التدفقات النقدية",
            ReportType.FINANCIAL_TRIAL_BALANCE: "ميزان المراجعة",
        }
        return titles.get(self.report_type, "تقرير")
    
    def get_total_lines(self) -> int:
        """الحصول على إجمالي السطور"""
        if self.sales_lines:
            return len(self.sales_lines)
        elif self.inventory_lines:
            return len(self.inventory_lines)
        elif self.financial_lines:
            return len(self.financial_lines)
        return 0
    
    def has_charts(self) -> bool:
        """التحقق من وجود رسوم بيانية"""
        return len(self.charts) > 0
    
    def get_period_description(self) -> str:
        """الحصول على وصف الفترة"""
        if not self.filters:
            return "غير محدد"
        
        if self.filters.start_date and self.filters.end_date:
            return f"من {self.filters.start_date} إلى {self.filters.end_date}"
        elif self.filters.period:
            return self.filters.period.value
        
        return "الكل"


@dataclass
class ReportTemplate:
    """قالب التقرير"""
    id: Optional[int] = None
    name: str = ""
    report_type: ReportType = ReportType.SALES_SUMMARY
    description: Optional[str] = None
    
    default_filters: Optional[ReportFilter] = None
    default_format: ReportFormat = ReportFormat.PDF
    
    include_charts: bool = True
    chart_types: List[ChartType] = field(default_factory=list)
    
    columns: List[str] = field(default_factory=list)
    group_by: Optional[str] = None
    sort_by: Optional[str] = None
    
    is_default: bool = False
    is_active: bool = True
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """التهيئة بعد الإنشاء"""
        if not self.created_at:
            self.created_at = datetime.now()
