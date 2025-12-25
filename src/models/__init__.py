"""
Models Module - نماذج البيانات
Data models and business logic for the application
"""

# Core Models
from .product import Product, ProductManager
from .customer import Customer, CustomerManager
from .sale import Sale, SaleItem, SaleManager, SaleStatus, PaymentMethod
from .supplier import Supplier, SupplierManager
from .user import User, UserManager, UserRole

# Purchase & Inventory Models
from .purchase import Purchase, PurchaseItem, PurchaseManager, PurchaseStatus, PaymentStatus
from .purchase_order import PurchaseOrder, PurchaseOrderItem
from .receiving_note import ReceivingNote, ReceivingItem
from .physical_count import PhysicalCount, CountItem
from .inventory_optimization import ABCAnalysisResult, ReorderRecommendation, SafetyStockConfig

# Financial Models
from .payment import Payment, PaymentManager, PaymentType
from .payment_plan import PaymentPlan, PaymentInstallment
from .account import Account, ChartOfAccounts
from .journal_entry import JournalEntry, JournalLine
from .currency import Currency, ExchangeRate, CurrencyManager
from .company import Company, UserCompany, CompanyManager

# Reporting & Analytics
from .report import (
    Report, ReportData, ReportTemplate, ReportType, ReportPeriod,
    ReportFormat, ExportFormat, ChartType, ReportFilter,
    SalesReportLine, SalesReportSummary,
    InventoryReportLine, InventoryReportSummary,
    FinancialReportLine, FinancialReportSummary,
    ChartData
)
from .dashboard import DashboardData

# Other Models
from .quote import Quote, QuoteItem
from .return_invoice import ReturnInvoice, ReturnItem
from .category import Category, CategoryManager
from .permission import Permission, Role, User, AuditLog, LoginHistory
from .search import SearchResult, SearchQuery, SearchFilter
# Pydantic schemas are optional - import only if available
try:
    from .pydantic_schemas import *
except ImportError:
    pass

__all__ = [
    # Core Models
    'Product', 'ProductManager',
    'Customer', 'CustomerManager',
    'Sale', 'SaleItem', 'SaleManager', 'SaleStatus', 'PaymentMethod',
    'Supplier', 'SupplierManager',
    'User', 'UserManager', 'UserRole',
    
    # Purchase & Inventory
    'Purchase', 'PurchaseItem', 'PurchaseManager', 'PurchaseStatus', 'PaymentStatus',
    'PurchaseOrder', 'PurchaseOrderItem',
    'ReceivingNote', 'ReceivingItem',
    'PhysicalCount', 'CountItem',
    'ABCAnalysisResult', 'ReorderRecommendation', 'SafetyStockConfig',
    
    # Financial
    'Payment', 'PaymentManager', 'PaymentType',
    'PaymentPlan', 'PaymentInstallment',
    'Account', 'ChartOfAccounts',
    'JournalEntry', 'JournalLine',
    'Currency', 'ExchangeRate', 'CurrencyManager',
    'Company', 'UserCompany', 'CompanyManager',
    
    # Reporting & Analytics
    'Report', 'ReportData', 'ReportTemplate', 'ReportType', 'ReportPeriod',
    'ReportFormat', 'ExportFormat', 'ChartType', 'ReportFilter',
    'SalesReportLine', 'SalesReportSummary',
    'InventoryReportLine', 'InventoryReportSummary',
    'FinancialReportLine', 'FinancialReportSummary',
    'ChartData',
    'DashboardData',
    
    # Other Models
    'Quote', 'QuoteItem',
    'ReturnInvoice', 'ReturnItem',
    'Category', 'CategoryManager',
    'Permission', 'Role', 'User', 'AuditLog', 'LoginHistory',
    'SearchResult', 'SearchQuery', 'SearchFilter',
    
    # Pydantic Schemas (optional)
]

