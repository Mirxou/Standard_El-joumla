-- ============================================================================
-- Migration 024: Add EDI Support
-- دعم EDI للطلبات والفواتير (EDIFACT, X12)
-- ============================================================================
PRAGMA foreign_keys = ON;

-- ============================================================================
-- 1. جدول شركاء EDI (EDI Partners)
-- ============================================================================
CREATE TABLE IF NOT EXISTS edi_partners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                          -- اسم الشريك
    partner_code TEXT NOT NULL,                   -- كود الشريك (EDI ID)
    partner_type TEXT NOT NULL DEFAULT 'SUPPLIER', -- نوع الشريك (SUPPLIER, CUSTOMER, BOTH)
    
    -- معلومات الاتصال
    contact_name TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    
    -- إعدادات EDI
    edi_standard TEXT NOT NULL DEFAULT 'EDIFACT', -- المعيار (EDIFACT, X12)
    edi_version TEXT DEFAULT 'D96A',               -- إصدار EDI (EDIFACT: D96A, D01B, etc.)
    interchange_id TEXT,                          -- Interchange ID
    sender_id TEXT,                               -- Sender ID
    receiver_id TEXT,                             -- Receiver ID
    
    -- أنواع المستندات المدعومة
    supports_orders INTEGER DEFAULT 1,            -- يدعم أوامر الشراء (850)
    supports_invoices INTEGER DEFAULT 1,           -- يدعم الفواتير (810)
    supports_acknowledgments INTEGER DEFAULT 1,   -- يدعم الإقرارات (855, 997)
    supports_asn INTEGER DEFAULT 0,               -- يدعم Advanced Shipping Notice (856)
    
    -- إعدادات الاتصال
    connection_type TEXT DEFAULT 'FILE',          -- نوع الاتصال (FILE, FTP, SFTP, AS2, API)
    file_path TEXT,                               -- مسار الملفات (لـ FILE)
    ftp_host TEXT,                                -- FTP Host
    ftp_port INTEGER DEFAULT 21,                  -- FTP Port
    ftp_username TEXT,                            -- FTP Username
    ftp_password TEXT,                            -- FTP Password (مشفرة)
    ftp_directory TEXT,                           -- FTP Directory
    
    -- إعدادات الأمان
    encryption_method TEXT,                       -- طريقة التشفير (PGP, SSL, etc.)
    signature_method TEXT,                        -- طريقة التوقيع (HMAC, RSA, etc.)
    public_key TEXT,                             -- Public Key للشريك
    
    -- حالة التفعيل
    is_active INTEGER DEFAULT 1,                 -- نشط/غير نشط
    auto_process INTEGER DEFAULT 0,               -- معالجة تلقائية
    
    -- Multi-Company Support
    company_id INTEGER,                           -- معرف الشركة
    
    -- التتبع
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    
    UNIQUE(company_id, partner_code)              -- ضمان عدم تكرار الكود في نفس الشركة
);

-- ============================================================================
-- 2. جدول مستندات EDI (EDI Documents)
-- ============================================================================
CREATE TABLE IF NOT EXISTS edi_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_type TEXT NOT NULL,                  -- نوع المستند (850, 810, 855, 856, 997, etc.)
    document_number TEXT NOT NULL,                -- رقم المستند
    partner_id INTEGER NOT NULL,                   -- معرف الشريك
    
    -- حالة المستند
    status TEXT NOT NULL DEFAULT 'PENDING',       -- PENDING, PROCESSED, ERROR, ACKNOWLEDGED
    direction TEXT NOT NULL,                      -- INBOUND (وارد), OUTBOUND (صادر)
    
    -- المحتوى
    raw_content TEXT NOT NULL,                    -- المحتوى الخام (EDI Format)
    parsed_content TEXT,                          -- المحتوى المحلل (JSON)
    
    -- المراجع
    related_po_id INTEGER,                        -- معرف أمر الشراء المرتبط
    related_invoice_id INTEGER,                   -- معرف الفاتورة المرتبطة
    related_sale_id INTEGER,                      -- معرف فاتورة المبيعات المرتبطة
    
    -- معلومات الإرسال/الاستلام
    sent_at DATETIME,                            -- تاريخ الإرسال
    received_at DATETIME,                        -- تاريخ الاستلام
    processed_at DATETIME,                        -- تاريخ المعالجة
    acknowledged_at DATETIME,                    -- تاريخ الإقرار
    
    -- الأخطاء
    error_message TEXT,                          -- رسالة الخطأ (إن وجدت)
    error_details TEXT,                          -- تفاصيل الخطأ
    
    -- التحقق
    is_valid INTEGER DEFAULT 1,                 -- صحيح/غير صحيح
    validation_errors TEXT,                      -- أخطاء التحقق (JSON)
    
    -- Multi-Company Support
    company_id INTEGER,                          -- معرف الشركة
    
    -- التتبع
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (partner_id) REFERENCES edi_partners(id) ON DELETE CASCADE,
    FOREIGN KEY (related_po_id) REFERENCES purchase_orders(id) ON DELETE SET NULL,
    FOREIGN KEY (related_invoice_id) REFERENCES purchases(id) ON DELETE SET NULL,
    FOREIGN KEY (related_sale_id) REFERENCES sales(id) ON DELETE SET NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    
    UNIQUE(partner_id, document_type, document_number) -- ضمان عدم التكرار
);

-- ============================================================================
-- 3. جدول Mapping EDI (EDI Mappings)
-- ============================================================================
CREATE TABLE IF NOT EXISTS edi_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                          -- اسم الـ Mapping
    document_type TEXT NOT NULL,                 -- نوع المستند (850, 810, etc.)
    partner_id INTEGER,                           -- معرف الشريك (NULL = عام)
    
    -- Mapping Rules (JSON)
    field_mappings TEXT NOT NULL,                -- قواعد Mapping (JSON)
    transformation_rules TEXT,                   -- قواعد التحويل (JSON)
    validation_rules TEXT,                       -- قواعد التحقق (JSON)
    
    -- حالة التفعيل
    is_active INTEGER DEFAULT 1,                 -- نشط/غير نشط
    is_default INTEGER DEFAULT 0,               -- افتراضي
    
    -- Multi-Company Support
    company_id INTEGER,                          -- معرف الشركة
    
    -- التتبع
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (partner_id) REFERENCES edi_partners(id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    
    UNIQUE(company_id, name)                     -- ضمان عدم تكرار الاسم في نفس الشركة
);

-- ============================================================================
-- 4. جدول سجلات معالجة EDI (EDI Processing Logs)
-- ============================================================================
CREATE TABLE IF NOT EXISTS edi_processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,                 -- معرف المستند
    partner_id INTEGER NOT NULL,                  -- معرف الشريك
    
    -- معلومات المعالجة
    operation_type TEXT NOT NULL,                 -- نوع العملية (PARSE, GENERATE, VALIDATE, SEND, RECEIVE)
    status TEXT NOT NULL,                        -- الحالة (SUCCESS, ERROR, WARNING)
    
    -- التفاصيل
    message TEXT,                                -- الرسالة
    details TEXT,                                -- التفاصيل (JSON)
    execution_time_ms INTEGER,                   -- وقت التنفيذ (بالميلي ثانية)
    
    -- التتبع
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (document_id) REFERENCES edi_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (partner_id) REFERENCES edi_partners(id) ON DELETE CASCADE
);

-- ============================================================================
-- Indexes للأداء
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_edi_partners_company ON edi_partners(company_id);
CREATE INDEX IF NOT EXISTS idx_edi_partners_code ON edi_partners(partner_code);
CREATE INDEX IF NOT EXISTS idx_edi_partners_type ON edi_partners(partner_type);

CREATE INDEX IF NOT EXISTS idx_edi_documents_partner ON edi_documents(partner_id);
CREATE INDEX IF NOT EXISTS idx_edi_documents_type ON edi_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_edi_documents_status ON edi_documents(status);
CREATE INDEX IF NOT EXISTS idx_edi_documents_direction ON edi_documents(direction);
CREATE INDEX IF NOT EXISTS idx_edi_documents_company ON edi_documents(company_id);
CREATE INDEX IF NOT EXISTS idx_edi_documents_po ON edi_documents(related_po_id);
CREATE INDEX IF NOT EXISTS idx_edi_documents_invoice ON edi_documents(related_invoice_id);

CREATE INDEX IF NOT EXISTS idx_edi_mappings_partner ON edi_mappings(partner_id);
CREATE INDEX IF NOT EXISTS idx_edi_mappings_type ON edi_mappings(document_type);
CREATE INDEX IF NOT EXISTS idx_edi_mappings_company ON edi_mappings(company_id);

CREATE INDEX IF NOT EXISTS idx_edi_logs_document ON edi_processing_logs(document_id);
CREATE INDEX IF NOT EXISTS idx_edi_logs_partner ON edi_processing_logs(partner_id);
CREATE INDEX IF NOT EXISTS idx_edi_logs_status ON edi_processing_logs(status);
CREATE INDEX IF NOT EXISTS idx_edi_logs_created ON edi_processing_logs(created_at);

-- ============================================================================
-- Trigger لتحديث updated_at
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS update_edi_partners_updated_at
    AFTER UPDATE ON edi_partners
    FOR EACH ROW
BEGIN
    UPDATE edi_partners SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_edi_documents_updated_at
    AFTER UPDATE ON edi_documents
    FOR EACH ROW
BEGIN
    UPDATE edi_documents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_edi_mappings_updated_at
    AFTER UPDATE ON edi_mappings
    FOR EACH ROW
BEGIN
    UPDATE edi_mappings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

