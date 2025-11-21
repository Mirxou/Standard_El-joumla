"""
نماذج لوحات المعلومات ومؤشرات الأداء
Dashboard Models & KPIs
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import date, datetime


@dataclass
class KPI:
    """مؤشر أداء رئيسي"""
    key: str
    title: str
    value: float | int
    change: float = 0.0
    change_label: Optional[str] = None
    unit: Optional[str] = None
    color: str = "#2196F3"


@dataclass
class TimeSeriesPoint:
    label: str
    value: float
    ts: Optional[datetime] = None


@dataclass
class ChartSeries:
    name: str
    points: List[TimeSeriesPoint] = field(default_factory=list)
    color: Optional[str] = None


@dataclass
class DashboardData:
    period_start: date
    period_end: date

    kpis: List[KPI] = field(default_factory=list)

    sales_series: List[ChartSeries] = field(default_factory=list)
    top_products: List[Dict[str, Any]] = field(default_factory=list)

    inventory_value: float = 0.0
    low_stock_count: int = 0

    receivables_balance: float = 0.0
    payables_balance: float = 0.0

    active_customers: int = 0
    active_suppliers: int = 0

    notes: Optional[str] = None

    # Distribution dataset for donut/pie (list of {label, value})
    distribution: List[Dict[str, Any]] = field(default_factory=list)
