"""
UI Windows Module - نوافذ التطبيق الرئيسية
Using Lazy Loading to improve performance
"""

import importlib

# Mapping of names to their respective modules
_WINDOWS_MAP = {
    # Main window
    "MainWindow": ".main_window",
    # Reports windows
    "ReportsWindow": ".reports_window",
    "AdvancedReportsWindow": ".advanced_reports_window",
    # Account and payment windows
    "AccountsWindow": ".accounts_window",
    "PaymentDashboard": ".payment_dashboard",
    "PaymentPlansWindow": ".payment_plans_window",
    "AccountingWindow": ".accounting_window",
    # Inventory windows
    "PhysicalCountsWindow": ".physical_counts_window",
    "StockAdjustmentsWindow": ".stock_adjustments_window",
    "PurchaseOrdersWindow": ".purchase_orders_window",
    "ReturnsWindow": ".returns_window",
    "BatchTrackingWindow": ".batch_tracking_window",
    "SafetyStockWindow": ".safety_stock_window",
    "ReorderRecommendationsWindow": ".reorder_recommendations_window",
    "ABCAnalysisWindow": ".abc_analysis_window",
    "CycleCountWindow": ".cycle_count_window",
    # Sales windows
    "QuotesWindow": ".quotes_window",
    # Dashboard windows
    "DashboardWindow": ".dashboard_window",
    "SmartDashboardWindow": ".smart_dashboard_window",
    # Management windows
    "PermissionManagementWindow": ".permission_management_window",
    "TemplateEditorWindow": ".template_editor_window",
    "AdvancedSearchWindow": ".advanced_search_window",
}


def __getattr__(name):
    if name in _WINDOWS_MAP:
        module_path = _WINDOWS_MAP[name]
        module = importlib.import_module(module_path, __package__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


def __dir__():
    return sorted(
        list(_WINDOWS_MAP.keys()) + ["__doc__", "__file__", "__name__", "__package__", "__path__", "__spec__"]
    )


__all__ = list(_WINDOWS_MAP.keys())
