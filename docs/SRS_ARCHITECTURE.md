# Software Requirements Specification (SRS) — Architecture & Gap Analysis
# وثيقة متطلبات البرمجيات — التحليل المعماري وتحليل الفجوات

**System / النظام:** Standard El-Joumla ERP/POS
**Version / الإصدار:** 1.0
**Date / التاريخ:** 2025-07-09
**Status / الحالة:** Active — Development Roadmap
**Classification / التصنيف:** Internal Technical Document / وثيقة تقنية داخلية

---

## Table of Contents / فهرس المحتويات

1. [Executive Summary / الملخص التنفيذي](#1-executive-summary--الملخص-التنفيذي)
2. [Area 1: Inventory & Products / المخزون والمنتجات](#2-area-1-inventory--products--المخزون-والمنتجات)
3. [Area 2: Sales & Customers / المبيعات والعملاء](#3-area-2-sales--customers--المبيعات-والعملاء)
4. [Area 3: Suppliers & Purchases / الموردون والمشتريات](#4-area-3-suppliers--purchases--الموردون-والمشتريات)
5. [Area 4: Accounting & Analytics / المحاسبة والتحليلات](#5-area-4-accounting--analytics--المحاسبة-والتحليلات)
6. [Area 5: Architecture & Infrastructure / البنية والبنية التحتية](#6-area-5-architecture--infrastructure--البنية-والبنية-التحتية)
7. [Consolidated Priority Matrix / مصفوفة الأولويات الموحدة](#7-consolidated-priority-matrix--مصفوفة-الأولويات-الموحدة)
8. [Implementation Roadmap / خارطة طريق التنفيذ](#8-implementation-roadmap--خارطة-طريق-التنفيذ)
9. [Acceptance Criteria / معايير القبول](#9-acceptance-criteria--معايير-القبول)
10. [Appendix / الملحق](#10-appendix--الملحق)

---

## 1. Executive Summary / الملخص التنفيذي

This document provides a comprehensive architectural gap analysis of the Standard El-Joumla ERP/POS system. It identifies 18 significant gaps across 5 functional domains, proposes concrete solutions with technical specifications, and establishes a prioritized implementation roadmap.

> توفر هذه الوثيقة تحليلاً معمارياً شاملاً لنظام الجملة القياسي للموارد المؤسسية ونقاط البيع. تحدد الوثيقة 18 فجوة كبيرة عبر 5 مجالات وظيفية، وتقترح حلولاً ملموسة مع مواصفات تقنية، وتؤسس خارطة طريق تنفيذ مرتبة حسب الأولوية.

### System Overview / نظرة عامة على النظام

| Attribute / السمة | Value / القيمة |
|---|---|
| **Architecture / البنية** | Dual: PySide6 Desktop + Next.js Web → FastAPI + SQLite |
| **Database / قاعدة البيانات** | SQLite with WAL mode, sync_queue for offline |
| **Auth / المصادقة** | JWT + WebSocket sessions |
| **Sync / المزامنة** | HybridDataService, DeltaSyncService, CloudSyncService |
| **Accounting / المحاسبة** | Full double-entry with chart of accounts |

---

## 2. Area 1: Inventory & Products / المخزون والمنتجات

### 2.1 Overview / نظرة عامة

The inventory module manages product catalog, stock levels, batch tracking, barcode/QR identification, and multi-warehouse operations. It serves as the backbone for sales, purchases, and accounting modules.

> تدير وحدة المخزون كتالوج المنتجات ومستويات المخزون وتتبع الدفعات وتحديد الباركود/QR والعمليات متعددة المستودعات. وهي تشكل العمود الفقري لوحدات المبيعات والمشتريات والمحاسبة.

### 2.2 Current Implementation / التنفيذ الحالي

| Feature / الميزة | Status | Details / التفاصيل |
|---|---|---|
| Product CRUD with categories, variants, bundles | ✅ | Full product lifecycle management |
| `products.barcode` UNIQUE column | ✅ | Barcode field stored and unique-constrained |
| `products.parent_product_id` and `conversion_factor` columns | ✅ | DB schema supports parent-child product relationships |
| `products.expiry_date` column | ✅ | Expiry date stored at product level |
| `batches` table with `expiry_date` | ✅ | Batch-level expiry tracking exists |
| `_check_expiry_alerts()` method | ✅ | Generates warnings for near-expiry products |
| `qrcode_service.py` | ✅ | QR code generation for products |
| Multi-warehouse with transfer stock | ✅ | Full warehouse management with stock transfers |
| Stock adjustments and cycle counts | ✅ | Inventory count workflows implemented |
| Safety stock and reorder alerts | ✅ | Reorder point notifications active |

### 2.3 Gaps & Missing Features / الفجوات والميزات المفقودة

#### Gap 1.1: Multi-Unit Conversion / تحويل الوحدات المتعددة

| Attribute | Value |
|---|---|
| **ID** | GAP-1.1 |
| **Severity / الخطورة** | ❌ Critical |
| **Arabic** | تحويل الوحدات المتعددة — أعمدة `parent_product_id` و `conversion_factor` موجودة في قاعدة البيانات ولكن لا يوجد كود خدمة يستخدمها |

**Impact / الأثر:** Without unit conversion, users cannot sell in retail units while purchasing in wholesale units (e.g., purchase by carton, sell by piece). This is a fundamental requirement for a wholesale (الجملة) ERP system. Pricing, stock deduction, and reporting are all incorrect when units differ.

> بدون تحويل الوحدات، لا يمكن للمستخدمين البيع بوحدات التجزئة بينما يشترون بوحدات الجملة (مثلاً: الشراء بالكرتون والبيع بالقطعة). هذا مطلب أساسي لنظام جملة.

**Current state:**
- `products.parent_product_id` → exists in schema, **never referenced in any service**
- `products.conversion_factor` → exists in schema, **never referenced in any service**
- No `unit_conversion_service.py` exists
- No conversion matrix table `(from_unit, to_unit, factor)`
- No pricing-per-unit logic

#### Gap 1.2: FEFO Batch Allocation / تخصيص الدفعات (أول ما ينتهي أولاً)

| Attribute | Value |
|---|---|
| **ID** | GAP-1.2 |
| **Severity / الخطورة** | ❌ Critical |
| **Arabic** | لا يوجد تخصيص تلقائي للدفعات حسب قاعدة FEFO أثناء المبيعات — يتم خصم المخزون كرقم مسطح بدون وعي بالدفعات |

**Impact / الأثر:** Selling products without FEFO allocation leads to expired stock remaining in warehouse while newer stock is sold first. This causes direct financial loss from write-offs and potential regulatory issues for perishable goods.

> بيع المنتجات بدون تخصيص FEFO يؤدي إلى بقاء المخزون منتهي الصلاحية في المستودع بينما يُباع المخزون الأحدث أولاً. هذا يسبب خسارة مالية مباشرة.

**Current state:**
- `batches.expiry_date` → stored ✅
- `_check_expiry_alerts()` → generates warnings ✅
- `sales_service.py` → deducts from `products.current_stock` as flat number ❌
- No FEFO sorting during sale ❌
- No batch-aware stock deduction ❌
- No batch reservation/allocation engine ❌

#### Gap 1.3: 1D Barcode Generation & Scanner Integration / توليد الباركود أحادي البُعد وتكامل الماسح

| Attribute | Value |
|---|---|
| **ID** | GAP-1.3 |
| **Severity / الخطورة** | ⚠️ High |
| **Arabic** | لا يوجد توليد لباركود أحادي البُعد (EAN-13, Code128) ولا تكامل لماسح الباركود في `hardware_service.py` |

**Impact / الأثر:** POS checkout speed is significantly reduced without barcode scanning. QR codes are not scannable by standard 1D laser scanners used in retail. This directly impacts checkout throughput.

> سرعة نقاط البيع تتأثر بشكل كبير بدون مسح الباركود. رموز QR غير قابلة للمسح بواسطة ماسحات الليزر أحادية البُعد القياسية.

**Current state:**
- `products.barcode` UNIQUE → field exists ✅
- `qrcode_service.py` → generates QR codes only ✅
- No EAN-13 generation ❌
- No Code128 generation ❌
- `hardware_service.py` → only customer display (VFD 2x20) ❌
- No barcode scanner HID/serial integration ❌
- No keyboard-wedge scanner support ❌

### 2.4 Proposed Solutions / الحلول المقترحة

#### Solution for GAP-1.1: Multi-Unit Conversion Service

```
📁 Proposed Files:
  src/services/unit_conversion_service.py
  src/models/unit_conversion.py
  migrations/036_create_unit_conversions.sql
```

**Database Schema:**

```sql
CREATE TABLE unit_conversions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    from_unit VARCHAR(50) NOT NULL,     -- e.g., 'carton'
    to_unit VARCHAR(50) NOT NULL,       -- e.g., 'piece'
    conversion_factor DECIMAL(18,6) NOT NULL, -- e.g., 24.0
    barcode VARCHAR(100),               -- unit-specific barcode
    sell_price DECIMAL(18,2),           -- price per this unit
    cost_price DECIMAL(18,2),           -- cost per this unit
    is_base_unit BOOLEAN DEFAULT FALSE, -- the smallest unit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, from_unit, to_unit)
);

CREATE INDEX idx_uc_product ON unit_conversions(product_id);
```

**Service Interface:**

```python
class UnitConversionService:
    def convert_quantity(self, product_id: int, qty: float,
                         from_unit: str, to_unit: str) -> float:
        """Convert quantity from one unit to another.
        تحويل الكمية من وحدة إلى أخرى."""

    def get_price_for_unit(self, product_id: int, unit: str) -> float:
        """Get selling price for a specific unit.
        الحصول على سعر البيع لوحدة محددة."""

    def get_base_unit_qty(self, product_id: int, qty: float,
                          unit: str) -> float:
        """Convert any unit to base unit for stock deduction.
        تحويل أي وحدة إلى الوحدة الأساسية لخصم المخزون."""

    def get_all_units(self, product_id: int) -> list[UnitConversion]:
        """List all available units for a product.
        عرض جميع الوحدات المتاحة لمنتج."""
```

**Integration Points:**
- `sales_service.py`: Call `get_base_unit_qty()` before stock deduction
- `purchase_service.py`: Store in purchase unit, convert for stock
- Pricing engine: Use `get_price_for_unit()` instead of flat `sell_price`
- Reports: Display quantities in user-selected unit

#### Solution for GAP-1.2: FEFO Batch Allocation Engine

```
📁 Proposed Files:
  src/services/batch_allocation_service.py
  migrations/037_add_batch_allocation.sql
```

**Database Schema:**

```sql
CREATE TABLE batch_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER REFERENCES sales(id),
    batch_id INTEGER REFERENCES batches(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    allocated_qty DECIMAL(18,6) NOT NULL,
    unit_cost DECIMAL(18,2) NOT NULL,  -- cost at time of allocation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add batch tracking to sale items
ALTER TABLE sale_items ADD COLUMN batch_id INTEGER REFERENCES batches(id);
ALTER TABLE sale_items ADD COLUMN batch_number VARCHAR(50);
```

**Service Interface:**

```python
class BatchAllocationService:
    def allocate_fefo(self, product_id: int, warehouse_id: int,
                      required_qty: float) -> list[BatchAllocation]:
        """Allocate batches using FEFO (First Expiry, First Out).
        تخصيص الدفعات باستخدام قاعدة أول ما ينتهي أولاً.
        Sorts batches by expiry_date ASC, allocates from oldest first.
        Raises InsufficientStockError if total available < required_qty."""

    def reserve_batch(self, batch_id: int, qty: float,
                      sale_id: int) -> BatchAllocation:
        """Reserve stock from a specific batch for a sale.
        حجز المخزون من دفعة محددة لعملية بيع."""

    def get_batch_stock(self, product_id: int,
                        warehouse_id: int) -> list[BatchStock]:
        """Get available stock grouped by batch.
        الحصول على المخزون المتاح مجمّع حسب الدفعة."""

    def auto_deduct_on_sale(self, sale_id: int) -> None:
        """Automatically deduct from allocated batches on sale completion.
        خصم تلقائي من الدفعات المخصصة عند إتمام البيع."""
```

**Core Algorithm (FEFO):**

```
1. SELECT * FROM batches
   WHERE product_id = ? AND warehouse_id = ?
   AND current_qty > 0 AND expiry_date > DATE('now')
   ORDER BY expiry_date ASC
2. For each batch in result:
   a. take = MIN(batch.current_qty, remaining_required)
   b. Create BatchAllocation(sale_id, batch.id, take)
   c. batch.current_qty -= take
   d. remaining_required -= take
   e. IF remaining_required == 0: BREAK
3. IF remaining_required > 0: RAISE InsufficientStockError
```

#### Solution for GAP-1.3: 1D Barcode & Scanner Integration

```
📁 Proposed Files:
  src/services/barcode_service.py
  src/services/scanner_service.py
  migrations/038_add_barcode_generation.sql
```

**Service Interface:**

```python
class BarcodeService:
    def generate_ean13(self, product_id: int) -> str:
        """Generate EAN-13 barcode with valid check digit.
        توليد باركود EAN-13 مع رقم تحقق صالح."""

    def generate_code128(self, value: str) -> Image:
        """Generate Code128 barcode image.
        توليد صورة باركود Code128."""

    def print_barcode_label(self, product_id: int,
                           label_format: str = '30x20mm') -> None:
        """Print barcode label to configured label printer.
        طباعة ملصق باركود على طابعة الملصقات المُعدة."""

class ScannerService:
    def __init__(self, connection_type: str = 'hid'):
        """Initialize scanner: 'hid', 'serial', or 'keyboard_wedge'.
        تهيئة الماسح: 'hid' أو 'serial' أو 'keyboard_wedge'."""

    def start_listening(self, callback: Callable) -> None:
        """Start listening for scanner input.
        بدء الاستماع لمدخلات الماسح."""

    def stop_listening(self) -> None:
        """Stop scanner listener.
        إيقاف مستمع الماسح."""

    def on_scan(self, barcode: str) -> Product:
        """Handle scanned barcode, return matched product.
        معالجة الباركود الممسوح وإرجاع المنتج المطابق."""
```

**Hardware Integration in `hardware_service.py`:**

```python
# Extend existing hardware_service.py
class HardwareService:
    # Existing
    customer_display: CustomerDisplayService  # ✅

    # Proposed additions
    barcode_scanner: ScannerService           # NEW
    receipt_printer: ESCPOSPrinterService     # NEW (see GAP-2.2)
    cash_drawer: CashDrawerService            # NEW (see GAP-2.2)
    label_printer: LabelPrinterService        # NEW
```

### 2.5 Priority Assessment / تقييم الأولوية

| Gap ID | Feature / الميزة | Priority | Effort | Dependencies |
|---|---|---|---|---|
| GAP-1.1 | Multi-Unit Conversion / تحويل الوحدات | 🔴 Critical | 5 days | Product model, sales service, purchase service |
| GAP-1.2 | FEFO Batch Allocation / تخصيص الدفعات | 🔴 Critical | 7 days | Batch model, sales service, inventory service |
| GAP-1.3 | 1D Barcode & Scanner / الباركود والماسح | 🟠 High | 4 days | Hardware service, product model |

---

## 3. Area 2: Sales & Customers / المبيعات والعملاء

### 3.1 Overview / نظرة عامة

The sales module handles POS operations, customer management, credit sales, invoice generation, and hardware integration. It is the primary revenue-facing module of the system.

> تتعامل وحدة المبيعات مع عمليات نقاط البيع وإدارة العملاء والمبيعات الآجلة وتوليد الفواتير وتكامل الأجهزة. وهي الوحدة الرئيسية المواجهة للإيرادات.

### 3.2 Current Implementation / التنفيذ الحالي

| Feature / الميزة | Status | Details / التفاصيل |
|---|---|---|
| Full sales CRUD with items, discounts, taxes | ✅ | Complete sale lifecycle |
| Customer management with credit fields | ✅ | `credit_limit`, `current_balance`, `available_credit` property |
| Invoice generation (PDF/Qt) | ✅ | Multiple print services available |
| POS session start/end | ✅ | `start_pos_session()`, `end_pos_session()` in sales_service.py |
| Customer display (VFD 2x20) | ✅ | `hardware_service.py` handles customer-facing displays |
| Returns with multiple refund methods | ✅ | Full return invoice workflow |
| Quotes and quotations | ✅ | Quote-to-sale conversion |
| Payment plans and installments | ✅ | Flexible payment scheduling |

### 3.3 Gaps & Missing Features / الفجوات والميزات المفقودة

#### Gap 2.1: Credit Limit Enforcement / تطبيق حد الائتمان

| Attribute | Value |
|---|---|
| **ID** | GAP-2.1 |
| **Severity / الخطورة** | ❌ Critical |
| **Arabic** | لا يوجد تحقق من حد الائتمان قبل السماح ببيع آجل — أعمدة `credit_limit` و `current_balance` موجودة لكن `sales_service.py` لا يستخدمها |

**Impact / الأثر:** Without credit limit enforcement, customers can accumulate unlimited debt, leading to bad debts and cash flow problems. This is a critical financial control gap.

> بدون تطبيق حد الائتمان، يمكن للعملاء تراكم ديون غير محدودة، مما يؤدي إلى ديون معدومة ومشاكل في التدفق النقدي.

**Current state:**
- `customers.credit_limit` → column exists ✅
- `customers.current_balance` → column exists ✅
- `customers.available_credit` → property exists ✅
- `sales_service.py` → **does NOT check** `credit_limit` before credit sale ❌
- No AR aging report ❌
- No credit hold mechanism ❌
- No credit override with authorization ❌

#### Gap 2.2: POS Hardware — Receipt Printer, Cash Drawer, Scanner / أجهزة نقاط البيع

| Attribute | Value |
|---|---|
| **ID** | GAP-2.2 |
| **Severity / الخطورة** | ❌ Critical |
| **Arabic** | لا يوجد تكامل لطابعة الإيصالات (ESC/POS) أو درج النقدية أو ماسح الباركود — فقط شاشة العملاء (VFD 2x20) |

**Impact / الأثر:** A POS system without receipt printing and cash drawer control is incomplete for retail operations. This prevents deployment in actual stores.

> نظام نقاط البيع بدون طباعة إيصالات والتحكم في درج النقدية غير مكتمل لعمليات التجزئة.

**Current state:**
- `hardware_service.py` → only customer display (VFD 2x20) ✅/❌
- Multiple print services → output PDF/Qt, **NOT** ESC/POS ❌
- No ESC/POS thermal printer integration ❌
- No cash drawer kick command ❌
- No barcode scanner integration ❌ (see GAP-1.3)
- No pole display beyond basic VFD ❌

#### Gap 2.3: Shift Management — Cash Reconciliation & Handover / إدارة الورديات

| Attribute | Value |
|---|---|
| **ID** | GAP-2.3 |
| **Severity / الخطورة** | ⚠️ High |
| **Arabic** | لا يوجد تسوية نقدية ولا تسليم وردية ولا مبيعات مرتبطة بالجلسة ولا واجهة مستخدم لإدارة الورديات |

**Impact / الأثر:** Without proper shift management, cash discrepancies cannot be tracked to specific cashiers, and there is no accountability for cash handling during shift transitions.

> بدون إدارة ورديات سليمة، لا يمكن تتبع فروق النقدية إلى صرافين محددين، ولا توجد مساءلة عن التعامل مع النقد أثناء انتقال الورديات.

**Current state:**
- `start_pos_session()` / `end_pos_session()` → exist ✅
- `pos_sessions` table → created dynamically (not in base schema) ⚠️
- No cash reconciliation (expected vs. actual cash) ❌
- No shift handover workflow ❌
- No session-linked sales (sales not tagged with session_id) ❌
- No UI for shift management ❌
- No shift summary report ❌

### 3.4 Proposed Solutions / الحلول المقترحة

#### Solution for GAP-2.1: Credit Limit Enforcement & AR Aging

```
📁 Proposed Files:
  src/services/credit_service.py
  src/services/ar_aging_service.py
  migrations/039_add_credit_management.sql
```

**Database Schema:**

```sql
-- Credit management tables
CREATE TABLE credit_holds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    hold_reason VARCHAR(200) NOT NULL,
    held_by INTEGER REFERENCES users(id),
    held_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    released_at TIMESTAMP,
    released_by INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE
);

-- Add session linking to sales
ALTER TABLE sales ADD COLUMN pos_session_id INTEGER REFERENCES pos_sessions(id);
ALTER TABLE customers ADD COLUMN credit_status VARCHAR(20) DEFAULT 'active';
-- credit_status: 'active', 'on_hold', 'over_limit'
```

**Service Interface:**

```python
class CreditService:
    def check_credit_available(self, customer_id: int,
                               sale_amount: float) -> CreditCheckResult:
        """Check if customer has sufficient credit for sale.
        التحقق من وجود ائتمان كافٍ للعميل للبيع.
        Returns: CreditCheckResult(available, over_limit_by, can_override)"""

    def enforce_credit_limit(self, customer_id: int,
                             sale_amount: float) -> None:
        """Enforce credit limit before allowing sale.
        تطبيق حد الائتمان قبل السماح بالبيع.
        Raises CreditLimitExceededError if over limit.
        Allows override with manager authorization."""

    def place_credit_hold(self, customer_id: int,
                          reason: str, user_id: int) -> None:
        """Place customer on credit hold.
        وضع العميل في حالة توقف ائتماني."""

    def get_ar_aging(self, as_of_date: date = None) -> ARAgingReport:
        """Generate AR aging report (30/60/90/120+ days).
        إنشاء تقرير تقادم الذمم المدينة."""

class ARAgingService:
    def get_aging_buckets(self, customer_id: int) -> AgingBuckets:
        """Get aging buckets for a specific customer.
        الحصول على فترات التقادم لعميل محدد.
        Returns: {current: X, 30_days: Y, 60_days: Z, 90_days: W, 120_plus: V}"""

    def get_customer_statement(self, customer_id: int,
                               from_date: date, to_date: date) -> Statement:
        """Generate customer account statement.
        إنشاء كشف حساب العميل."""
```

**Integration in `sales_service.py`:**

```python
# Before creating a sale on credit:
if payment_method == 'credit':
    credit_service = CreditService(db)
    credit_service.enforce_credit_limit(customer_id, total_amount)
    # If we reach here, credit is available or override was authorized
```

#### Solution for GAP-2.2: ESC/POS Hardware Integration

```
📁 Proposed Files:
  src/services/escpos_printer_service.py
  src/services/cash_drawer_service.py
  src/services/scanner_service.py  (covered in GAP-1.3)
  migrations/040_add_hardware_config.sql
```

**Database Schema:**

```sql
CREATE TABLE hardware_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_type VARCHAR(50) NOT NULL,  -- 'receipt_printer', 'cash_drawer', 'scanner', 'label_printer'
    connection_type VARCHAR(20) NOT NULL, -- 'usb', 'serial', 'network', 'bluetooth'
    connection_params JSON,              -- {port: 'COM3', baud_rate: 9600} or {ip: '192.168.1.100', port: 9100}
    device_name VARCHAR(100),
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Service Interface:**

```python
class ESCPOSPrinterService:
    """Thermal receipt printer using ESC/POS protocol.
    طابعة الإيصالات الحرارية باستخدام بروتوكول ESC/POS."""

    def __init__(self, config: HardwareConfig):
        """Initialize printer from hardware_config.
        تهيئة الطابعة من إعدادات الأجهزة."""

    def print_receipt(self, sale: Sale) -> None:
        """Print full receipt for a sale.
        طباعة إيصال كامل لعملية بيع."""

    def print_x_report(self, session: POSSession) -> None:
        """Print X-report (mid-shift summary).
        طباعة تقرير X (ملخص منتصف الوردية)."""

    def print_z_report(self, session: POSSession) -> None:
        """Print Z-report (end-of-shift summary).
        طباعة تقرير Z (ملخص نهاية الوردية)."""

    def open_cash_drawer(self) -> None:
        """Send pulse to open cash drawer.
        إرسال نبضة لفتح درج النقدية."""

    def cut_paper(self, partial: bool = False) -> None:
        """Cut receipt paper.
        قطع ورق الإيصال."""

class CashDrawerService:
    """Cash drawer control service.
    خدمة التحكم في درج النقدية."""

    def open(self) -> None:
        """Open cash drawer via printer kick or direct GPIO.
        فتح درج النقدية عبر نبضة الطابعة أو GPIO مباشر."""

    def check_status(self) -> DrawerStatus:
        """Check if drawer is open/closed.
        التحقق من حالة الدرج (مفتوح/مغلق)."""
```

**ESC/POS Receipt Template:**

```
================================
     Standard El-Joumla
     نقاط البيع - الجملة
================================
Date: 2025-07-09 14:30
Cashier: Ahmed  Shift: #12
--------------------------------
Item          Qty   Price  Total
--------------------------------
Product A      2   15.00  30.00
Product B      1   25.00  25.00
--------------------------------
Subtotal:                55.00
Tax (15%):                8.25
--------------------------------
TOTAL:                   63.25
--------------------------------
Payment: Cash            63.25
================================
Thank you! / شكراً لكم!
```

#### Solution for GAP-2.3: Shift Management System

```
📁 Proposed Files:
  src/services/shift_service.py
  migrations/041_create_shift_management.sql
```

**Database Schema:**

```sql
-- Proper pos_sessions table (replace dynamic creation)
CREATE TABLE pos_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id INTEGER REFERENCES warehouses(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    shift_number INTEGER NOT NULL,
    opening_cash DECIMAL(18,2) DEFAULT 0,
    closing_cash DECIMAL(18,2),
    expected_closing DECIMAL(18,2),
    cash_difference DECIMAL(18,2),        -- closing_cash - expected_closing
    status VARCHAR(20) DEFAULT 'open',    -- 'open', 'closed', 'suspended'
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    handover_to INTEGER REFERENCES users(id),
    handover_note TEXT,
    closing_note TEXT,
    UNIQUE(warehouse_id, shift_number)
);

-- Cash reconciliation events
CREATE TABLE cash_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES pos_sessions(id),
    event_type VARCHAR(30) NOT NULL,  -- 'cash_in', 'cash_out', 'sale', 'refund', 'drop', 'pickup'
    amount DECIMAL(18,2) NOT NULL,
    reference_id INTEGER,             -- sale_id, purchase_id, etc.
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ensure sales are linked to sessions
ALTER TABLE sales ADD COLUMN pos_session_id INTEGER REFERENCES pos_sessions(id);
```

**Service Interface:**

```python
class ShiftService:
    def open_shift(self, warehouse_id: int, user_id: int,
                   opening_cash: float) -> POSSession:
        """Open a new shift with starting cash.
        فتح وردية جديدة مع النقدية الافتتاحية."""

    def close_shift(self, session_id: int, closing_cash: float,
                    note: str = None) -> ShiftSummary:
        """Close shift with cash count and reconciliation.
        إغلاق الوردية مع عد النقدية والتسوية.
        Calculates: expected_closing, cash_difference, generates Z-report."""

    def handover(self, session_id: int, to_user_id: int,
                 cash_count: float, note: str = None) -> POSSession:
        """Hand over shift to another cashier.
        تسليم الوردية إلى صراف آخر.
        Closes current shift, opens new shift for receiving user."""

    def record_cash_event(self, session_id: int,
                          event_type: str, amount: float,
                          note: str = None) -> None:
        """Record cash in/out/drop/pickup event.
        تسجيل حدث نقدي (إيداع/سحب/إسقاط/رفع)."""

    def get_shift_summary(self, session_id: int) -> ShiftSummary:
        """Get complete shift summary for Z-report.
        الحصول على ملخص الوردية الكامل لتقرير Z."""

    def get_active_session(self, warehouse_id: int,
                           user_id: int) -> POSSession:
        """Get currently active session for user/warehouse.
        الحصول على الجلسة النشطة حالياً."""
```

### 3.5 Priority Assessment / تقييم الأولوية

| Gap ID | Feature / الميزة | Priority | Effort | Dependencies |
|---|---|---|---|---|
| GAP-2.1 | Credit Limit Enforcement / تطبيق حد الائتمان | 🔴 Critical | 4 days | Customer model, sales service |
| GAP-2.2 | ESC/POS Hardware / أجهزة نقاط البيع | 🔴 Critical | 6 days | Hardware service, print services |
| GAP-2.3 | Shift Management / إدارة الورديات | 🟠 High | 5 days | POS session model, sales service |

---

## 4. Area 3: Suppliers & Purchases / الموردون والمشتريات

### 4.1 Overview / نظرة عامة

The procurement module manages supplier relationships, purchase orders, goods receiving, supplier payments, and purchase returns. It ensures supply chain continuity and controls payables.

> تدير وحدة المشتريات علاقات الموردين وأوامر الشراء واستلام البضائع ومدفوعات الموردين ومرتجعات المشتريات.

### 4.2 Current Implementation / التنفيذ الحالي

| Feature / الميزة | Status | Details / التفاصيل |
|---|---|---|
| Supplier CRUD with payment terms & credit | ✅ | `payment_terms`, `credit_limit`, `current_balance` |
| Purchase orders with full lifecycle | ✅ | Draft → Approved → Sent → Received → Closed |
| Receiving notes | ✅ | Goods receiving with batch tracking |
| Supplier evaluation | ✅ | Performance scoring system |
| `create_supplier_payment()` in PaymentService | ✅ | Payment creation exists |
| Return Invoice model (SALE_RETURN, PURCHASE_RETURN) | ✅ | Multiple refund methods, restockable flag |
| ReturnService | ✅ | Return processing service |
| `purchases.paid_amount`, `remaining_amount`, `payment_status` | ✅ | Payment tracking fields exist |

### 4.3 Gaps & Missing Features / الفجوات والميزات المفقودة

#### Gap 3.1: Automatic FIFO Payment Allocation / تخصيص المدفوعات تلقائياً حسب FIFO

| Attribute | Value |
|---|---|
| **ID** | GAP-3.1 |
| **Severity / الخطورة** | ⚠️ High |
| **Arabic** | لا يوجد تخصيص تلقائي للمدفوعات الجزئية حسب قاعدة FIFO (أول فاتورة غير مدفوعة بالكامل تحصل على الدفعة أولاً) |

**Impact / الأثر:** Without automatic FIFO allocation, partial payments may be applied inconsistently, leading to incorrect aging reports, disputed balances with suppliers, and audit trail gaps.

> بدون تخصيص FIFO تلقائي، قد تُطبق المدفوعات الجزئية بشكل غير متسق، مما يؤدي إلى تقارير تقادم غير صحيحة وأرصدة متنازع عليها.

**Current state:**
- `create_supplier_payment()` → exists but no auto-allocation ✅/❌
- `purchases.payment_status` → tracked per purchase ✅
- `purchases.remaining_amount` → tracked ✅
- No FIFO allocation algorithm ❌
- No payment-to-purchase linking table ❌
- No aging report for payables ❌

#### Gap 3.2: Purchase Return Workflow & Automatic Stock Restoration / سير عمل مرتجع المشتريات واستعادة المخزون التلقائية

| Attribute | Value |
|---|---|
| **ID** | GAP-3.2 |
| **Severity / الخطورة** | ⚠️ High |
| **Arabic** | سير عمل مرتجع المشتريات ضئيل — قد لا تكون استعادة المخزون تلقائية عند الموافقة على المرتجع |

**Impact / الأثر:** If stock is not automatically restored (or deducted) on purchase return approval, inventory levels become inaccurate. Manual correction is error-prone and leads to discrepancies.

> إذا لم تُستعاد المخزون تلقائياً عند الموافقة على مرتجع المشتريات، تصبح مستويات المخزون غير دقيقة.

**Current state:**
- `ReturnInvoice` model → fully implemented ✅
- `PURCHASE_RETURN` type → exists ✅
- `restockable` flag → exists ✅
- Stock restoration on approval → **may not be automatic** ⚠️
- Purchase return workflow → **minimal** ❌
- No supplier credit/debit note generation ❌
- No return-to-PO linking ❌

### 4.4 Proposed Solutions / الحلول المقترحة

#### Solution for GAP-3.1: FIFO Payment Allocation Engine

```
📁 Proposed Files:
  src/services/payment_allocation_service.py
  src/services/ap_aging_service.py
  migrations/042_create_payment_allocations.sql
```

**Database Schema:**

```sql
CREATE TABLE payment_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id INTEGER NOT NULL REFERENCES payments(id),
    purchase_id INTEGER NOT NULL REFERENCES purchases(id),
    allocated_amount DECIMAL(18,2) NOT NULL,
    allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(payment_id, purchase_id)
);

CREATE INDEX idx_pa_purchase ON payment_allocations(purchase_id);
CREATE INDEX idx_pa_payment ON payment_allocations(payment_id);
```

**Service Interface:**

```python
class PaymentAllocationService:
    def allocate_fifo(self, supplier_id: int,
                      payment_amount: float) -> list[PaymentAllocation]:
        """Allocate payment to oldest unpaid purchases first (FIFO).
        تخصيص الدفعة لأقدم المشتريات غير المدفوعة أولاً.
        Algorithm:
        1. Get all purchases for supplier WHERE payment_status != 'paid'
           ORDER BY purchase_date ASC
        2. For each purchase:
           allocate = MIN(purchase.remaining_amount, remaining_payment)
           Create PaymentAllocation(payment_id, purchase.id, allocate)
           purchase.remaining_amount -= allocate
           purchase.paid_amount += allocate
           Update payment_status accordingly
           remaining_payment -= allocate
           IF remaining_payment == 0: BREAK
        3. Return list of allocations"""

    def get_unallocated_amount(self, payment_id: int) -> float:
        """Get any unallocated portion of a payment.
        الحصول على أي جزء غير مخصص من الدفعة."""

    def reallocate(self, payment_id: int,
                   new_allocations: list) -> None:
        """Reallocate payment (requires authorization).
        إعادة تخصيص الدفعة (تتطلب تصريحاً)."""

class APAgingService:
    def get_aging_buckets(self, supplier_id: int = None) -> APAgingReport:
        """Generate AP aging report (30/60/90/120+ days).
        إنشاء تقرير تقادم الذمم الدائنة."""
```

#### Solution for GAP-3.2: Purchase Return Workflow Enhancement

```
📁 Proposed Files:
  src/services/purchase_return_service.py
  migrations/043_enhance_purchase_returns.sql
```

**Database Schema:**

```sql
-- Link returns to original purchase
ALTER TABLE return_invoices ADD COLUMN original_purchase_id INTEGER REFERENCES purchases(id);
ALTER TABLE return_invoices ADD COLUMN supplier_credit_note_number VARCHAR(50);

-- Return approval workflow
CREATE TABLE return_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    return_id INTEGER NOT NULL REFERENCES return_invoices(id),
    approver_id INTEGER NOT NULL REFERENCES users(id),
    approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    stock_restored BOOLEAN DEFAULT FALSE,
    credit_note_generated BOOLEAN DEFAULT FALSE,
    notes TEXT
);
```

**Service Interface:**

```python
class PurchaseReturnService:
    def create_purchase_return(self, purchase_id: int,
                               items: list[ReturnItem],
                               reason: str) -> ReturnInvoice:
        """Create purchase return from original purchase.
        إنشاء مرتجع مشتريات من عملية الشراء الأصلية."""

    def approve_return(self, return_id: int,
                       approver_id: int,
                       restock: bool = True) -> None:
        """Approve purchase return with automatic stock restoration.
        الموافقة على مرتجع المشتريات مع استعادة تلقائية للمخزون.
        If restock=True:
          - For each return item:
            - IF restockable: Add qty back to product.current_stock
            - Update batch stock if batch_id specified
          - Create supplier credit note
          - Update purchase.remaining_amount"""

    def generate_credit_note(self, return_id: int) -> CreditNote:
        """Generate supplier credit/debit note.
        إنشاء إشعار دائن/مدين للمورد."""
```

### 4.5 Priority Assessment / تقييم الأولوية

| Gap ID | Feature / الميزة | Priority | Effort | Dependencies |
|---|---|---|---|---|
| GAP-3.1 | FIFO Payment Allocation / تخصيص المدفوعات FIFO | 🟠 High | 4 days | Payment service, purchase model |
| GAP-3.2 | Purchase Return Workflow / سير عمل مرتجع المشتريات | 🟠 High | 5 days | Return service, inventory service, accounting service |

---

## 5. Area 4: Accounting & Analytics / المحاسبة والتحليلات

### 5.1 Overview / نظرة عامة

The accounting module provides financial record-keeping, reporting, and analytics. It includes double-entry bookkeeping, cost tracking, profit calculation, and financial statement generation.

> توفر وحدة المحاسبة حفظ السجلات المالية وإعداد التقارير والتحليلات. تشمل القيد المزدوج وتتبع التكاليف وحساب الأرباح وإنشاء القوائم المالية.

### 5.2 Current Implementation / التنفيذ الحالي

| Feature / الميزة | Status | Details / التفاصيل |
|---|---|---|
| Full double-entry bookkeeping | ✅ | `chart_of_accounts`, `general_journal`, `journal_lines` tables |
| Balanced journal entries | ✅ | Debit = Credit validation enforced |
| Trial balance | ✅ | `AccountingService.get_trial_balance()` |
| Income statement | ✅ | `AccountingService.get_income_statement()` |
| Financial position (balance sheet) | ✅ | Statement of financial position |
| `financial_transactions` with `operating_expenses` category | ✅ | Expense transactions tracked |
| `payments` with `expense` type | ✅ | Expense payments recorded |
| Simple profit calculation (selling - cost) | ✅ | Standard costing with single `cost_price` |

### 5.3 Gaps & Missing Features / الفجوات والميزات المفقودة

#### Gap 4.1: Costing Methods (FIFO/LIFO/Moving Average) / طرق التسعير

| Attribute | Value |
|---|---|
| **ID** | GAP-4.1 |
| **Severity / الخطورة** | ❌ Critical |
| **Arabic** | يستخدم النظام تكلفة معيارية بسيطة (سعر تكلفة واحد لكل منتج) — لا يوجد FIFO أو LIFO أو المتوسط المتحرك — لا يوجد إعداد لطريقة التسعير |

**Impact / الأثر:** Using a single cost_price per product gives inaccurate profit margins when purchase prices fluctuate. FIFO/LIFO/Moving Average are required by accounting standards (IFRS/GAAP) for proper COGS calculation and inventory valuation.

> استخدام سعر تكلفة واحد لكل منتج يعطي هوامش ربح غير دقيق عندما تتقلب أسعار الشراء. طرق FIFO/LIFO/Mتوسط المتحرك مطلوبة حسب معايير المحاسبة.

**Current state:**
- `products.cost_price` → single field ✅
- Profit = `selling_price - cost_price` → simplistic ❌
- No `costing_method` configuration ❌
- No cost layer tracking ❌
- No Moving Average recalculation ❌
- No FIFO cost layer consumption ❌

#### Gap 4.2: Operating Expense Management / إدارة المصروفات التشغيلية

| Attribute | Value |
|---|---|
| **ID** | GAP-4.2 |
| **Severity / الخطورة** | ⚠️ High |
| **Arabic** | لا توجد واجهة مستخدم مخصصة لإدارة المصروفات ولا إضافة/تعديل/حذف فئات المصروفات ولا مصروفات متكررة ولا سير عمل موافقة المصروفات |

**Impact / الأثر:** Without proper expense management, operating costs are tracked informally, making budget control, expense analysis, and financial planning unreliable.

> بدون إدارة مصروفات سليمة، يتم تتبع التكاليف التشغيلية بشكل غير رسمي، مما يجعل التحكم في الميزانية وتحليل المصروفات غير موثوق.

**Current state:**
- `financial_transactions` with `'operating_expenses'` category → exists ✅
- `payments` with `'expense'` type → exists ✅
- `AccountingService.get_income_statement()` → includes expenses ✅
- No dedicated expense management UI ❌
- No expense categories CRUD ❌
- No recurring expenses ❌
- No expense approval workflow ❌
- No budget vs. actual tracking ❌

### 5.4 Proposed Solutions / الحلول المقترحة

#### Solution for GAP-4.1: Multi-Method Costing Engine

```
📁 Proposed Files:
  src/services/costing_service.py
  src/models/cost_layer.py
  migrations/044_create_costing_system.sql
```

**Database Schema:**

```sql
-- Costing method configuration per product
ALTER TABLE products ADD COLUMN costing_method VARCHAR(20) DEFAULT 'moving_average';
-- costing_method: 'fifo', 'lifo', 'moving_average', 'standard', 'specific_identification'

-- Cost layers for FIFO/LIFO tracking
CREATE TABLE cost_layers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    warehouse_id INTEGER REFERENCES warehouses(id),
    purchase_id INTEGER REFERENCES purchases(id),
    batch_id INTEGER REFERENCES batches(id),
    layer_date TIMESTAMP NOT NULL,
    qty_in DECIMAL(18,6) NOT NULL,        -- quantity added to layer
    qty_remaining DECIMAL(18,6) NOT NULL, -- quantity still available
    unit_cost DECIMAL(18,2) NOT NULL,     -- cost per unit at this layer
    total_cost DECIMAL(18,2) NOT NULL,    -- qty_in * unit_cost
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cl_product ON cost_layers(product_id);
CREATE INDEX idx_cl_date ON cost_layers(layer_date);

-- Costing history for audit trail
CREATE TABLE costing_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    costing_method VARCHAR(20) NOT NULL,
    old_cost DECIMAL(18,2),
    new_cost DECIMAL(18,2),
    qty_changed DECIMAL(18,6),
    reference_type VARCHAR(20),  -- 'purchase', 'sale', 'return', 'adjustment'
    reference_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Service Interface:**

```python
class CostingService:
    def calculate_cogs(self, product_id: int, qty: float,
                       warehouse_id: int = None) -> COGSResult:
        """Calculate COGS using product's costing method.
        حساب تكلفة البضاعة المباعة باستخدام طريقة تسعير المنتج.
        Dispatches to: _calc_fifo, _calc_lifo, _calc_moving_avg, _calc_standard"""

    def _calc_fifo(self, product_id: int, qty: float) -> COGSResult:
        """FIFO: Consume from oldest cost layers first.
        FIFO: الاستهلاك من أقدم طبقات التكلفة أولاً.
        1. SELECT cost_layers WHERE product_id=? AND qty_remaining>0
           ORDER BY layer_date ASC
        2. For each layer: take = MIN(layer.qty_remaining, remaining)
           cogs += take * layer.unit_cost
           layer.qty_remaining -= take
           remaining -= take
        3. Return total COGS"""

    def _calc_lifo(self, product_id: int, qty: float) -> COGSResult:
        """LIFO: Consume from newest cost layers first.
        LIFO: الاستهلاك من أحدث طبقات التكلفة أولاً.
        Same as FIFO but ORDER BY layer_date DESC"""

    def _calc_moving_avg(self, product_id: int, qty: float) -> COGSResult:
        """Moving Average: Use current average cost.
        المتوسط المتحرك: استخدام متوسط التكلفة الحالي.
        avg_cost = SUM(layer.qty_remaining * layer.unit_cost) / SUM(layer.qty_remaining)
        cogs = qty * avg_cost"""

    def _calc_standard(self, product_id: int, qty: float) -> COGSResult:
        """Standard Costing: Use products.cost_price.
        التكلفة المعيارية: استخدام سعر التكلفة الثابت.
        cogs = qty * products.cost_price"""

    def add_cost_layer(self, product_id: int, qty: float,
                       unit_cost: float, purchase_id: int = None,
                       batch_id: int = None) -> CostLayer:
        """Add new cost layer on purchase receipt.
        إضافة طبقة تكلفة جديدة عند استلام المشتريات.
        Also recalculates moving average if method is 'moving_average'."""

    def get_inventory_valuation(self, warehouse_id: int = None) -> ValuationReport:
        """Calculate total inventory valuation using each product's method.
        حساب تقييم المخزون الكلي باستخدام طريقة كل منتج."""

    def set_costing_method(self, product_id: int,
                           method: str, effective_date: date = None) -> None:
        """Change costing method for a product.
        تغيير طريقة التسعير لمنتج.
        Note: IFRS restricts changes — requires authorization and audit entry."""
```

#### Solution for GAP-4.2: Operating Expense Management System

```
📁 Proposed Files:
  src/services/expense_service.py
  src/models/expense.py
  migrations/045_create_expense_management.sql
```

**Database Schema:**

```sql
CREATE TABLE expense_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    name_ar VARCHAR(100),            -- Arabic name
    parent_id INTEGER REFERENCES expense_categories(id),
    gl_account_id INTEGER REFERENCES chart_of_accounts(id),
    is_active BOOLEAN DEFAULT TRUE,
    budget_monthly DECIMAL(18,2) DEFAULT 0,
    budget_yearly DECIMAL(18,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES expense_categories(id),
    amount DECIMAL(18,2) NOT NULL,
    description TEXT,
    expense_date DATE NOT NULL,
    payment_method VARCHAR(30),      -- 'cash', 'bank_transfer', 'check', 'card'
    payment_ref VARCHAR(100),
    vendor_name VARCHAR(200),        -- who was paid
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_rule JSON,            -- {'frequency': 'monthly', 'day_of_month': 1}
    recurring_parent_id INTEGER REFERENCES expenses(id),
    status VARCHAR(20) DEFAULT 'draft',  -- 'draft', 'pending_approval', 'approved', 'rejected', 'paid'
    submitted_by INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP,
    gl_account_id INTEGER REFERENCES chart_of_accounts(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE expense_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER NOT NULL REFERENCES expenses(id),
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(20),           -- 'receipt', 'invoice', 'other'
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Service Interface:**

```python
class ExpenseService:
    def create_expense(self, expense: ExpenseCreate) -> Expense:
        """Create new expense entry.
        إنشاء بند مصروف جديد.
        If is_recurring, also create recurrence schedule."""

    def submit_for_approval(self, expense_id: int) -> None:
        """Submit expense for approval workflow.
        تقديم المصروف لسير عمل الموافقة.
        Sets status to 'pending_approval'."""

    def approve_expense(self, expense_id: int, approver_id: int) -> None:
        """Approve expense and create journal entry.
        الموافقة على المصروف وإنشاء قيد يومية.
        Debit: expense_category.gl_account_id
        Credit: cash/bank account"""

    def reject_expense(self, expense_id: int, approver_id: int,
                       reason: str) -> None:
        """Reject expense with reason.
        رفض المصروف مع السبب."""

    def process_recurring(self, as_of_date: date = None) -> list[Expense]:
        """Process recurring expenses due on given date.
        معالجة المصروفات المتكررة المستحقة في التاريخ المحدد."""

    def get_budget_vs_actual(self, category_id: int,
                             year: int, month: int = None) -> BudgetComparison:
        """Compare budgeted vs actual expenses.
        مقارنة المصروفات المخططة بالفعلية.
        Returns: {budgeted: X, actual: Y, variance: Z, pct: W}"""

    def get_expense_summary(self, from_date: date,
                            to_date: date) -> ExpenseSummary:
        """Get expense summary by category for period.
        الحصول على ملخص المصروفات حسب الفئة للفترة."""
```

### 5.5 Priority Assessment / تقييم الأولوية

| Gap ID | Feature / الميزة | Priority | Effort | Dependencies |
|---|---|---|---|---|
| GAP-4.1 | Costing Methods (FIFO/LIFO/MA) / طرق التسعير | 🔴 Critical | 8 days | Product model, purchase service, accounting service |
| GAP-4.2 | Expense Management / إدارة المصروفات | 🟠 High | 6 days | Chart of accounts, journal entry, approval workflow |

---

## 6. Area 5: Architecture & Infrastructure / البنية والبنية التحتية

### 6.1 Overview / نظرة عامة

The architecture supports a dual-client (Desktop + Web) system with local-first SQLite storage, FastAPI backend, JWT authentication, WebSocket real-time communication, and multi-device synchronization with cloud backup.

> تدعم البنية نظام عملاء مزدوج (سطح المكتب + الويب) مع تخزين SQLite محلي أولاً وخلفية FastAPI ومصادقة JWT واتصال WebSocket في الوقت الحقيقي ومزامنة متعددة الأجهزة مع نسخ احتياطي سحابي.

### 6.2 Current Implementation / التنفيذ الحالي

| Feature / الميزة | Status | Details / التفاصيل |
|---|---|---|
| SQLite with WAL mode | ✅ | Write-Ahead Logging for concurrent reads |
| `sync_queue` table for offline operations | ✅ | Operations queued when offline |
| FastAPI server with JWT auth | ✅ | REST API with token-based authentication |
| WebSocket support | ✅ | Real-time communication channel |
| HybridDataService | ✅ | Smart local/cloud data routing |
| DeltaSyncService | ✅ | Incremental sync with delta tracking |
| SyncService with conflict resolution | ✅ | Basic conflict resolution strategies |
| CloudSyncService (AWS/GCP/Azure) | ✅ | Cloud backup to major providers |
| PySide6 desktop application | ✅ | Full-featured desktop client |
| Next.js web application | ✅ | Responsive web client |

### 6.3 Gaps & Missing Features / الفجوات والميزات المفقودة

#### Gap 5.1: LAN Device Discovery & Auto-Configuration / اكتشاف الأجهزة على الشبكة المحلية

| Attribute | Value |
|---|---|
| **ID** | GAP-5.1 |
| **Severity / الخطورة** | ⚠️ High |
| **Arabic** | لا يوجد اكتشاف تلقائي للأجهزة على الشبكة المحلية (LAN) — يجب إعداد كل جهاز يدوياً |

**Impact / الأثر:** In multi-terminal POS deployments (e.g., 5 cash registers in a store), manual configuration of each terminal's server address, printer, and scanner is time-consuming and error-prone.

> في نشر نقاط البيع متعددة الأجهزة (مثلاً: 5 صرارات في متجر)، الإعداد اليدوي لكل جهاز يستغرق وقتاً طويلاً وعرضة للأخطاء.

**Current state:**
- Manual server URL configuration ✅ (but not auto)
- No mDNS/Zeroconf service discovery ❌
- No UDP broadcast for LAN discovery ❌
- No auto-configuration protocol ❌
- No device presence monitoring ❌

#### Gap 5.2: Automatic Offline Queue Flush / تفريغ طابور غير المتصل تلقائياً

| Attribute | Value |
|---|---|
| **ID** | GAP-5.2 |
| **Severity / الخطورة** | ⚠️ High |
| **Arabic** | لا يوجد تفريغ تلقائي لطابور العمليات غير المتصلة عند استعادة الاتصال — قد تضيع العمليات أو تتأخر بلا حدود |

**Impact / الأثر:** Operations performed offline (sales, stock adjustments) remain in `sync_queue` indefinitely if not manually synced. This creates data inconsistency between devices and can lead to lost transactions if the local database is corrupted before sync.

> العمليات المنفذة بدون اتصال تبقى في طابور المزامنة بلا حدود إذا لم تُزامن يدوياً. هذا يخلق تناقضاً في البيانات بين الأجهزة.

**Current state:**
- `sync_queue` table → exists ✅
- Queue operations when offline ✅
- No automatic flush on reconnection ❌
- No exponential backoff retry ❌
- No queue prioritization ❌
- No dead letter handling ❌
- No sync status notifications to UI ❌

#### Gap 5.3: Real-Time Collaborative Editing & Conflict Resolution UI / التحرير التعاوني في الوقت الحقيقي وواجهة حل التعارضات

| Attribute | Value |
|---|---|
| **ID** | GAP-5.3 |
| **Severity / الخطورة** | 🟡 Medium |
| **Arabic** | لا يوجد تحرير تعاوني في الوقت الحقيقي — واجهة حل التعارضات ضئيلة |

**Impact / الأثر:** When multiple users edit the same record (e.g., product price), last-write-wins without UI notification. Users are unaware of conflicts and may lose work silently.

> عندما يحرر عدة مستخدمين نفس السجل (مثلاً: سعر منتج)، آخر كتابة تفوز بدون إشعار. المستخدمون لا يعرفون عن التعارضات وقد يفقدون عملهم بصمت.

**Current state:**
- `SyncService` with conflict resolution → exists ✅ (basic)
- `DeltaSyncService` → incremental sync ✅
- WebSocket → real-time channel exists ✅
- No collaborative editing (Operational Transform/CRDT) ❌
- No conflict resolution UI ❌
- No edit conflict notifications ❌
- No version history / audit for conflicts ❌

### 6.4 Proposed Solutions / الحلول المقترحة

#### Solution for GAP-5.1: LAN Device Discovery Service

```
📁 Proposed Files:
  src/services/lan_discovery_service.py
  migrations/046_add_device_registry.sql
```

**Database Schema:**

```sql
CREATE TABLE device_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_uuid VARCHAR(36) NOT NULL UNIQUE,
    device_name VARCHAR(100),
    device_type VARCHAR(30),      -- 'pos_terminal', 'server', 'label_printer', 'scanner'
    ip_address VARCHAR(45),
    port INTEGER,
    capabilities JSON,            -- {'scanner': True, 'receipt_printer': True, 'cash_drawer': True}
    last_seen TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Service Interface:**

```python
class LANDiscoveryService:
    """LAN device discovery using mDNS + UDP broadcast.
    اكتشاف الأجهزة على الشبكة المحلية باستخدام mDNS + بث UDP."""

    def start_discovery(self) -> None:
        """Start broadcasting and listening for devices.
        بدء البث والاستماع للأجهزة.
        - Register this device via mDNS (Zeroconf)
        - Broadcast presence via UDP on port 37621
        - Listen for other devices' broadcasts"""

    def register_device(self, device_info: DeviceInfo) -> None:
        """Register this device on the network.
        تسجيل هذا الجهاز على الشبكة."""

    def discover_devices(self, timeout: float = 5.0) -> list[DeviceInfo]:
        """Discover all active devices on LAN.
        اكتشاف جميع الأجهزة النشطة على الشبكة المحلية.
        Returns list of devices with their capabilities."""

    def auto_configure(self, server_device: DeviceInfo) -> None:
        """Auto-configure this terminal to connect to discovered server.
        الإعداد التلقائي لهذا الجهاز للاتصال بالخادم المكتشف.
        - Set API base URL to server's IP:port
        - Discover and map hardware (printers, scanners)"""

    def monitor_presence(self, callback: Callable) -> None:
        """Monitor device presence and notify on connect/disconnect.
        مراقبة وجود الأجهزة والإشعار عند الاتصال/الانقطاع."""
```

**Protocol:**

```
Discovery Broadcast (every 10 seconds):
{
  "type": "el-joumla-discovery",
  "version": "1.0",
  "device_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "device_name": "POS-Terminal-3",
  "device_type": "pos_terminal",
  "ip": "192.168.1.53",
  "api_port": 8000,
  "capabilities": {"scanner": true, "receipt_printer": true}
}
```

#### Solution for GAP-5.2: Automatic Offline Queue Flush Service

```
📁 Proposed Files:
  src/services/offline_flush_service.py
```

**Service Interface:**

```python
class OfflineFlushService:
    """Automatic offline queue flush with retry and priority.
    خدمة تفريغ طابور غير المتصل تلقائياً مع إعادة المحاولة والأولوية."""

    def __init__(self):
        self.is_online = False
        self.retry_backoff = ExponentialBackoff(initial=1, max=300)
        self.priority_order = ['sale', 'payment', 'stock_adjustment', 'product_update']

    def on_connectivity_change(self, is_online: bool) -> None:
        """Handle connectivity state change.
        معالجة تغيير حالة الاتصال.
        If going online: immediately start flushing queue.
        If going offline: pause flush, queue operations."""

    def flush_queue(self) -> FlushResult:
        """Flush all pending operations in priority order.
        تفريغ جميع العمليات المعلقة بترتيب الأولوية.
        1. Sort sync_queue by priority (sales first)
        2. For each operation:
           a. Try to sync with server
           b. On success: remove from queue, notify UI
           c. On failure: increment retry_count, apply backoff
           d. If retry_count > MAX_RETRIES: move to dead_letter_queue
        3. Return FlushResult(successes, failures, remaining)"""

    def get_queue_status(self) -> QueueStatus:
        """Get current queue status for UI display.
        الحصول على حالة الطابور لعرضها في واجهة المستخدم.
        Returns: {pending_count, oldest_pending_age, estimated_flush_time}"""

    def force_sync_all(self) -> FlushResult:
        """Force immediate sync of all pending operations.
        إجبار مزامنة جميع العمليات المعلقة فوراً."""

    def move_to_dead_letter(self, operation_id: int,
                            reason: str) -> None:
        """Move failed operation to dead letter queue for manual review.
        نقل العملية الفاشلة إلى طابور الرسائل الميتة للمراجعة اليدوية."""
```

**Connectivity Monitoring:**

```python
# WebSocket-based connectivity detection
class ConnectivityMonitor:
    async def monitor(self):
        """Monitor WebSocket connection health.
        مراقبة صحة اتصال WebSocket.
        - Send heartbeat every 30 seconds
        - If 3 heartbeats fail: set offline
        - On reconnect: trigger OfflineFlushService.on_connectivity_change(True)
        - On disconnect: trigger OfflineFlushService.on_connectivity_change(False)
        """
```

#### Solution for GAP-5.3: Collaborative Editing & Conflict Resolution UI

```
📁 Proposed Files:
  src/services/collaboration_service.py
  web/components/conflict-resolution-dialog.tsx
  migrations/047_add_record_locking.sql
```

**Database Schema:**

```sql
-- Record locking for pessimistic concurrency
CREATE TABLE record_locks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    locked_by INTEGER NOT NULL REFERENCES users(id),
    locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,            -- auto-release after timeout
    session_id VARCHAR(100),
    UNIQUE(table_name, record_id)
);

-- Conflict log for audit trail
CREATE TABLE sync_conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    local_data JSON NOT NULL,
    remote_data JSON NOT NULL,
    resolution VARCHAR(20),          -- 'local_wins', 'remote_wins', 'merged'
    resolved_by INTEGER REFERENCES users(id),
    resolved_at TIMESTAMP,
    merged_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Service Interface:**

```python
class CollaborationService:
    def acquire_lock(self, table: str, record_id: int,
                     user_id: int, ttl: int = 300) -> bool:
        """Acquire edit lock on a record.
        الحصول على قفل تحرير على سجل.
        Returns False if already locked by another user."""

    def release_lock(self, table: str, record_id: int,
                     user_id: int) -> None:
        """Release edit lock.
        تحرير قفل التحرير."""

    def notify_edit(self, table: str, record_id: int,
                    field: str, value: Any, user_id: int) -> None:
        """Broadcast field edit via WebSocket to other users viewing same record.
        بث تحرير الحقل عبر WebSocket إلى المستخدمين الآخرين الذين يعرضون نفس السجل."""

    def detect_conflict(self, table: str, record_id: int,
                        local_version: int, remote_version: int) -> ConflictResult:
        """Detect if there's a version conflict.
        كشف ما إذا كان هناك تعارض في الإصدار."""

    def resolve_conflict(self, conflict_id: int,
                         resolution: str, merged_data: dict = None) -> None:
        """Resolve a sync conflict.
        حل تعارض المزامنة.
        resolution: 'local_wins', 'remote_wins', 'merged'
        If 'merged': merged_data must be provided."""
```

**Conflict Resolution UI Component:**

```typescript
// React/Next.js component for conflict resolution
interface ConflictResolutionDialogProps {
  tableName: string;
  recordId: number;
  localData: Record<string, any>;
  remoteData: Record<string, any>;
  conflictingFields: string[];
  onResolve: (resolution: 'local' | 'remote' | 'merged', mergedData?: any) => void;
}

// Shows side-by-side comparison:
// | Field    | Your Version | Server Version |
// |----------|-------------|----------------|
// | price    | 150.00      | 145.00         |  <-- highlighted
// | name     | "Product A" | "Product A"    |
// | stock    | 200         | 195            |  <-- highlighted
// [Keep Mine] [Keep Server] [Merge Manually]
```

### 6.5 Priority Assessment / تقييم الأولوية

| Gap ID | Feature / الميزة | Priority | Effort | Dependencies |
|---|---|---|---|---|
| GAP-5.1 | LAN Device Discovery / اكتشاف الأجهزة | 🟠 High | 4 days | Network stack, device registry |
| GAP-5.2 | Auto Offline Flush / تفريغ الطابور التلقائي | 🟠 High | 3 days | Sync service, WebSocket, connectivity monitor |
| GAP-5.3 | Collaborative Editing / التحرير التعاوني | 🟡 Medium | 7 days | WebSocket, sync service, UI components |

---

## 7. Consolidated Priority Matrix / مصفوفة الأولويات الموحدة

### All Gaps Ranked by Priority / جميع الفجوات مرتبة حسب الأولوية

| Rank | Gap ID | Area | Feature / الميزة | Priority | Effort | Sprint |
|---|---|---|---|---|---|---|
| 1 | GAP-1.1 | Inventory | Multi-Unit Conversion / تحويل الوحدات | 🔴 Critical | 5d | S1 |
| 2 | GAP-1.2 | Inventory | FEFO Batch Allocation / تخصيص الدفعات | 🔴 Critical | 7d | S1-S2 |
| 3 | GAP-2.1 | Sales | Credit Limit Enforcement / تطبيق حد الائتمان | 🔴 Critical | 4d | S1 |
| 4 | GAP-2.2 | Sales | ESC/POS Hardware / أجهزة نقاط البيع | 🔴 Critical | 6d | S2 |
| 5 | GAP-4.1 | Accounting | Costing Methods / طرق التسعير | 🔴 Critical | 8d | S2-S3 |
| 6 | GAP-1.3 | Inventory | 1D Barcode & Scanner / الباركود والماسح | 🟠 High | 4d | S2 |
| 7 | GAP-2.3 | Sales | Shift Management / إدارة الورديات | 🟠 High | 5d | S3 |
| 8 | GAP-3.1 | Purchases | FIFO Payment Allocation / تخصيص المدفوعات | 🟠 High | 4d | S3 |
| 9 | GAP-3.2 | Purchases | Purchase Return Workflow / مرتجع المشتريات | 🟠 High | 5d | S3-S4 |
| 10 | GAP-4.2 | Accounting | Expense Management / إدارة المصروفات | 🟠 High | 6d | S4 |
| 11 | GAP-5.1 | Architecture | LAN Discovery / اكتشاف الأجهزة | 🟠 High | 4d | S4 |
| 12 | GAP-5.2 | Architecture | Auto Offline Flush / تفريغ تلقائي | 🟠 High | 3d | S3 |
| 13 | GAP-5.3 | Architecture | Collaborative Editing / التحرير التعاوني | 🟡 Medium | 7d | S5 |

### Summary Statistics / إحصائيات ملخصة

| Metric / المقياس | Count |
|---|---|
| **Total Gaps / إجمالي الفجوات** | 13 |
| **🔴 Critical / حرج** | 5 |
| **🟠 High / عالي** | 7 |
| **🟡 Medium / متوسط** | 1 |
| **Total Estimated Effort / الجهد المقدر** | 68 days |
| **Sprints Required / الدورات المطلوبة** | 5 sprints (~2 weeks each) |

### Gaps by Area / الفجوات حسب المجال

| Area / المجال | Critical | High | Medium | Total |
|---|---|---|---|---|
| Inventory & Products / المخزون والمنتجات | 2 | 1 | 0 | 3 |
| Sales & Customers / المبيعات والعملاء | 2 | 1 | 0 | 3 |
| Suppliers & Purchases / الموردون والمشتريات | 0 | 2 | 0 | 2 |
| Accounting & Analytics / المحاسبة والتحليلات | 1 | 1 | 0 | 2 |
| Architecture & Infrastructure / البنية | 0 | 2 | 1 | 3 |

---

## 8. Implementation Roadmap / خارطة طريق التنفيذ

### Sprint Plan / خطة الدورات

```
┌─────────────────────────────────────────────────────────────────────┐
│  SPRINT 1 (Weeks 1-2): Critical Foundation                        │
│  الدورة ١: الأساسيات الحرجة                                       │
│                                                                     │
│  ● GAP-1.1: Multi-Unit Conversion Service      (5 days)           │
│  ● GAP-2.1: Credit Limit Enforcement            (4 days)           │
│  ● GAP-1.2: FEFO Batch Allocation (start)       (1 day)           │
│                                                                     │
│  Deliverable: Products can be sold in any unit with proper         │
│  conversion, credit sales are controlled, batch data model ready    │
├─────────────────────────────────────────────────────────────────────┤
│  SPRINT 2 (Weeks 3-4): POS Completion                             │
│  الدورة ٢: إكمال نقاط البيع                                       │
│                                                                     │
│  ● GAP-1.2: FEFO Batch Allocation (complete)    (6 days)           │
│  ● GAP-2.2: ESC/POS Hardware Integration        (6 days)           │
│  ● GAP-1.3: 1D Barcode & Scanner (start)        (2 days)           │
│                                                                     │
│  Deliverable: FEFO batch picking, receipt printing, cash drawer,   │
│  barcode scanning functional                                        │
├─────────────────────────────────────────────────────────────────────┤
│  SPRINT 3 (Weeks 5-6): Accounting & Operations                    │
│  الدورة ٣: المحاسبة والعمليات                                      │
│                                                                     │
│  ● GAP-4.1: Costing Methods (FIFO/LIFO/MA)      (8 days)           │
│  ● GAP-2.3: Shift Management                    (5 days)           │
│  ● GAP-3.1: FIFO Payment Allocation             (4 days)           │
│  ● GAP-5.2: Auto Offline Flush                  (3 days)           │
│                                                                     │
│  Deliverable: Accurate profit calculation, shift reconciliation,   │
│  payment allocation, offline resilience                             │
├─────────────────────────────────────────────────────────────────────┤
│  SPRINT 4 (Weeks 7-8): Workflow & Management                      │
│  الدورة ٤: سير العمل والإدارة                                      │
│                                                                     │
│  ● GAP-3.2: Purchase Return Workflow             (5 days)           │
│  ● GAP-4.2: Expense Management System            (6 days)           │
│  ● GAP-5.1: LAN Device Discovery                (4 days)           │
│                                                                     │
│  Deliverable: Complete return workflow, expense tracking with       │
│  approval, plug-and-play device setup                               │
├─────────────────────────────────────────────────────────────────────┤
│  SPRINT 5 (Weeks 9-10): Polish & Collaboration                    │
│  الدورة ٥: الصقل والتعاون                                          │
│                                                                     │
│  ● GAP-5.3: Collaborative Editing & Conflict UI  (7 days)          │
│  ● Integration testing & bug fixes               (3 days)           │
│                                                                     │
│  Deliverable: Multi-user conflict resolution, full system           │
│  integration verified                                               │
└─────────────────────────────────────────────────────────────────────┘
```

### Migration Dependencies / تبعيات الترحيل

```
Migration Order (must be sequential):
  036_create_unit_conversions.sql          ← GAP-1.1
  037_add_batch_allocation.sql             ← GAP-1.2
  038_add_barcode_generation.sql           ← GAP-1.3
  039_add_credit_management.sql            ← GAP-2.1
  040_add_hardware_config.sql              ← GAP-2.2
  041_create_shift_management.sql          ← GAP-2.3
  042_create_payment_allocations.sql       ← GAP-3.1
  043_enhance_purchase_returns.sql         ← GAP-3.2
  044_create_costing_system.sql            ← GAP-4.1  (depends on 037)
  045_create_expense_management.sql        ← GAP-4.2
  046_add_device_registry.sql              ← GAP-5.1
  047_add_record_locking.sql               ← GAP-5.3
```

---

## 9. Acceptance Criteria / معايير القبول

### GAP-1.1: Multi-Unit Conversion

| # | Criterion / المعيار | Status |
|---|---|---|
| 1 | Can define multiple units per product with conversion factors | ☐ |
| 2 | Selling in non-base unit correctly converts to base unit for stock deduction | ☐ |
| 3 | Price per unit is retrieved correctly for each unit | ☐ |
| 4 | Reports display quantities in user-selected unit | ☐ |
| 5 | Conversion is transitive: if A→B and B→C, then A→C is computed | ☐ |

### GAP-1.2: FEFO Batch Allocation

| # | Criterion / المعيار | Status |
|---|---|---|
| 1 | Sales automatically allocate from earliest-expiring batch first | ☐ |
| 2 | Expired batches are excluded from allocation | ☐ |
| 3 | Insufficient stock error raised when total batch qty < required | ☐ |
| 4 | Sale items are tagged with batch_id and batch_number | ☐ |
| 5 | Batch current_qty is decremented on sale completion | ☐ |
| 6 | Multiple batches can be allocated for a single sale line | ☐ |

### GAP-2.1: Credit Limit Enforcement

| # | Criterion / المعيار | Status |
|---|---|---|
| 1 | Credit sale is blocked when `current_balance + sale_amount > credit_limit` | ☐ |
| 2 | Manager can override credit limit with authorization code | ☐ |
| 3 | AR aging report shows 30/60/90/120+ day buckets | ☐ |
| 4 | Customer can be placed on credit hold | ☐ |
| 5 | Credit hold prevents all credit sales until released | ☐ |

### GAP-2.2: ESC/POS Hardware

| # | Criterion / المعيار | Status |
|---|---|---|
| 1 | Thermal receipt printer prints formatted receipts via ESC/POS | ☐ |
| 2 | Cash drawer opens on sale completion | ☐ |
| 3 | X-report and Z-report print correctly | ☐ |
| 4 | Hardware configuration stored in DB and loaded on startup | ☐ |
| 5 | Barcode scanner input is captured and matched to product | ☐ |

### GAP-2.3: Shift Management

| # | Criterion / المعيار | Status |
|---|---|---|
| 1 | Opening cash is recorded when shift starts | ☐ |
| 2 | All sales during shift are linked to pos_session_id | ☐ |
| 3 | Closing cash reconciliation shows expected vs. actual | ☐ |
| 4 | Cash difference (over/short) is recorded and reported | ☐ |
| 5 | Shift handover creates new shift for receiving cashier | ☐ |
| 6 | Z-report summarizes all shift activity | ☐ |

### GAP-4.1: Costing Methods

| # | Criterion / المعيار | Status |
|---|---|---|
| 1 | FIFO: COGS calculated from oldest cost layers first | ☐ |
| 2 | LIFO: COGS calculated from newest cost layers first | ☐ |
| 3 | Moving Average: COGS uses weighted average cost | ☐ |
| 4 | Standard: COGS uses fixed cost_price | ☐ |
| 5 | Cost layers created on purchase receipt | ☐ |
| 6 | Inventory valuation matches chosen costing method | ☐ |
| 7 | Costing method can be set per product | ☐ |

### GAP-5.2: Auto Offline Flush

| # | Criterion / المعيار | Status |
|---|---|---|
| 1 | Pending operations are automatically flushed when connection restored | ☐ |
| 2 | Flush follows priority order (sales before product updates) | ☐ |
| 3 | Failed operations retry with exponential backoff | ☐ |
| 4 | Operations exceeding max retries move to dead letter queue | ☐ |
| 5 | UI shows queue status (pending count, oldest age) | ☐ |

---

## 10. Appendix / الملحق

### A. Database Table Impact Summary / ملخص تأثير جداول قاعدة البيانات

| Table | Modifications | New Columns | New Tables |
|---|---|---|---|
| `products` | Add `costing_method` | 1 | — |
| `sale_items` | Add `batch_id`, `batch_number` | 2 | — |
| `sales` | Add `pos_session_id` | 1 | — |
| `customers` | Add `credit_status` | 1 | — |
| `return_invoices` | Add `original_purchase_id`, `supplier_credit_note_number` | 2 | — |
| **New Tables** | — | — | `unit_conversions`, `batch_allocations`, `credit_holds`, `hardware_config`, `pos_sessions` (formal), `cash_events`, `payment_allocations`, `return_approvals`, `cost_layers`, `costing_history`, `expense_categories`, `expenses`, `expense_attachments`, `device_registry`, `record_locks`, `sync_conflicts` |

### B. Service Layer Impact / تأثير طبقة الخدمات

| New Service | Lines Est. | Depends On |
|---|---|---|
| `unit_conversion_service.py` | ~200 | Product model |
| `batch_allocation_service.py` | ~300 | Batch model, Inventory service |
| `barcode_service.py` | ~150 | Product model, python-barcode lib |
| `scanner_service.py` | ~200 | hardware_service.py |
| `credit_service.py` | ~250 | Customer model, Sales service |
| `ar_aging_service.py` | ~150 | Customer model, Sales model |
| `escpos_printer_service.py` | ~350 | python-escpos lib, Sale model |
| `cash_drawer_service.py` | ~100 | hardware_service.py |
| `shift_service.py` | ~300 | POS session model, Sales service |
| `payment_allocation_service.py` | ~200 | Payment service, Purchase model |
| `purchase_return_service.py` | ~250 | Return service, Inventory service |
| `costing_service.py` | ~500 | Product model, Purchase model |
| `expense_service.py` | ~350 | Chart of accounts, Journal service |
| `lan_discovery_service.py` | ~200 | zeroconf lib, Device registry |
| `offline_flush_service.py` | ~250 | Sync service, WebSocket |
| `collaboration_service.py` | ~300 | WebSocket, Sync service |

### C. External Dependencies / التبعيات الخارجية

| Library | Purpose | Version | Install |
|---|---|---|---|
| `python-barcode` | EAN-13, Code128 generation | ≥0.15 | `pip install python-barcode[images]` |
| `python-escpos` | ESC/POS printer protocol | ≥3.0 | `pip install python-escpos` |
| `zeroconf` | mDNS/LAN discovery | ≥0.39 | `pip install zeroconf` |
| `Pillow` | Barcode image rendering | ≥9.0 | Already installed |

### D. Risk Assessment / تقييم المخاطر

| Risk / الخطر | Likelihood | Impact | Mitigation / التخفيف |
|---|---|---|---|
| FEFO performance with thousands of batches | Medium | Medium | Add composite index on `(product_id, warehouse_id, expiry_date)`; cache batch stock |
| Costing method change violates IFRS | Low | High | Require authorization + audit entry; restrict to new fiscal year |
| ESC/POS printer compatibility varies | Medium | Medium | Support USB, serial, and network connections; test with major brands (Epson, Star, Xprinter) |
| Offline sync conflicts with FEFO allocation | Medium | High | Reserve batches optimistically; resolve conflicts with server-side FEFO recalculation |
| Credit limit race conditions | Low | High | Use DB-level locking or `SELECT ... FOR UPDATE` pattern on customer row |

### E. Revision History / تاريخ المراجعات

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2025-07-09 | Architecture Team | Initial SRS document — gap analysis and roadmap |

---

> **End of Document / نهاية الوثيقة**
>
> This document is a living artifact and should be updated as gaps are resolved and new requirements are discovered. Each sprint completion should trigger a review and update of the relevant sections.
>
> هذه الوثيقة أداة حية ويجب تحديثها عند حل الفجوات واكتشاف متطلبات جديدة. يجب أن يؤدي إكمال كل دورة إلى مراجعة وتحديث الأقسام ذات الصلة.
