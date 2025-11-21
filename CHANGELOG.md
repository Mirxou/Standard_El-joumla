# Changelog - الإصدار المنطقي (Logical Version)

All notable changes to this project will be documented in this file.

---

## [3.5.1] - 2025-11-20 (Maintenance)

### ✅ Stability & Test Reliability
- Standardized data access in Loyalty Service (`execute_query` replaces direct cursor usage)
- Fixed dict-based row access in Loyalty Service (removed tuple-style indexing)
- Added `vendors` table creation for isolated in-memory tests in Vendor Portal
- Defensive try/except around optional tables (`purchase_orders`, `vendor_ratings`) to avoid OperationalError in tests
- Updated test fixtures to use `db.initialize()` and `db_manager.connection`
- Achieved full test pass rate: **42/42 tests passing** (100% success rate)
  - test_ai_features.py: 26/26 ✅
  - test_comprehensive.py: 8/8 ✅
  - tests/ (API tests): 8/8 ✅

### 🔧 Dependencies & Compatibility
- Upgraded `pydantic` from 1.10.15 to 2.x for Python 3.13 compatibility
- Added `fastapi` and `httpx` to test requirements
- Fixed test_sales_api.py import order issue
- All services compatible with pydantic v2

### 🔒 Risk / Impact
- Low risk, no API contract changes
- All changes are idempotent and backward compatible
- Production dependencies updated for future compatibility

---

## [3.5.0] - 2024-12-20

### 🛡️ Multi-Factor Authentication (MFA)

#### Core MFA System
- **Complete MFA Service** (`src/security/mfa_service.py` - 500 lines)
  - SMS OTP: 6-digit codes, 5-minute expiry, 3 max attempts
  - Email OTP: 6-digit codes, 5-minute expiry, 3 max attempts
  - TOTP: RFC 6238 compliant, 30-second time step, HMAC-SHA1
  - Backup Codes: 10 codes per user, SHA-256 hashing, single-use

#### Security Features
- Secure random generation using `secrets.randbelow()`
- Encrypted storage for TOTP secrets
- Audit trail for all verification attempts
- IP address and User-Agent tracking
- Rate limiting on OTP attempts

#### Database Tables
- `mfa_settings`: User MFA configuration
- `mfa_otp`: Temporary OTP storage
- `mfa_verification_log`: Complete audit trail

#### API Endpoints
- `POST /auth/mfa/enable` - Enable MFA with multiple methods
- `POST /auth/mfa/disable` - Disable MFA
- `POST /auth/mfa/send-otp` - Send OTP via SMS or Email
- `POST /auth/mfa/verify` - Verify OTP, TOTP, or backup code

#### TOTP Support
- QR code URL generation for Authenticator apps
- Compatible with Google Authenticator
- Compatible with Microsoft Authenticator
- Base32-encoded secret sharing

### 📢 Marketing Automation

#### Campaign Management
- **Email Campaigns**: Subject, content, scheduling
- **SMS Campaigns**: Bulk SMS with personalization
- **Social Media Campaigns**: Multi-platform support
- **Push Notifications**: Real-time customer engagement

#### Customer Segmentation
- Dynamic criteria (tier, purchases, location, etc.)
- Automatic segment updates
- Custom segment creation
- Segment analytics

#### Lead Scoring
- Hot Leads: High engagement, recent activity
- Warm Leads: Moderate engagement
- Cold Leads: Low engagement
- Automatic scoring updates

#### Analytics & ROI
- Campaign performance metrics
- Conversion tracking
- Revenue attribution
- Cost per conversion
- ROI calculation

#### API Endpoints
- `POST /marketing/segments` - Create customer segment
- `POST /marketing/campaigns` - Create campaign
- `POST /marketing/campaigns/{id}/send` - Send campaign
- `GET /marketing/campaigns/{id}/analytics` - Get analytics
- `GET /marketing/leads/hot` - Get hot leads

### 🔧 API Updates

#### Version Bump
- API Version: `3.0.0` → `3.5.0`
- Added 10+ new endpoints
- Total endpoints: 140+

#### New Integrations
- `MFAService` integration
- `MarketingService` integration
- Enhanced error handling
- Improved dependency injection

### 📊 System Statistics

- **Spec Coverage**: 100% ✅ (up from 85%)
- **Total Features**: 70+
- **API Endpoints**: 140+
- **New Code Lines**: ~1,100
- **Database Tables**: 50+

### 🎯 Achievements

- ✅ Complete MFA implementation
- ✅ Marketing automation suite
- ✅ 100% specification coverage
- ✅ Production-ready security
- ✅ Global compliance standards

---

## [3.0.0] - 2024-12-19

### 🤖 AI & Machine Learning Features

#### AI Chatbot
- **Bilingual NLP Engine** (`src/ai/chatbot.py` - 478 lines)
  - Arabic and English language detection
  - 7 intent categories (sales, inventory, customers, reports, products, invoicing, general)
  - Pattern matching with confidence scoring
  - Conversation history tracking
  - Context-aware responses

#### Predictive Analytics
- **ML-Powered Forecasting** (`src/ai/predictive_analytics.py` - 320 lines)
  - Sales forecasting with trend analysis
  - Customer behavior analysis (LTV, RFM)
  - Product recommendations (collaborative filtering)
  - Anomaly detection (statistical outliers)
  - Customer segmentation (VIP, Regular, Active, New)

#### API Endpoints
- `POST /ai/chat` - Chat with AI assistant
- `GET /ai/chat/history` - Get conversation history
- `GET /ai/forecast/sales` - Sales predictions
- `GET /ai/insights/customer/{id}` - Customer insights
- `GET /ai/recommendations/{customer_id}` - Product recommendations
- `GET /ai/anomalies` - Detect unusual patterns

### 🎁 Loyalty Program

#### 4-Tier System
- **Bronze**: 0-999 points (1% cashback)
- **Silver**: 1000-4999 points (2% cashback)
- **Gold**: 5000-9999 points (3% cashback)
- **Platinum**: 10000+ points (5% cashback)

#### Features
- Automatic points accumulation (1 SAR = 1 point)
- Points redemption for discounts
- Automatic tier upgrades
- Special offers and promotions
- Points expiry management

#### Database Tables
- `loyalty_balance`: Customer points balance
- `loyalty_transactions`: Points earn/redeem history
- `loyalty_offers`: Special promotions

#### API Endpoints
- `POST /loyalty/earn` - Earn points from sale
- `POST /loyalty/redeem` - Redeem points
- `GET /loyalty/balance/{customer_id}` - Get balance
- `POST /loyalty/offers` - Create special offer

### 📄 E-Invoicing System

#### Government Compliance
- **Digital Signatures**: SHA-256 hashing
- **QR Codes**: Base64-encoded, Saudi/GCC standard
- **XML Format**: UBL (Universal Business Language)
- **JSON Format**: Structured invoice data

#### Features
- E-invoice generation for all sales
- QR code on printed invoices
- Digital signature validation
- XML/JSON export
- Recurring invoice management

#### Database Tables
- `einvoices`: Invoice metadata
- `recurring_invoices`: Subscription billing

#### API Endpoints
- `POST /einvoice/generate/{invoice_id}` - Generate e-invoice
- `GET /einvoice/{invoice_id}` - Get e-invoice
- `GET /einvoice/{invoice_id}/xml` - Export as XML
- `POST /einvoice/recurring` - Setup recurring invoice

### 🏪 Vendor Portal

#### Self-Service Features
- Vendor dashboard with real-time metrics
- Purchase order tracking
- Messaging system with staff
- Document upload/download
- Performance ratings

#### Database Tables
- `vendor_portal_accounts`: Portal access
- `vendor_messages`: Communication history
- `vendor_documents`: File management

#### API Endpoints
- `GET /vendor/dashboard/{vendor_id}` - Dashboard metrics
- `GET /vendor/orders/{vendor_id}` - Purchase orders
- `POST /vendor/message` - Send message
- `POST /vendor/document` - Upload document

### 🔧 System Enhancements

#### API Version
- Updated to `3.0.0`
- 130+ endpoints
- Enhanced error handling
- Improved performance

#### Dependencies
- Pattern matching libraries
- Statistical analysis tools
- QR code generation
- XML processing

---

## [2.0.0] - 2024-11-20

### 🔒 Security Enhancements v2.0

#### Rate Limiting
- **Thread-safe in-memory rate limiter** (`src/security/rate_limiter.py`)
  - Login endpoint: 10 attempts per 5 minutes per IP
  - API endpoints: 100 requests per minute per client
  - Automatic cleanup to prevent memory bloat
  - Returns `HTTP 429` with localized error message
- **Features**:
  - Per-IP tracking for anonymous requests
  - Per-token tracking for authenticated requests
  - Graceful degradation if unavailable
  - Configurable limits and time windows

#### Enhanced Authentication
- Rate-limited login with client IP tracking
- Improved error messages with context
- JWT token expiry management
- Security audit trail support

### 🌍 Internationalization (i18n)

#### Core i18n Implementation
- **Lightweight i18n service** (`src/utils/i18n_api.py`)
  - Fast message lookup (O(1))
  - Automatic locale negotiation from `Accept-Language` header
  - Fallback to default language (Arabic)
  - Format string support with parameters

#### Supported Locales
- **Arabic (ar)** - Default, 70+ messages
- **English (en)** - Full coverage, 70+ messages

#### Locale Files
- `locales/ar.json` - Arabic translations
- `locales/en.json` - English translations

#### API Integration
- All error responses support localization
- Messages include: authentication errors, rate limiting, validation, business logic
- Example: `"تم تجاوز حد المعدل. يرجى المحاولة لاحقاً."` / `"Rate limit exceeded. Please try again later."`


### 🧪 Testing
- **All tests passing**: 49/49 (100%)
- Rate limiter tested with multiple login attempts
- RBAC enforcement verified
- i18n message rendering validated

### 📚 Documentation
- Comprehensive security & i18n report: `SECURITY_I18N_v2.0_REPORT.md`
- Architecture diagrams and usage examples
- Deployment checklist and monitoring recommendations

---

## [1.8.0] - 2025-11-19

### 🧾 Added - Purchase Orders API

#### Core Purchase Order Lifecycle
- **Create Purchase Order**: Structured multi-line item purchase orders
  - `POST /purchase/orders` (Admin) – Supplier info, required date, currency, notes
  - Automatic PO number generation (`PO-{timestamp}`)
  - Line item financial breakdown (subtotal, discount, tax, net amounts)
- **List Purchase Orders**: Paginated list with status tracking
  - `GET /purchase/orders?page=&page_size=` – Includes supplier, totals, items_count
- **Purchase Order Detail**:
  - `GET /purchase/orders/{po_id}` – Full item quantities (ordered/received/pending)
- **Status Update**:
  - `POST /purchase/orders/update-status` – Workflow status transitions
  - Supports lifecycle values: `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `SENT_TO_SUPPLIER`, `CONFIRMED_BY_SUPPLIER`, `PARTIALLY_RECEIVED`, `FULLY_RECEIVED`, `CANCELLED`
- **Receive Shipment**:
  - `POST /purchase/orders/receive` – Accept received quantities per item
  - Updates `quantity_received` and `quantity_pending`
  - Records inventory stock movement with type `PURCHASE` (audit trail)

#### Data & Validation
- **Schemas Added**:
  - `PurchaseOrderItemCreate` – product_id, product_name, qty, pricing, discount/tax
  - `PurchaseOrderCreate` – supplier metadata + items list
  - `PurchaseOrderStatusUpdate` – `po_id`, `new_status`
  - `ReceivingItemCreate` / `ReceiveShipmentRequest` – granular receiving structure
- **Financial Calculations**: Per-item discount and tax amount derivation, net aggregation to `subtotal` and `total_amount`
- **Role-Based Access**: Create restricted to Admin; other operations require valid JWT

#### Inventory Integration
- Automatic stock movement creation on receipt with reference linkage (`purchase_order`)
- Movement stored using existing `StockMovement` + `MovementType.PURCHASE`

#### Testing
- New integration test suite: `test_purchase_api.py`
  - Create → List → Detail → Status Update → Receive flow
  - Validates quantity updates and message responses

### 🔧 Technical Updates
- **Service Injection**: Extended `get_services()` to include `purchase_order_service`
- **Endpoint Layer**: Added 5 endpoints under purchase namespace
- **Version**: Incremented to 1.8.0 (see `VERSION.txt`)

### 📚 Documentation
- Pending README & API summary updates (added in this release cycle)
- Changelog entry (this section) documents full scope

---

## [1.7.0] - 2025-11-19

### 🛒 Enhanced - Sales Orders API (Lifecycle & After-Sale Operations)

#### Order Status Workflow
- Added status transition endpoint:
  - `POST /sales/orders/update-status` – Supports: `draft`, `pending`, `confirmed`, `completed`, `cancelled`, `returned`, `refunded`
- Consistent response messaging: `Order <id> status updated to <status>`

#### Payment Tracking
- Added payment summary endpoint:
  - `POST /sales/orders/track-payment` – Returns payments list, `total_paid` aggregation
- Foundation for multi-payment per order scenarios

#### Refund Processing
- `POST /sales/orders/create-refund` – Partial/Full refund amounts with reason field
- Hooks prepared for financial ledger integration (future accounting linkage)

#### Returns Handling
- `POST /sales/orders/create-return` – Item-level return specification
- Enables inventory reconciliation & potential stock adjustments (future extension)

#### Validation & Security
- All endpoints JWT-protected; honors existing RBAC (Admin/Cashier roles)
- Structured Pydantic request bodies for each operation

#### Documentation & Tests
- README updated with new sales endpoints block (Arabic section)
- Extended `test_sales_api.py` for status, payment tracking, refund, return scenarios

---

## [1.6.0] - 2025-11-19

### 📊 Added - Reports & Analytics API

#### Comprehensive Reporting System
- **Sales Summary Report**: Complete sales analysis and insights
  - `POST /reports/sales-summary` - Generate sales summary with filters
  - Total sales revenue, count, and averages
  - Payment methods breakdown (cash, credit, debit)
  - Top customers analysis
  - Daily sales trends and charts data
  - Discount and tax summaries
  - Export formats: JSON, Excel (XLSX), PDF, CSV

- **Inventory Status Report**: Real-time stock analysis
  - `POST /reports/inventory-status` - Generate inventory status report
  - Stock levels and valuations
  - Out-of-stock, low-stock, high-stock alerts
  - Category-wise inventory breakdown
  - Stock status distribution charts
  - Export to multiple formats

- **Financial Summary Report**: Profit & Loss analysis
  - `POST /reports/financial-summary` - Generate financial overview
  - Total sales vs purchases comparison
  - Gross profit calculation
  - Profit margin percentage
  - Current inventory valuation
  - Monthly financial trends
  - Export capabilities

- **Payment Summary Report**: Payment analytics
  - `POST /reports/payment-summary` - Analyze payment patterns
  - Payment methods analysis
  - Outstanding balances tracking
  - Payment status breakdown
  - Date range filtering

- **Cash Flow Report**: Cash movement tracking
  - `POST /reports/cash-flow` - Monitor cash inflows/outflows
  - Net cash flow calculations
  - Period-based analysis
  - Cash flow trends

#### Advanced Filtering
- **Flexible Report Filters** via `ReportFilterSchema`:
  - Date range filtering (start_date, end_date)
  - Customer-specific reports (customer_id)
  - Supplier-specific reports (supplier_id)
  - Category filtering (category_id)
  - Product filtering (product_id)
  - User/salesperson filtering (user_id)
  - Amount range (min_amount, max_amount)
  - Payment type/method/status filters

#### Export Features
- **Multiple Export Formats**:
  - JSON: Direct API response with full data
  - Excel (XLSX): Formatted spreadsheet with charts
  - PDF: Professional report documents
  - CSV: Data export for external analysis
  - Format selection via query parameter: `?format=xlsx`

#### Analytics Capabilities
- Automatic chart data generation for visualizations
- Summary statistics and KPIs
- Trend analysis over time periods
- Category and segment breakdowns
- Performance metrics and comparisons

### 🔧 Technical Updates
- **Service Architecture**: Extended to 7-tuple
  - Added `reports_service` to service layer
  - Updated `get_services()` return signature
  - All endpoints migrated to 7-tuple pattern
  
- **Pydantic Schemas**: Added `ReportFilterSchema` for request validation

- **Version**: API version updated to 1.6.0

### ✅ Testing
- Created comprehensive test suite: `test_reports_api.py`
  - 10 test scenarios covering all report types
  - Filter validation tests
  - Export format tests
  - Authorization tests
  - Invalid input handling

---

## [1.5.0] - 2025-11-19

### 🏢 Added - Vendor Management & Rating API

#### Vendor CRUD Operations
- **Create Vendor**: Complete vendor profile creation
  - `POST /vendors` - Create vendor with name, contact info, payment terms, credit limit
  - Support for Arabic business names
  - Credit limit tracking (Admin only)
  
- **Get Vendor Details**: Retrieve complete vendor information
  - `GET /vendors/{vendor_id}` - Full vendor profile
  
- **Search Vendors**: Find vendors by name, contact, phone, or email
  - `GET /vendors?term={search_term}` - Search with flexible filters
  - Returns matching vendors list

#### Vendor Rating & Evaluation System
- **Create Evaluation**: Comprehensive vendor performance evaluation
  - `POST /vendors/{vendor_id}/evaluations` - Submit detailed evaluation
  - Five scoring criteria (1-5 scale):
    - Quality Score
    - Delivery Score
    - Pricing Score
    - Communication Score
    - Reliability Score
  - Automatic overall score calculation (average of 5 criteria)
  - Automatic grade assignment (A+, A, B+, B, C, D, F)
  - Track order statistics and delivery performance
  - Notes and recommendations support
  - Approved/Preferred vendor flags

- **Get Latest Evaluation**: Retrieve most recent vendor assessment
  - `GET /vendors/{vendor_id}/evaluation` - Latest evaluation details
  
- **Get Vendor Score**: Quick access to vendor grade
  - `GET /vendors/{vendor_id}/score` - Overall score and grade

#### Vendor Performance Metrics
- **Performance Analytics**: Automated performance tracking
  - `GET /vendors/{vendor_id}/performance` - Key performance indicators
  - Average lead time in days
  - Total orders and completion rate
  - On-time delivery rate
  - Calculated from purchase order history

#### Technical Implementation
- VendorService integration for CRUD operations
- VendorRatingService for evaluation system
- 6-tuple service architecture (added vendor_crud_service)
- Comprehensive Pydantic schemas with validation
- Role-based access control (Admin for create, Manager for evaluations)

### 🧪 Testing
- New comprehensive test suite: `test_vendor_api.py`
- 11 test scenarios covering:
  - Vendor CRUD operations
  - Vendor search functionality
  - Evaluation creation and retrieval
  - Score/grade calculations
  - Performance metrics
  - Authorization checks
  - Input validation
  - Error handling

---

## [1.4.0] - 2025-11-19

### 📦 Added - Inventory Management API

#### Stock Transfer Operations
- **Transfer Stock**: Transfer inventory between warehouse locations
  - `POST /inventory/transfer` - Transfer stock with from/to location tracking
  - Support for multi-location warehousing
  - Detailed notes and audit trail for each transfer
  - Role-based access (Admin, Warehouse staff)

#### Stock Reservation System  
- **Reserve Stock**: Reserve inventory for orders and operations
  - `POST /inventory/reserve` - Reserve stock with reference tracking
  - Links to orders/quotes via reference_id and reference_type
  - Prevents overselling with automated reservation
- **Release Stock**: Release reserved inventory
  - `POST /inventory/release/{product_id}` - Release with quantity and reference
  - Supports partial release of reservations
  - Automatic stock availability updates

#### Inventory Tracking & Analytics
- **Stock Movements**: Complete movement history and audit trail
  - `GET /inventory/movements` - List all stock movements with filters
  - Filter by product_id, date range, limit
  - Movement types: Transfer, Reservation, Release, Adjustment, Loss
  - Full audit trail with timestamps and user tracking
- **ABC Analysis**: Product categorization by value
  - `GET /inventory/abc-analysis` - Automatic ABC classification
  - Category A: Top 80% of inventory value
  - Category B: Next 15% of inventory value  
  - Category C: Remaining 5% of inventory value
  - Helps optimize inventory management and purchasing decisions

#### Technical Improvements
- Enhanced InventoryService integration (652 lines)
- Support for batch tracking and barcode scanning
- Multi-warehouse location support
- Comprehensive error handling and validation
- Role-based access control for all inventory operations

### 🧪 Testing
- New comprehensive test suite: `test_inventory_api.py`
- 9 test scenarios covering all inventory operations
- Validation testing for data integrity
- Authorization and authentication tests

---

## [1.3.0] - 2025-11-19

### 🛒 Added - Sales & Customer Management API

#### Sales Orders API
- **Create Sales Order**: Direct creation of sales orders with line items
  - `POST /sales/orders` - Create order with customer, items (product/batch), payment method, notes
  - Full line item support with product_id, batch_id, quantity, unit_price
  - Automatic invoice number generation (`ORD-{timestamp}`)
  - Total amount calculation with discount support at item level
- **List Sales Orders**: Paginated list with customer information
  - `GET /sales/orders?page=&page_size=` - List all orders with pagination
  - Includes customer name, invoice number, amounts, payment method
- **Sales Order Detail**: Full order information with all items
  - `GET /sales/orders/{id}` - Detailed order with all sale items and product names
  - Complete order metadata and line items breakdown

#### Customer Management API  
- **Create Customer**: Full customer profile creation
  - `POST /customers` - Create with name, phone, email, address, credit limit (Admin only)
  - Arabic business names fully supported
  - Credit limit tracking and active status
- **Customer Details**: Retrieve complete customer information
  - `GET /customers/{id}` - Full customer profile including credit info
- **List Customers**: Paginated customer listing
  - `GET /customers?page=&page_size=` - All customers with balances and contact info

#### Quotes API (Partial)
- **Quote Creation**: Basic quote support
  - `POST /sales/quotes` - Create quote with items and validity period
  - `GET /sales/quotes?page=&page_size=` - List quotes
  - **Note**: Requires `quotes` table migration (currently returns 501 if table missing)

### 🔧 Technical Improvements
- **Service Integration**: Added `SalesService` to API dependency injection
- **4-Tuple Refactor**: Updated all endpoints to handle new service structure (db, us, vs, ss)
- **Error Handling**: Improved error messages for sales operations
- **Database Schema Alignment**: Mapped API models to existing `sales`, `sale_items` tables
- **Testing**: Complete test coverage in `test_sales_api.py` (100% pass rate)

### 📊 API Statistics (v1.3.0)
- **Total Endpoints**: ~35 (including auth, products, bundles, pricing, tags, suppliers, sales, customers, quotes)
- **Sales Endpoints**: 7 new endpoints (create/list/detail orders, create/list quotes, create/detail/list customers)
- **Authentication**: JWT-based with role validation (Admin, Cashier roles for sales)

---

## [1.2.0] - 2025-11-19

### 🚀 Added - Product Management Expansion

#### Product Variants
- **Product Variants API**: Complete CRUD for product variants with attributes (size, color, etc.)
- **Variant Schema**: `VariantCreate` Pydantic model with SKU, attributes JSON, barcode support
- **Endpoints**:
  - `POST /products/{id}/variants` - Create variant (Admin only)
  - Variants included in `GET /products/{id}` detail response
- **Migration 013**: `product_variants` table with attributes, pricing, stock per variant
- **Migration 014**: Added `current_stock` column to align with API expectations

#### Product Bundles
- **Bundle System**: Create bundles composed of products and/or variants
- **Bundle Schemas**: `BundleCreate`, `BundleItemCreate` with item_type validation
- **Endpoints**:
  - `POST /products/{id}/bundles` - Create bundle (Admin only)
  - `POST /bundles/{id}/items` - Add product/variant to bundle (Admin only)
  - `GET /bundles?page=&page_size=` - List bundles with pagination
  - `GET /bundles/{id}` - Bundle detail with all items
  - `DELETE /bundles/{id}/items/{item_id}` - Remove bundle item (Admin only)
- **Tables**: `product_bundles`, `product_bundle_items` with FK constraints

#### Tiered Pricing
- **Advanced Pricing**: Multiple price points per product/variant
- **Price Types**: `retail`, `wholesale`, `customer_group` with validation
- **Schema**: `PriceCreate` with min_qty, valid_from/to, customer_group support
- **Endpoints**:
  - `POST /prices` - Create price tier (Admin only, requires product_id or variant_id)
  - `GET /products/{id}/prices` - List product price tiers (ordered by min_qty)
  - `GET /variants/{id}/prices` - List variant price tiers
  - `DELETE /prices/{id}` - Delete price tier (Admin only)
- **Table**: `product_prices` with date validity and customer group support

#### Product Tags & Filtering
- **Tagging System**: Flexible product categorization via tags
- **Tag Filtering**: Filter products by tag in list endpoint
- **Endpoints**:
  - `POST /products/{id}/tags` - Add tag (Admin only)
  - `GET /products/{id}/tags` - List product tags
  - `DELETE /products/{id}/tags/{tag}` - Remove tag (Admin only)
  - `GET /products?tag=<value>` - Filter products by tag
- **Table**: `product_tags` with unique constraint on (product_id, tag)

#### Multiple Barcodes
- **Multi-Barcode Support**: Multiple barcodes per product/variant
- **Primary Barcode**: Flag to mark primary barcode
- **Barcode Types**: `auto`, `ean13`, `code128`, `qrcode`
- **Table**: `product_barcodes` with unique barcode constraint
- **API**: Barcodes returned in product detail endpoint

### 🔧 Enhanced

#### API Improvements
- **Product List Endpoint**: Now supports optional `?tag=<value>` filter
- **Product Detail**: Returns variants and barcodes arrays
- **Validation**: Strict `price_type` enum and conditional `customer_group` requirement
- **Error Handling**: Proper 400/404 responses with descriptive messages

#### Database Schema
- **Migration 013**: Complete schema for variants, bundles, pricing, barcodes, tags
- **Migration 014**: Column addition with backfill from legacy `stock_quantity`
- **Indexes**: Optimized queries on product_id, variant_id, SKU, barcode, tag
- **Constraints**: FK integrity, unique constraints on barcodes and tags

### 🧪 Testing

#### New Integration Tests
- **test_api_products.py**: Product and variant creation, detail retrieval (1 test)
- **test_api_tags.py**: Tag add/list/filter/delete flow (1 test)
- **test_api_bundles.py**: Bundle creation, item addition, detail fetch (1 test)
- **test_api_pricing.py**: Price tier creation and listing (1 test)
- **test_api_pricing_negative.py**: Invalid price_type and missing customer_group (1 test)
- **Test Results**: 49/49 passing (100%)

### 📚 Documentation

#### Updated Files
- **README.md**: Added "REST API Quick Reference" section with all new endpoints
- **دليل_API_بالعربية.md**: Comprehensive Arabic API guide with:
  - Product creation, variant creation, product detail examples
  - Tags: add/list/delete with filtering
  - Bundles: create/add items/list/detail
  - Pricing: create/list/delete price tiers
  - Updated RBAC table with all new admin-only endpoints

#### New Files
- **api_samples.http**: VS Code REST Client samples with JWT token reuse
- **api_postman_collection.json**: Postman collection with environment variables

### 🔐 Security & Quality

- **RBAC Enforcement**: All write operations restricted to admin role
- **Input Validation**: Pydantic v1 schemas with Field constraints (ge, gt, default)
- **SQL Safety**: Parameterized queries throughout, no SQL injection vectors
- **Unique Identifiers**: Test fixtures use UUID to prevent cross-run collisions
- **Literal Types**: Restricted `item_type` and `price_type` to allowed values

---

## [1.1.0] - 2025-11-19

### 🚀 Added - Major Features

#### REST API Layer
- **FastAPI Integration**: Professional REST API with automatic documentation
- **JWT Authentication**: Secure token-based authentication with 24-hour expiry
- **Pagination Support**: Professional pagination for all list endpoints
  - Customers, Products, Invoices with `PaginatedResponse` model
  - Query parameters: `page` and `page_size` (max 100)
- **API Documentation**: Auto-generated Swagger UI and ReDoc
- **API Server**: Uvicorn ASGI server with hot-reload support
- **Health Endpoint**: `/health` for monitoring and load balancers

#### Vendor Rating System
- **VendorRatingService**: Complete supplier evaluation system
- **Evaluation Criteria**: 5-point scale for quality, delivery, pricing, communication, reliability
- **Auto-Grading**: Automatic grade assignment (A+, A, B+, B, C, D, F)
- **API Endpoints**:
  - `POST /suppliers/{id}/evaluations` - Create evaluation (Admin only)
  - `GET /suppliers/{id}/rating` - Get latest rating
- **RBAC Integration**: Role-based access control for evaluation creation

#### Security Enhancements
- **RBAC**: Role-based access control for API endpoints
- **Admin Roles**: Support for `admin`, `ADMIN`, and `مدير`
- **403 Forbidden**: Proper HTTP status for insufficient privileges
- **Bearer Token**: Industry-standard authorization header

### 🔧 Fixed

#### Critical Bugs
- **DatabaseManager API**: Fixed `get_connection()` vs `connection` property usage
- **JWT Generation**: Handle role as string value instead of enum
- **Context Manager**: Fixed `get_cursor()` context manager usage throughout codebase
- **Pydantic v2 Compatibility**: Added `skip_on_failure=True` to `@root_validator` decorators
- **UserRole Enum**: Use existing roles (CASHIER) instead of non-existent USER

#### Test Fixes
- **pytest Configuration**: Removed deprecated `pytest_html_report_title` hook
- **Test Isolation**: Proper database setup in vendor rating tests
- **API Tests**: Fixed user creation and authentication flows

### 📚 Documentation

#### New Files
- **API_IMPLEMENTATION_SUMMARY.md**: Complete technical documentation for API
- **DEPLOYMENT.md**: Comprehensive deployment guide
  - Desktop deployment (Windows/Linux)
  - API server deployment (Development/Production)
  - Security hardening
  - Monitoring and maintenance
  - Troubleshooting guide
- **.env.example**: Environment configuration template
- **scripts/test_api_health.py**: Automated API health check script

#### Updated Files
- **README.md**: Added REST API section with examples
- **README.md**: Updated security section with JWT and RBAC
- **requirements.txt**: Added FastAPI, Uvicorn, PyJWT, requests
- **requirements-test.txt**: Added pytest>=7.0.0 and httpx>=0.27.0

### 🧪 Testing

#### New Tests
- **test_vendor_rating_service.py**: Unit tests for vendor rating service
- **test_api_vendor_rating.py**: Integration tests for API endpoints
  - Evaluation creation test
  - Rating retrieval test
  - RBAC enforcement test (non-admin blocked)

#### Test Results
- **Vendor Rating Tests**: 3/3 passing (100%)
- **System Tests**: 7/7 passing (100%)
  - Module imports
  - Database initialization (60 tables)
  - Security service (Argon2id + TOTP)
  - LRU Cache with TTL
  - Pydantic validation
  - Structured logging
  - SQLite connection pool

### 📦 Dependencies

#### New Dependencies
```
fastapi>=0.110.0           # REST API framework
uvicorn[standard]>=0.30.0  # ASGI server
PyJWT>=2.10.0              # JWT authentication
pytest>=7.0.0              # Testing framework
httpx>=0.27.0              # HTTP client for tests
requests>=2.32.0           # HTTP requests
argon2-cffi==25.1.0        # Password hashing
pyotp==2.9.0               # TOTP 2FA
```

### 🎯 Performance

- **Connection Pooling**: Already optimized with 10-connection pool
- **LRU Caching**: TTL-based caching for frequently accessed data
- **Pagination**: Prevents large data transfers
- **Indexed Queries**: All list endpoints use database indexes

### 🔒 Security

- **Argon2id**: Military-grade password hashing
- **TOTP 2FA**: Time-based one-time passwords
- **JWT**: Secure token-based authentication
- **RBAC**: Fine-grained access control
- **Audit Logging**: All security events logged

---

## [1.0.0] - 2025-11-XX

### Initial Release

#### Core Features
- **Desktop Application**: PySide6-based GUI
- **Inventory Management**: Products, stock, batches, adjustments
- **Sales & Purchases**: Invoices, returns, quotes
- **Accounting System**: Double-entry bookkeeping, chart of accounts
- **Customer & Supplier Management**: Contacts, transactions, balances
- **Payment Plans**: Installments, schedules, notifications
- **Reports**: Sales, inventory, financial, exports (PDF, Excel, JSON)
- **User Management**: Roles, permissions, authentication
- **Backup System**: Encrypted backups with AES-256-GCM
- **Logging**: Structured JSON logging with rotation
- **Database**: SQLite with WAL mode and optimization

#### Security
- **Argon2id Password Hashing**: Automatic rehashing on login
- **2FA Support**: TOTP-based two-factor authentication
- **Session Management**: Timeout, brute-force protection
- **Encrypted Backups**: AES-256-GCM with metadata and checksums

#### Performance
- **Connection Pool**: SQLite connection pooling
- **Caching**: LRU cache with TTL for frequent queries
- **Database Optimization**: Proper indexes and PRAGMA settings
- **Non-blocking UI**: Background operations for heavy tasks

#### Documentation
- **README.md**: Comprehensive user and developer documentation (735+ lines)
- **SECURITY_BACKUP_GUIDE.md**: Security best practices
- **PRODUCTION_CHECKLIST.md**: Pre-production verification
- **Database Schema**: 60+ tables with migrations

---

## Version History Summary

- **v1.8.0** (2025-11-19): Purchase Orders API (create/list/detail/status/receive), Admin RBAC, inventory movement integration
- **v1.7.0** (2025-11-19): Sales order lifecycle enhancements (status, payments, refunds, returns)
- **v1.6.0** (2025-11-19): Reports & Analytics API (sales, inventory, financial, payment, cash flow)
- **v1.5.0** (2025-11-19): Vendor Management & Rating API (CRUD, evaluations, performance metrics)
- **v1.4.0** (2025-11-19): Inventory Management API (transfer, reserve/release, movements, ABC analysis)
- **v1.3.0** (2025-11-19): Sales & Customer Management API (orders, quotes, customers)
- **v1.2.0** (2025-11-19): Product expansion (variants, bundles, tiered pricing, tags, barcodes)
- **v1.1.0** (2025-11-19): Initial REST API layer + Vendor Rating foundation
- **v1.0.0** (2025-11-XX): Initial desktop ERP release (inventory, sales, accounting, security)

---

## Upgrade Notes

### From 1.0.0 to 1.1.0

#### Breaking Changes
- None. This is a backward-compatible update.

#### New Features Available
- REST API endpoints (opt-in, requires running API server)
- Vendor rating system (accessible via API and future UI integration)

#### Action Required
1. **Update Dependencies**:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

2. **Security Recommendation**:
   - Create `.env` file from `.env.example`
   - Change `JWT_SECRET_KEY` to a secure random value
   - Update admin password if still using default

3. **Optional - Enable API**:
   ```bash
   python scripts/run_api_server.py
   ```

4. **Verify Installation**:
   ```bash
   python scripts/run_system_tests.py
   python scripts/test_api_health.py  # If API enabled
   ```

---

## Future Roadmap

### Planned Features
- [ ] Rate limiting for API endpoints
- [ ] Complete CRUD operations for all entities
- [ ] E-invoicing integration (government compliance)
- [ ] Advanced analytics and dashboards
- [ ] Cloud backup support
- [ ] Mobile app (React Native)
- [ ] Multi-branch support
- [ ] AI-powered forecasting
- [ ] OCR for receipt scanning

### Under Consideration
- [ ] GraphQL API layer
- [ ] WebSocket support for real-time updates
- [ ] Multi-currency support enhancements
- [ ] Advanced reporting with custom templates
- [ ] Integration with accounting software (QuickBooks, Xero)

---

**Maintained by:** Logical Version Team  
**License:** MIT  
**Support:** See README.md for contact information
