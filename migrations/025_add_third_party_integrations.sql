-- ============================================================================
-- Migration 025: Add Third-party Integrations Support
-- دعم التكامل مع الأنظمة الخارجية (Payment Gateways, Shipping, Accounting)
-- ============================================================================
PRAGMA foreign_keys = ON;

-- ============================================================================
-- 1. جدول التكاملات (Integrations)
-- ============================================================================
CREATE TABLE IF NOT EXISTS integrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                          -- اسم التكامل
    integration_type TEXT NOT NULL,               -- نوع التكامل (PAYMENT_GATEWAY, SHIPPING, ACCOUNTING)
    provider TEXT NOT NULL,                       -- المزود (Stripe, PayPal, FedEx, DHL, QuickBooks, Xero)
    
    -- إعدادات الاتصال
    api_key TEXT,                                -- API Key
    api_secret TEXT,                             -- API Secret (مشفرة)
    api_url TEXT,                                -- API URL
    webhook_url TEXT,                            -- Webhook URL للاستقبال
    
    -- إعدادات إضافية (JSON)
    config TEXT,                                 -- إعدادات إضافية (JSON)
    
    -- حالة التفعيل
    is_active INTEGER DEFAULT 1,                 -- نشط/غير نشط
    is_test_mode INTEGER DEFAULT 1,              -- وضع الاختبار/الإنتاج
    
    -- Multi-Company Support
    company_id INTEGER,                          -- معرف الشركة
    
    -- التتبع
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    
    UNIQUE(company_id, name)                     -- ضمان عدم تكرار الاسم في نفس الشركة
);

-- ============================================================================
-- 2. جدول معاملات Payment Gateway (Payment Gateway Transactions)
-- ============================================================================
CREATE TABLE IF NOT EXISTS payment_gateway_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    integration_id INTEGER NOT NULL,              -- معرف التكامل
    
    -- معلومات المعاملة
    transaction_id TEXT NOT NULL,                 -- معرف المعاملة من Gateway
    transaction_type TEXT NOT NULL,               -- نوع المعاملة (CHARGE, REFUND, VOID)
    amount DECIMAL(15, 2) NOT NULL,              -- المبلغ
    currency TEXT DEFAULT 'DZD',                 -- العملة
    
    -- الحالة
    status TEXT NOT NULL DEFAULT 'PENDING',       -- PENDING, SUCCESS, FAILED, CANCELLED
    gateway_status TEXT,                         -- حالة من Gateway
    
    -- المراجع
    payment_id INTEGER,                           -- معرف الدفعة في النظام
    sale_id INTEGER,                             -- معرف فاتورة المبيعات
    customer_id INTEGER,                          -- معرف العميل
    
    -- معلومات إضافية
    gateway_response TEXT,                        -- استجابة Gateway (JSON)
    error_message TEXT,                           -- رسالة الخطأ (إن وجدت)
    
    -- التتبع
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (integration_id) REFERENCES integrations(id) ON DELETE CASCADE,
    FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE SET NULL,
    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE SET NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    
    UNIQUE(integration_id, transaction_id)        -- ضمان عدم تكرار المعاملة
);

-- ============================================================================
-- 3. جدول شحنات Shipping (Shipping Shipments)
-- ============================================================================
CREATE TABLE IF NOT EXISTS shipping_shipments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    integration_id INTEGER NOT NULL,              -- معرف التكامل
    
    -- معلومات الشحنة
    shipment_id TEXT NOT NULL,                   -- معرف الشحنة من Provider
    tracking_number TEXT,                        -- رقم التتبع
    carrier TEXT,                                 -- الناقل
    
    -- المراجع
    sale_id INTEGER,                             -- معرف فاتورة المبيعات
    customer_id INTEGER,                          -- معرف العميل
    
    -- معلومات الشحن
    origin_address TEXT,                          -- عنوان المنشأ
    destination_address TEXT,                     -- عنوان الوجهة
    weight DECIMAL(10, 2),                       -- الوزن (كجم)
    dimensions TEXT,                             -- الأبعاد (JSON)
    
    -- الحالة
    status TEXT NOT NULL DEFAULT 'PENDING',      -- PENDING, IN_TRANSIT, DELIVERED, CANCELLED
    shipping_status TEXT,                        -- حالة الشحن من Provider
    
    -- التكلفة
    shipping_cost DECIMAL(15, 2),                -- تكلفة الشحن
    currency TEXT DEFAULT 'DZD',                 -- العملة
    
    -- معلومات إضافية
    provider_response TEXT,                      -- استجابة Provider (JSON)
    estimated_delivery_date DATE,                -- تاريخ التسليم المتوقع
    actual_delivery_date DATE,                  -- تاريخ التسليم الفعلي
    
    -- التتبع
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (integration_id) REFERENCES integrations(id) ON DELETE CASCADE,
    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE SET NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    
    UNIQUE(integration_id, shipment_id)          -- ضمان عدم تكرار الشحنة
);

-- ============================================================================
-- 4. جدول مزامنة المحاسبة (Accounting Sync)
-- ============================================================================
CREATE TABLE IF NOT EXISTS accounting_sync (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    integration_id INTEGER NOT NULL,              -- معرف التكامل
    
    -- معلومات المزامنة
    sync_type TEXT NOT NULL,                     -- نوع المزامنة (SALE, PURCHASE, PAYMENT, INVOICE)
    entity_type TEXT NOT NULL,                   -- نوع الكيان (SALE, PURCHASE, PAYMENT)
    entity_id INTEGER NOT NULL,                  -- معرف الكيان
    
    -- حالة المزامنة
    status TEXT NOT NULL DEFAULT 'PENDING',       -- PENDING, SYNCED, FAILED
    sync_status TEXT,                           -- حالة المزامنة من Provider
    
    -- معلومات إضافية
    provider_id TEXT,                            -- معرف في Provider
    provider_response TEXT,                      -- استجابة Provider (JSON)
    error_message TEXT,                          -- رسالة الخطأ (إن وجدت)
    
    -- التتبع
    synced_at DATETIME,                         -- تاريخ المزامنة
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (integration_id) REFERENCES integrations(id) ON DELETE CASCADE,
    
    UNIQUE(integration_id, entity_type, entity_id) -- ضمان عدم تكرار المزامنة
);

-- ============================================================================
-- 5. جدول سجلات التكامل (Integration Logs)
-- ============================================================================
CREATE TABLE IF NOT EXISTS integration_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    integration_id INTEGER NOT NULL,             -- معرف التكامل
    
    -- معلومات السجل
    log_type TEXT NOT NULL,                      -- نوع السجل (REQUEST, RESPONSE, ERROR, WEBHOOK)
    operation TEXT NOT NULL,                     -- العملية (CHARGE, SHIP, SYNC, etc.)
    
    -- المحتوى
    request_data TEXT,                           -- بيانات الطلب (JSON)
    response_data TEXT,                          -- بيانات الاستجابة (JSON)
    error_message TEXT,                          -- رسالة الخطأ (إن وجدت)
    
    -- الأداء
    execution_time_ms INTEGER,                   -- وقت التنفيذ (بالميلي ثانية)
    
    -- التتبع
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (integration_id) REFERENCES integrations(id) ON DELETE CASCADE
);

-- ============================================================================
-- Indexes للأداء
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_integrations_type ON integrations(integration_type);
CREATE INDEX IF NOT EXISTS idx_integrations_provider ON integrations(provider);
CREATE INDEX IF NOT EXISTS idx_integrations_company ON integrations(company_id);
CREATE INDEX IF NOT EXISTS idx_integrations_active ON integrations(is_active);

CREATE INDEX IF NOT EXISTS idx_payment_gateway_transactions_integration ON payment_gateway_transactions(integration_id);
CREATE INDEX IF NOT EXISTS idx_payment_gateway_transactions_status ON payment_gateway_transactions(status);
CREATE INDEX IF NOT EXISTS idx_payment_gateway_transactions_payment ON payment_gateway_transactions(payment_id);
CREATE INDEX IF NOT EXISTS idx_payment_gateway_transactions_sale ON payment_gateway_transactions(sale_id);

CREATE INDEX IF NOT EXISTS idx_shipping_shipments_integration ON shipping_shipments(integration_id);
CREATE INDEX IF NOT EXISTS idx_shipping_shipments_status ON shipping_shipments(status);
CREATE INDEX IF NOT EXISTS idx_shipping_shipments_tracking ON shipping_shipments(tracking_number);
CREATE INDEX IF NOT EXISTS idx_shipping_shipments_sale ON shipping_shipments(sale_id);

CREATE INDEX IF NOT EXISTS idx_accounting_sync_integration ON accounting_sync(integration_id);
CREATE INDEX IF NOT EXISTS idx_accounting_sync_status ON accounting_sync(status);
CREATE INDEX IF NOT EXISTS idx_accounting_sync_entity ON accounting_sync(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_integration_logs_integration ON integration_logs(integration_id);
CREATE INDEX IF NOT EXISTS idx_integration_logs_type ON integration_logs(log_type);
CREATE INDEX IF NOT EXISTS idx_integration_logs_created ON integration_logs(created_at);

-- ============================================================================
-- Triggers لتحديث updated_at
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS update_integrations_updated_at
    AFTER UPDATE ON integrations
    FOR EACH ROW
BEGIN
    UPDATE integrations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_payment_gateway_transactions_updated_at
    AFTER UPDATE ON payment_gateway_transactions
    FOR EACH ROW
BEGIN
    UPDATE payment_gateway_transactions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_shipping_shipments_updated_at
    AFTER UPDATE ON shipping_shipments
    FOR EACH ROW
BEGIN
    UPDATE shipping_shipments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_accounting_sync_updated_at
    AFTER UPDATE ON accounting_sync
    FOR EACH ROW
BEGIN
    UPDATE accounting_sync SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

