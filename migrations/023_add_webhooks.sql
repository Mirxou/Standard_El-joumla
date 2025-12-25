-- =====================================================
-- Migration 023: Webhooks Support
-- دعم Webhooks للأحداث
-- =====================================================

PRAGMA foreign_keys = ON;

-- =====================================================
-- 1. جدول Webhooks (إعدادات Webhooks)
-- =====================================================
CREATE TABLE IF NOT EXISTS webhooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                          -- اسم Webhook
    url TEXT NOT NULL,                            -- عنوان URL للـ Webhook
    event_type TEXT NOT NULL,                     -- نوع الحدث (sale_created, payment_received, purchase_created, etc.)
    http_method TEXT DEFAULT 'POST',              -- طريقة HTTP (POST, PUT, PATCH)
    headers TEXT,                                 -- Headers مخصصة (JSON)
    payload_template TEXT,                        -- قالب Payload (JSON template)
    is_active INTEGER DEFAULT 1,                 -- نشط/غير نشط
    retry_count INTEGER DEFAULT 3,                -- عدد محاولات إعادة الإرسال
    timeout_seconds INTEGER DEFAULT 30,          -- مهلة الانتظار (بالثواني)
    secret_key TEXT,                             -- Secret Key للتوقيع (اختياري)
    priority INTEGER DEFAULT 5,                  -- الأولوية (1=عاجل, 5=عادي, 10=منخفض)
    rate_limit_per_minute INTEGER DEFAULT 60,    -- حد الإرسال (عدد الطلبات في الدقيقة)
    company_id INTEGER,                           -- معرف الشركة (Multi-Company Support)
    created_by INTEGER,                           -- المستخدم الذي أنشأ Webhook
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    
    -- فهرس لتحسين البحث حسب نوع الحدث
    UNIQUE(company_id, name)                     -- ضمان عدم تكرار الاسم في نفس الشركة
);

-- =====================================================
-- 2. جدول Webhook Logs (سجل محاولات الإرسال)
-- =====================================================
CREATE TABLE IF NOT EXISTS webhook_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    webhook_id INTEGER NOT NULL,                 -- معرف Webhook
    event_type TEXT NOT NULL,                     -- نوع الحدث
    entity_id INTEGER,                            -- معرف الكيان (sale_id, payment_id, etc.)
    payload TEXT NOT NULL,                        -- Payload المرسل (JSON)
    response_status INTEGER,                       -- كود حالة الاستجابة (200, 404, 500, etc.)
    response_body TEXT,                           -- نص الاستجابة
    error_message TEXT,                            -- رسالة الخطأ (إن وجدت)
    attempt_number INTEGER DEFAULT 1,            -- رقم المحاولة
    is_success INTEGER DEFAULT 0,                -- نجح/فشل
    execution_time_ms INTEGER,                    -- وقت التنفيذ (بالميلي ثانية)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (webhook_id) REFERENCES webhooks(id) ON DELETE CASCADE
);

-- =====================================================
-- 3. Indexes لتحسين الأداء
-- =====================================================

-- فهرس للبحث حسب نوع الحدث والشركة
CREATE INDEX IF NOT EXISTS idx_webhooks_event_company 
    ON webhooks(event_type, company_id, is_active);

-- فهرس للبحث حسب Webhook ID في السجلات
CREATE INDEX IF NOT EXISTS idx_webhook_logs_webhook 
    ON webhook_logs(webhook_id, created_at DESC);

-- فهرس للبحث حسب نوع الحدث في السجلات
CREATE INDEX IF NOT EXISTS idx_webhook_logs_event 
    ON webhook_logs(event_type, created_at DESC);

-- فهرس للبحث حسب حالة النجاح
CREATE INDEX IF NOT EXISTS idx_webhook_logs_success 
    ON webhook_logs(is_success, created_at DESC);

-- =====================================================
-- 4. Trigger لتحديث updated_at تلقائياً
-- =====================================================
CREATE TRIGGER IF NOT EXISTS update_webhooks_updated_at
    AFTER UPDATE ON webhooks
    FOR EACH ROW
BEGIN
    UPDATE webhooks 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- =====================================================
-- 5. بيانات تجريبية (اختياري - يمكن حذفها)
-- =====================================================
-- يمكن إضافة بيانات تجريبية هنا إذا لزم الأمر

