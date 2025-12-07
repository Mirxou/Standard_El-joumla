#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI Windows Module
نوافذ التطبيق الرئيسية
"""

# Main window
from .main_window import MainWindow

# Reports windows
from .reports_window import ReportsWindow
from .advanced_reports_window import AdvancedReportsWindow

# Account and payment windows
from .accounts_window import AccountsWindow
from .payment_dashboard import PaymentDashboard
from .payment_plans_window import PaymentPlansWindow
from .accounting_window import AccountingWindow

# Inventory windows
from .physical_counts_window import PhysicalCountsWindow
from .stock_adjustments_window import StockAdjustmentsWindow
from .purchase_orders_window import PurchaseOrdersWindow
from .returns_window import ReturnsWindow
from .batch_tracking_window import BatchTrackingWindow
from .safety_stock_window import SafetyStockWindow
from .reorder_recommendations_window import ReorderRecommendationsWindow
from .abc_analysis_window import ABCAnalysisWindow
from .cycle_count_window import CycleCountWindow

# Sales windows
from .quotes_window import QuotesWindow

# Dashboard windows
from .dashboard_window import DashboardWindow
from .smart_dashboard_window import SmartDashboardWindow

# Management windows
from .permission_management_window import PermissionManagementWindow
from .template_editor_window import TemplateEditorWindow
from .advanced_search_window import AdvancedSearchWindow

__all__ = [
    # Main window
    'MainWindow',
    
    # Reports windows
    'ReportsWindow',
    'AdvancedReportsWindow',
    
    # Account and payment windows
    'AccountsWindow',
    'PaymentDashboard',
    'PaymentPlansWindow',
    'AccountingWindow',
    
    # Inventory windows
    'PhysicalCountsWindow',
    'StockAdjustmentsWindow',
    'PurchaseOrdersWindow',
    'ReturnsWindow',
    'BatchTrackingWindow',
    'SafetyStockWindow',
    'ReorderRecommendationsWindow',
    'ABCAnalysisWindow',
    'CycleCountWindow',
    
    # Sales windows
    'QuotesWindow',
    
    # Dashboard windows
    'DashboardWindow',
    'SmartDashboardWindow',
    
    # Management windows
    'PermissionManagementWindow',
    'TemplateEditorWindow',
    'AdvancedSearchWindow',
]

