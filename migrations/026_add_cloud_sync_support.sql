-- ============================================================================
-- Migration 026: Add Cloud Sync Support
-- دعم المزامنة السحابية والنسخ الاحتياطي التلقائي
-- ============================================================================
PRAGMA foreign_keys = ON;

-- ============================================================================
-- 1. جدول إعدادات Cloud Sync (Cloud Sync Settings)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cloud_sync_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                          -- اسم الإعداد
    provider TEXT NOT NULL,                       -- المزود (AWS_S3, GOOGLE_CLOUD, AZURE_BLOB, LOCAL)
    
    -- إعدادات الاتصال
    access_key TEXT,                              -- Access Key
    secret_key TEXT,                              -- Secret Key (مشفرة)
    bucket_name TEXT,                             -- اسم Bucket/Container
    region TEXT,                                  -- المنطقة (لـ AWS/Azure)
    endpoint_url TEXT,                            -- Endpoint URL (لـ S3-compatible)
    
    -- إعدادات المزامنة
    sync_enabled INTEGER DEFAULT 0,               -- تفعيل المزامنة
    auto_sync INTEGER DEFAULT 0,                  -- مزامنة تلقائية
    sync_interval_minutes INTEGER DEFAULT 60,     -- فترة المزامنة (بالدقائق)
    last_sync_at DATETIME,                       -- آخر مزامنة
    
    -- إعدادات النسخ الاحتياطي
    backup_enabled INTEGER DEFAULT 0,            -- تفعيل النسخ الاحتياطي
    auto_backup INTEGER DEFAULT 0,                -- نسخ احتياطي تلقائي
    backup_interval_hours INTEGER DEFAULT 24,     -- فترة النسخ الاحتياطي (بالساعات)
    backup_time TEXT,                            -- وقت النسخ الاحتياطي (HH:MM)
    last_backup_at DATETIME,                     -- آخر نسخ احتياطي
    
    -- إعدادات التشفير
    encryption_enabled INTEGER DEFAULT 1,         -- تفعيل التشفير
    encryption_key TEXT,                          -- مفتاح التشفير (مشفرة)
    
    -- إعدادات إضافية (JSON)
    config TEXT,                                 -- إعدادات إضافية (JSON)
    
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
-- 2. جدول سجلات المزامنة (Sync Logs)
-- ============================================================================
CREATE TABLE IF NOT EXISTS sync_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_settings_id INTEGER NOT NULL,            -- معرف إعدادات المزامنة
    
    -- معلومات المزامنة
    sync_type TEXT NOT NULL,                     -- نوع المزامنة (UPLOAD, DOWNLOAD, FULL_SYNC)
    entity_type TEXT,                            -- نوع الكيان (SALE, PURCHASE, PRODUCT, etc.)
    entity_id INTEGER,                            -- معرف الكيان
    
    -- الحالة
    status TEXT NOT NULL DEFAULT 'PENDING',       -- PENDING, IN_PROGRESS, SUCCESS, FAILED
    direction TEXT,                              -- الاتجاه (UP, DOWN, BOTH)
    
    -- التفاصيل
    local_hash TEXT,                             -- Hash المحلي
    remote_hash TEXT,                            -- Hash السحابي
    conflict_resolved INTEGER DEFAULT 0,         -- تم حل التعارض
    
    -- معلومات إضافية
    error_message TEXT,                         -- رسالة الخطأ (إن وجدت)
    sync_data TEXT,                              -- بيانات المزامنة (JSON)
    
    -- الأداء
    execution_time_ms INTEGER,                    -- وقت التنفيذ (بالميلي ثانية)
    data_size_bytes INTEGER,                      -- حجم البيانات (بالبايت)
    
    -- التتبع
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (sync_settings_id) REFERENCES cloud_sync_settings(id) ON DELETE CASCADE
);

-- ============================================================================
-- 3. جدول التعارضات (Sync Conflicts)
-- ============================================================================
CREATE TABLE IF NOT EXISTS sync_conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_settings_id INTEGER NOT NULL,            -- معرف إعدادات المزامنة
    
    -- معلومات التعارض
    entity_type TEXT NOT NULL,                   -- نوع الكيان
    entity_id INTEGER NOT NULL,                   -- معرف الكيان
    
    -- بيانات التعارض
    local_data TEXT NOT NULL,                    -- البيانات المحلية (JSON)
    remote_data TEXT NOT NULL,                   -- البيانات السحابية (JSON)
    local_version INTEGER NOT NULL,               -- إصدار محلي
    remote_version INTEGER NOT NULL,              -- إصدار سحابي
    
    -- الحالة
    status TEXT NOT NULL DEFAULT 'PENDING',       -- PENDING, RESOLVED, IGNORED
    resolution_strategy TEXT,                    -- استراتيجية الحل (LOCAL_WINS, REMOTE_WINS, MANUAL_MERGE)
    
    -- الحل
    resolved_data TEXT,                          -- البيانات المحلولة (JSON)
    resolved_by INTEGER,                         -- المستخدم الذي حل التعارض
    resolved_at DATETIME,                        -- تاريخ الحل
    
    -- التتبع
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (sync_settings_id) REFERENCES cloud_sync_settings(id) ON DELETE CASCADE,
    FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL,
    
    UNIQUE(sync_settings_id, entity_type, entity_id) -- ضمان عدم تكرار التعارض
);

-- ============================================================================
-- 4. جدول النسخ الاحتياطي السحابي (Cloud Backups)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cloud_backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_settings_id INTEGER NOT NULL,            -- معرف إعدادات المزامنة
    
    -- معلومات النسخة الاحتياطية
    backup_name TEXT NOT NULL,                   -- اسم النسخة الاحتياطية
    backup_type TEXT NOT NULL DEFAULT 'FULL',     -- نوع النسخة (FULL, INCREMENTAL)
    
    -- الملفات
    local_path TEXT,                             -- المسار المحلي
    remote_path TEXT NOT NULL,                   -- المسار السحابي
    
    -- الحالة
    status TEXT NOT NULL DEFAULT 'PENDING',       -- PENDING, UPLOADING, UPLOADED, FAILED
    upload_progress INTEGER DEFAULT 0,           -- تقدم الرفع (0-100)
    
    -- المعلومات
    file_size_bytes INTEGER,                     -- حجم الملف (بالبايت)
    file_hash TEXT,                              -- Hash الملف
    encryption_enabled INTEGER DEFAULT 1,         -- مشفر
    
    -- معلومات إضافية
    metadata TEXT,                               -- بيانات إضافية (JSON)
    error_message TEXT,                          -- رسالة الخطأ (إن وجدت)
    
    -- التتبع
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    uploaded_at DATETIME,
    
    FOREIGN KEY (sync_settings_id) REFERENCES cloud_sync_settings(id) ON DELETE CASCADE
);

-- ============================================================================
-- 5. جدول حالة المزامنة (Sync State)
-- ============================================================================
CREATE TABLE IF NOT EXISTS sync_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_settings_id INTEGER NOT NULL,            -- معرف إعدادات المزامنة
    
    -- حالة المزامنة
    entity_type TEXT NOT NULL,                   -- نوع الكيان
    entity_id INTEGER NOT NULL,                  -- معرف الكيان
    
    -- الإصدارات
    local_version INTEGER DEFAULT 1,              -- إصدار محلي
    remote_version INTEGER DEFAULT 1,             -- إصدار سحابي
    last_synced_at DATETIME,                     -- آخر مزامنة
    
    -- Hash للتحقق
    local_hash TEXT,                             -- Hash محلي
    remote_hash TEXT,                             -- Hash سحابي
    
    -- التتبع
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (sync_settings_id) REFERENCES cloud_sync_settings(id) ON DELETE CASCADE,
    
    UNIQUE(sync_settings_id, entity_type, entity_id) -- ضمان عدم التكرار
);

-- ============================================================================
-- Indexes للأداء
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_cloud_sync_settings_company ON cloud_sync_settings(company_id);
CREATE INDEX IF NOT EXISTS idx_cloud_sync_settings_provider ON cloud_sync_settings(provider);

CREATE INDEX IF NOT EXISTS idx_sync_logs_settings ON sync_logs(sync_settings_id);
CREATE INDEX IF NOT EXISTS idx_sync_logs_status ON sync_logs(status);
CREATE INDEX IF NOT EXISTS idx_sync_logs_entity ON sync_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_sync_logs_created ON sync_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_sync_conflicts_settings ON sync_conflicts(sync_settings_id);
CREATE INDEX IF NOT EXISTS idx_sync_conflicts_status ON sync_conflicts(status);
CREATE INDEX IF NOT EXISTS idx_sync_conflicts_entity ON sync_conflicts(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_cloud_backups_settings ON cloud_backups(sync_settings_id);
CREATE INDEX IF NOT EXISTS idx_cloud_backups_status ON cloud_backups(status);
CREATE INDEX IF NOT EXISTS idx_cloud_backups_created ON cloud_backups(created_at);

CREATE INDEX IF NOT EXISTS idx_sync_state_settings ON sync_state(sync_settings_id);
CREATE INDEX IF NOT EXISTS idx_sync_state_entity ON sync_state(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_sync_state_synced ON sync_state(last_synced_at);

-- ============================================================================
-- Triggers لتحديث updated_at
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS update_cloud_sync_settings_updated_at
    AFTER UPDATE ON cloud_sync_settings
    FOR EACH ROW
BEGIN
    UPDATE cloud_sync_settings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_sync_conflicts_updated_at
    AFTER UPDATE ON sync_conflicts
    FOR EACH ROW
BEGIN
    UPDATE sync_conflicts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_sync_state_updated_at
    AFTER UPDATE ON sync_state
    FOR EACH ROW
BEGIN
    UPDATE sync_state SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

