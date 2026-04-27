"""
Models Module - نماذج البيانات
Data models and business logic for the application
Using Lazy Loading to improve performance
"""
import importlib

# Mapping of names to their respective modules
_MODELS_MAP = {
    # Core Models
    'Product': '.product',
    'ProductManager': '.product',
    'Customer': '.customer',
    'CustomerManager': '.customer',
    'Sale': '.sale',
    'SaleItem': '.sale',
    'SaleManager': '.sale',
    'SaleStatus': '.sale',
    'PaymentMethod': '.sale',
    'Supplier': '.supplier',
    'SupplierManager': '.supplier',
    'User': '.user',
    'UserManager': '.user',
    'UserRole': '.user',
    
    # Purchase & Inventory
    'Purchase': '.purchase',
    'PurchaseItem': '.purchase',
    'PurchaseManager': '.purchase',
    'PurchaseStatus': '.purchase',
    'PaymentStatus': '.purchase',
    'PurchaseOrder': '.purchase_order',
    'PurchaseOrderItem': '.purchase_order',
    'ReceivingNote': '.receiving_note',
    'ReceivingItem': '.receiving_note',
    'PhysicalCount': '.physical_count',
    'CountItem': '.physical_count',
    'ABCAnalysisResult': '.inventory_optimization',
    'ReorderRecommendation': '.inventory_optimization',
    'SafetyStockConfig': '.inventory_optimization',
    
    # Financial
    'Payment': '.payment',
    'PaymentManager': '.payment',
    'PaymentType': '.payment',
    'PaymentPlan': '.payment_plan',
    'PaymentInstallment': '.payment_plan',
    'Account': '.account',
    'ChartOfAccounts': '.account',
    'JournalEntry': '.journal_entry',
    'JournalLine': '.journal_entry',
    'Currency': '.currency',
    'ExchangeRate': '.currency',
    'CurrencyManager': '.currency',
    'Company': '.company',
    'UserCompany': '.company',
    'CompanyManager': '.company',
    
    # Reporting & Analytics
    'Report': '.report',
    'ReportData': '.report',
    'ReportTemplate': '.report',
    'ReportType': '.report',
    'ReportPeriod': '.report',
    'ReportFormat': '.report',
    'ExportFormat': '.report',
    'ChartType': '.report',
    'ReportFilter': '.report',
    'SalesReportLine': '.report',
    'SalesReportSummary': '.report',
    'InventoryReportLine': '.report',
    'InventoryReportSummary': '.report',
    'FinancialReportLine': '.report',
    'FinancialReportSummary': '.report',
    'ChartData': '.report',
    'DashboardData': '.dashboard',
    
    # Other Models
    'Quote': '.quote',
    'QuoteItem': '.quote',
    'ReturnInvoice': '.return_invoice',
    'ReturnItem': '.return_invoice',
    'Category': '.category',
    'CategoryManager': '.category',
    'Permission': '.permission',
    'Role': '.permission',
    'AuditLog': '.permission',
    'LoginHistory': '.permission',
    'SearchResult': '.search',
    'SearchQuery': '.search',
    'SearchFilter': '.search',
}

def __getattr__(name):
    if name in _MODELS_MAP:
        module_path = _MODELS_MAP[name]
        module = importlib.import_module(module_path, __package__)
        return getattr(module, name)
    
    # Special handling for pydantic_schemas (import all if requested)
    if name == "pydantic_schemas":
        try:
            return importlib.import_module('.pydantic_schemas', __package__)
        except ImportError:
            return None
            
    raise AttributeError(f"module {__name__} has no attribute {name}")

def __dir__():
    return sorted(list(_MODELS_MAP.keys()) + ['__doc__', '__file__', '__name__', '__package__', '__path__', '__spec__'])

__all__ = list(_MODELS_MAP.keys())
