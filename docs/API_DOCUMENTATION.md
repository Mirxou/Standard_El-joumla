# 📚 API Documentation - توثيق API

## Overview

This document provides API documentation for the core components of the Logical Version ERP System.

---

## Core Modules

### Database Manager

**Location:** `src/core/database_manager.py`

#### `DatabaseManager`

Manages database connections and operations.

**Initialization:**
```python
from src.core.database_manager import DatabaseManager

db_manager = DatabaseManager(
    db_path="data/logical_release.db",
    encryption_password=None,
    pool_options=None,
    backup_options=None
)
```

**Key Methods:**

- `initialize() -> bool`: Initialize the database and create tables
- `get_connection()`: Get a database connection from the pool
- `close()`: Close all connections and cleanup
- `table_exists(table_name: str) -> bool`: Check if a table exists
- `execute_query(query, params=())`: Execute a query and return results as dictionaries
- `execute_scalar(query, params=())`: Execute a query and return a single value
- `backup_database(backup_path=None) -> bool`: Create a database backup
- `backup_database_encrypted(metadata=None) -> Optional[str]`: Create an encrypted backup
- `restore_database(backup_path) -> bool`: Restore from a backup
- `cleanup_old_backups(max_backups=30)`: Clean up old backup files
- `checkpoint_wal() -> bool`: Merge WAL files into main database
- `get_database_size_info() -> Dict[str, Any]`: Get database size information
- `vacuum_database() -> bool`: Clean and optimize database
- `cleanup_old_data(days=90, tables=None) -> Dict[str, int]`: Clean up old data
- `get_database_info() -> Dict[str, Any]`: Get database information

**Example:**
```python
db_manager = DatabaseManager()
if db_manager.initialize():
    # Get connection
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        results = cursor.fetchall()
    
    # Execute query (returns dictionaries)
    products = db_manager.execute_query("SELECT * FROM products WHERE category_id = ?", (1,))
    
    # Create backup
    db_manager.backup_database()
    
    # Cleanup WAL
    db_manager.checkpoint_wal()
    
    # Get size info
    size_info = db_manager.get_database_size_info()
    print(f"Database size: {size_info['database_size_mb']} MB")
    
    # Cleanup old data
    deleted = db_manager.cleanup_old_data(days=90)
    
    db_manager.close()
```

---

### Product Manager

**Location:** `src/models/product.py`

#### `ProductManager`

Manages product operations.

**Initialization:**
```python
from src.models.product import ProductManager

product_manager = ProductManager(db_manager)
```

**Key Methods:**

- `create_product(product: Product) -> Optional[int]`: Create a new product
- `get_product_by_id(product_id: int) -> Optional[Product]`: Get product by ID
- `get_product_by_barcode(barcode: str) -> Optional[Product]`: Get product by barcode
- `search_products(query: str) -> List[Product]`: Search products
- `update_product(product_id: int, data: Dict) -> bool`: Update product
- `delete_product(product_id: int) -> bool`: Delete product

**Example:**
```python
from src.models.product import Product

product = Product(
    name="منتج جديد",
    cost_price=100.0,
    selling_price=150.0,
    current_stock=50
)

product_id = product_manager.create_product(product)
product = product_manager.get_product_by_id(product_id)
```

---

### Math Utils

**Location:** `src/utils/math_utils.py`

Financial calculation utilities with Decimal precision.

**Key Functions:**

- `to_decimal(value) -> Decimal`: Safely convert any value to Decimal
- `calculate_line_total(quantity, unit_price, discount) -> Decimal`: Calculate line item total
- `calculate_subtotal(line_totals: List[Decimal]) -> Decimal`: Calculate subtotal
- `calculate_discount_amount(subtotal, discount, is_percentage=False) -> Decimal`: Calculate discount
- `calculate_tax_amount(subtotal, discount_amount, tax_rate) -> Decimal`: Calculate tax
- `calculate_grand_total(subtotal, discount_amount, tax_amount) -> Decimal`: Calculate grand total

**Example:**
```python
from src.utils.math_utils import (
    to_decimal,
    calculate_line_total,
    calculate_grand_total
)

quantity = to_decimal("5")
unit_price = to_decimal(100)
discount = to_decimal("10")

line_total = calculate_line_total(quantity, unit_price, discount)
grand_total = calculate_grand_total(
    subtotal=to_decimal(1000),
    discount_amount=to_decimal(100),
    tax_amount=to_decimal(135)
)
```

---

### Sales Manager

**Location:** `src/models/sale.py`

#### `SaleManager`

Manages sales and invoices.

**Initialization:**
```python
from src.models.sale import SaleManager

sale_manager = SaleManager(db_manager)
```

**Key Methods:**

- `create_sale(sale: Sale) -> Optional[int]`: Create a new sale
- `get_sale_by_id(sale_id: int) -> Optional[Sale]`: Get sale by ID
- `get_sales_by_date_range(start_date, end_date) -> List[Sale]`: Get sales in date range
- `update_sale_status(sale_id: int, status: SaleStatus) -> bool`: Update sale status

**Example:**
```python
from src.models.sale import Sale, SaleItem, SaleStatus

sale = Sale(
    customer_id=1,
    invoice_number="INV-001",
    items=[
        SaleItem(product_id=1, quantity=5, unit_price=100)
    ],
    status=SaleStatus.CONFIRMED
)

sale_id = sale_manager.create_sale(sale)
```

---

## UI Components

### Product Dialog

**Location:** `src/ui/dialogs/product_dialog.py`

#### `ProductDialog`

Dialog for adding/editing products.

**Initialization:**
```python
from src.ui.dialogs.product_dialog import ProductDialog

# Add new product
dialog = ProductDialog(db_manager, product=None, parent=parent_window)

# Edit existing product
product = product_manager.get_product_by_id(product_id)
dialog = ProductDialog(db_manager, product=product, parent=parent_window)

if dialog.exec() == QDialog.Accepted:
    # Product saved
    pass
```

**Signals:**

- `product_saved(product: Product)`: Emitted when product is saved

---

### Sales Dialog

**Location:** `src/ui/dialogs/sales_dialog.py`

#### `SalesDialog`

Dialog for creating/editing sales invoices.

**Initialization:**
```python
from src.ui.dialogs.sales_dialog import SalesDialog

# Create new sale
dialog = SalesDialog(db_manager, sale=None, parent=parent_window)

# Edit existing sale
sale = sale_manager.get_sale_by_id(sale_id)
dialog = SalesDialog(db_manager, sale=sale, parent=parent_window)

if dialog.exec() == QDialog.Accepted:
    # Sale completed
    pass
```

**Signals:**

- `sale_completed(sale: Sale)`: Emitted when sale is completed

---

### Config Manager

**Location:** `src/core/config_manager.py`

#### `ConfigManager`

Manages application configuration with support for environment variables and encryption.

**Initialization:**
```python
from src.core.config_manager import ConfigManager

config = ConfigManager()
config.load_config()
```

**Key Methods:**

- `get(key, default=None, use_env=True)`: Get a configuration value
- `set(key, value)`: Set a configuration value
- `save_config() -> bool`: Save configuration to file
- `load_config() -> bool`: Load configuration from file
- `validate_config() -> List[str]`: Validate configuration settings
- `get_database_path() -> str`: Get database path
- `get_backup_settings() -> Dict[str, Any]`: Get backup settings
- `get_email_settings() -> Dict[str, Any]`: Get email settings
- `get_api_settings() -> Dict[str, Any]`: Get API settings
- `get_company_settings() -> Dict[str, Any]`: Get company settings
- `get_templates_settings() -> Dict[str, Any]`: Get templates settings

**Example:**
```python
config = ConfigManager()
config.load_config()

# Get value
db_path = config.get('database.path')
theme = config.get('ui.theme', 'light')

# Set value
config.set('ui.theme', 'dark')
config.save_config()

# Get specialized settings
email_settings = config.get_email_settings()
api_settings = config.get_api_settings()

# Validate
errors = config.validate_config()
if errors:
    print("Configuration errors:", errors)
```

---

### Encryption Manager

**Location:** `src/core/encryption_manager.py`

#### `EncryptionManager`

Manages encryption for sensitive data and database files.

**Initialization:**
```python
from src.core.encryption_manager import EncryptionManager

encryption_manager = EncryptionManager("your_password")
```

**Key Methods:**

- `encrypt_data(data) -> bytes`: Encrypt data
- `decrypt_data(encrypted_data) -> bytes`: Decrypt data
- `encrypt_file(file_path, output_path=None) -> str`: Encrypt a file
- `decrypt_file(encrypted_file_path, output_path=None) -> str`: Decrypt a file
- `encrypt_database(db_path, password, backup_original=True) -> str`: Encrypt database
- `decrypt_database(encrypted_db_path, password, output_path=None) -> str`: Decrypt database
- `generate_secure_password(length=16) -> str`: Generate secure password
- `hash_password(password, salt=None) -> tuple`: Hash password for storage
- `verify_password(stored_password, stored_salt, provided_password) -> bool`: Verify password

**Example:**
```python
encryption_manager = EncryptionManager("master_password")

# Encrypt data
encrypted = encryption_manager.encrypt_data("sensitive data")

# Decrypt data
decrypted = encryption_manager.decrypt_data(encrypted)

# Encrypt database
encryption_manager.encrypt_database(
    db_path="data/database.db",
    password="your_password",
    backup_original=True
)

# Generate secure password
secure_password = EncryptionManager.generate_secure_password(length=16)
```

---

### Report Exporter

**Location:** `src/services/report_exporter.py`

#### `ReportExporter`

Generates and exports various types of reports.

**Initialization:**
```python
from src.services.report_exporter import ReportExporter

report_exporter = ReportExporter(db_manager)
```

**Key Methods:**

- `generate_report(report_type, filters) -> ReportData`: Generate a report
- `export_report(report_data, format, output_path) -> str`: Export report to file

**Example:**
```python
from src.models.report import ReportType, ReportFilter, ExportFormat
from datetime import datetime, timedelta

filters = ReportFilter(
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)

report_data = report_exporter.generate_report(
    ReportType.SALES_SUMMARY,
    filters
)

export_path = report_exporter.export_report(
    report_data=report_data,
    format=ExportFormat.PDF,
    output_path="reports/sales.pdf"
)
```

---

## Services

### Inventory Service

**Location:** `src/services/inventory_service.py`

#### `InventoryService`

High-level inventory operations.

**Key Methods:**

- `get_all_products(limit=None, offset=0) -> List[Product]`: Get products with pagination
- `search_products(query: str) -> List[Product]`: Search products
- `add_product(product: Product) -> int`: Add product
- `update_product(product_id: int, data: Dict) -> bool`: Update product
- `delete_product(product_id: int) -> bool`: Delete product

---

### Sales Service

**Location:** `src/services/sales_service.py`

#### `SalesService`

High-level sales operations.

**Key Methods:**

- `create_sale(sale_data: Dict) -> int`: Create sale
- `get_sales(filters: Dict) -> List[Sale]`: Get sales with filters
- `get_sale_summary(start_date, end_date) -> Dict`: Get sales summary

---

## Error Handling

All modules use custom exceptions from `src/core/exceptions.py`:

- `DatabaseException`: Database-related errors
- `ValidationError`: Data validation errors
- `NotFoundError`: Resource not found errors

**Example:**
```python
from src.core.exceptions import DatabaseException, NotFoundError

try:
    product = product_manager.get_product_by_id(product_id)
    if not product:
        raise NotFoundError(f"Product {product_id} not found")
except DatabaseException as e:
    logger.error(f"Database error: {e}")
```

---

## Best Practices

1. **Always use Decimal for financial calculations**
   ```python
   from src.utils.math_utils import to_decimal
   price = to_decimal(100.50)
   ```

2. **Use context managers for database connections**
   ```python
   with db_manager.get_connection() as conn:
       # Use connection
       pass
   ```

3. **Handle exceptions properly**
   ```python
   try:
       result = operation()
   except Exception as e:
       logger.error(f"Error: {e}")
       raise
   ```

4. **Use type hints**
   ```python
   def create_product(product: Product) -> Optional[int]:
       ...
   ```

---

## Additional Resources

- **[Configuration Guide](CONFIGURATION_GUIDE.md)** - Detailed configuration guide
- **[Database Management Guide](DATABASE_MANAGEMENT_GUIDE.md)** - Database management and optimization
- **[Security Guide](SECURITY_GUIDE.md)** - Security features and encryption
- **[Integration Guide](INTEGRATION_GUIDE.md)** - API and service integrations
- **[Reports Guide](REPORTS_GUIDE.md)** - Comprehensive reporting system

## Version

**API Version:** 5.3.0  
**Last Updated:** January 2025

