-- Migration: إنشاء جداول إدارة النظام والصيانة
-- Create System Management & Maintenance Tables

PRAGMA foreign_keys = ON;

-- ==================== Backup History ====================

-- جدول سجل النسخ الاحتياطية
CREATE TABLE IF NOT EXISTS backup_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_name TEXT NOT NULL,
    description TEXT,
    size_bytes INTEGER,
    files_count INTEGER,
    backup_type TEXT DEFAULT 'manual', -- manual, automatic
    status TEXT DEFAULT 'completed', -- completed, failed, in_progress
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_backup_history_date ON backup_history(created_at);
CREATE INDEX IF NOT EXISTS idx_backup_history_type ON backup_history(backup_type);

-- ==================== Restore History ====================

-- جدول سجل عمليات الاستعادة
CREATE TABLE IF NOT EXISTS restore_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_name TEXT NOT NULL,
    restored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    restored_by INTEGER,
    status TEXT DEFAULT 'completed', -- completed, failed
    error_message TEXT,
    FOREIGN KEY (restored_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_restore_history_date ON restore_history(restored_at);

-- ==================== System Maintenance ====================

-- جدول سجل الصيانة
CREATE TABLE IF NOT EXISTS maintenance_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_type TEXT NOT NULL, -- optimize, vacuum, analyze, repair, cleanup
    status TEXT DEFAULT 'completed', -- completed, failed, in_progress
    execution_time_seconds REAL,
    details TEXT, -- JSON
    error_message TEXT,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    performed_by INTEGER,
    FOREIGN KEY (performed_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_maintenance_log_type ON maintenance_log(operation_type);
CREATE INDEX IF NOT EXISTS idx_maintenance_log_date ON maintenance_log(performed_at);

-- ==================== System Settings ====================

-- جدول إعدادات النظام
CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL, -- general, backup, performance, security
    key TEXT NOT NULL UNIQUE,
    value TEXT,
    data_type TEXT DEFAULT 'string', -- string, integer, boolean, json
    description TEXT,
    is_system BOOLEAN DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_system_settings_category ON system_settings(category);
CREATE UNIQUE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(key);

-- ==================== Performance Metrics ====================

-- جدول مقاييس الأداء
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_unit TEXT, -- ms, mb, count, percent
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_performance_metrics_name ON performance_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_date ON performance_metrics(recorded_at);

-- ==================== Default Settings ====================

-- إدخال الإعدادات الافتراضية
INSERT OR IGNORE INTO system_settings (category, key, value, data_type, description, is_system) VALUES
-- General Settings
('general', 'app_version', '1.0.0', 'string', 'إصدار التطبيق', 1),
('general', 'db_version', '1.0', 'string', 'إصدار قاعدة البيانات', 1),
('general', 'company_name', 'شركة التجارة العامة', 'string', 'اسم الشركة', 0),
('general', 'company_address', '', 'string', 'عنوان الشركة', 0),
('general', 'company_phone', '', 'string', 'هاتف الشركة', 0),
('general', 'company_email', '', 'string', 'بريد الشركة الإلكتروني', 0),
('general', 'tax_number', '', 'string', 'الرقم الضريبي', 0),
('general', 'commercial_registration', '', 'string', 'رقم السجل التجاري', 0),

-- Backup Settings
('backup', 'auto_backup_enabled', 'false', 'boolean', 'تفعيل النسخ الاحتياطي التلقائي', 0),
('backup', 'auto_backup_interval_hours', '24', 'integer', 'فترة النسخ الاحتياطي التلقائي (بالساعات)', 0),
('backup', 'backup_keep_count', '10', 'integer', 'عدد النسخ الاحتياطية المحتفظ بها', 0),
('backup', 'backup_keep_days', '30', 'integer', 'مدة الاحتفاظ بالنسخ (بالأيام)', 0),
('backup', 'backup_compress', 'true', 'boolean', 'ضغط النسخ الاحتياطية', 0),

-- Performance Settings
('performance', 'auto_optimize_enabled', 'true', 'boolean', 'تفعيل التحسين التلقائي', 0),
('performance', 'optimize_interval_days', '7', 'integer', 'فترة التحسين التلقائي (بالأيام)', 0),
('performance', 'cleanup_old_logs_days', '90', 'integer', 'حذف السجلات القديمة بعد (أيام)', 0),
('performance', 'cache_size_mb', '64', 'integer', 'حجم الذاكرة المؤقتة (ميغابايت)', 0),

-- Security Settings
('security', 'password_min_length', '6', 'integer', 'الحد الأدنى لطول كلمة المرور', 0),
('security', 'password_require_uppercase', 'false', 'boolean', 'طلب أحرف كبيرة في كلمة المرور', 0),
('security', 'password_require_numbers', 'false', 'boolean', 'طلب أرقام في كلمة المرور', 0),
('security', 'password_require_special', 'false', 'boolean', 'طلب رموز خاصة في كلمة المرور', 0),
('security', 'max_login_attempts', '5', 'integer', 'الحد الأقصى لمحاولات تسجيل الدخول', 0),
('security', 'account_lockout_minutes', '30', 'integer', 'مدة قفل الحساب (بالدقائق)', 0),
('security', 'session_timeout_minutes', '480', 'integer', 'مدة انتهاء الجلسة (بالدقائق)', 0),
('security', 'enable_audit_log', 'true', 'boolean', 'تفعيل سجل التدقيق', 0);

-- ==================== Views ====================

-- عرض إحصائيات النسخ الاحتياطية
CREATE VIEW IF NOT EXISTS v_backup_statistics AS
SELECT 
    COUNT(*) as total_backups,
    COUNT(CASE WHEN backup_type = 'automatic' THEN 1 END) as automatic_backups,
    COUNT(CASE WHEN backup_type = 'manual' THEN 1 END) as manual_backups,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_backups,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_backups,
    SUM(size_bytes) as total_size_bytes,
    AVG(size_bytes) as average_size_bytes,
    MAX(created_at) as last_backup_date,
    MIN(created_at) as first_backup_date
FROM backup_history;

-- عرض إحصائيات الصيانة
CREATE VIEW IF NOT EXISTS v_maintenance_statistics AS
SELECT 
    operation_type,
    COUNT(*) as operation_count,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_operations,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_operations,
    AVG(execution_time_seconds) as average_execution_time,
    MAX(performed_at) as last_operation_date
FROM maintenance_log
GROUP BY operation_type;

-- عرض مقاييس الأداء الأخيرة
CREATE VIEW IF NOT EXISTS v_latest_performance_metrics AS
SELECT 
    metric_name,
    metric_value,
    metric_unit,
    recorded_at
FROM performance_metrics pm1
WHERE recorded_at = (
    SELECT MAX(recorded_at)
    FROM performance_metrics pm2
    WHERE pm2.metric_name = pm1.metric_name
)
ORDER BY metric_name;

-- ==================== Triggers ====================

-- محفز تحديث وقت تعديل الإعدادات
CREATE TRIGGER IF NOT EXISTS update_system_settings_timestamp 
AFTER UPDATE ON system_settings
FOR EACH ROW
BEGIN
    UPDATE system_settings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- محفز تسجيل عمليات النسخ الاحتياطي في سجل التدقيق
CREATE TRIGGER IF NOT EXISTS log_backup_creation
AFTER INSERT ON backup_history
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, username, action, resource_type, resource_id, new_value, status)
    VALUES (
        NEW.created_by,
        COALESCE((SELECT username FROM users WHERE id = NEW.created_by), 'system'),
        'CREATE_BACKUP',
        'BACKUP',
        NEW.id,
        json_object('backup_name', NEW.backup_name, 'size', NEW.size_bytes),
        NEW.status
    );
END;

-- محفز تسجيل عمليات الاستعادة في سجل التدقيق
CREATE TRIGGER IF NOT EXISTS log_restore_operation
AFTER INSERT ON restore_history
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, username, action, resource_type, resource_id, new_value, status)
    VALUES (
        NEW.restored_by,
        COALESCE((SELECT username FROM users WHERE id = NEW.restored_by), 'system'),
        'RESTORE_BACKUP',
        'BACKUP',
        NEW.id,
        json_object('backup_name', NEW.backup_name),
        NEW.status
    );
END;

-- محفز تسجيل عمليات الصيانة
CREATE TRIGGER IF NOT EXISTS log_maintenance_operation
AFTER INSERT ON maintenance_log
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, username, action, resource_type, new_value, status)
    VALUES (
        NEW.performed_by,
        COALESCE((SELECT username FROM users WHERE id = NEW.performed_by), 'system'),
        'MAINTENANCE_' || UPPER(NEW.operation_type),
        'SYSTEM',
        json_object('operation', NEW.operation_type, 'execution_time', NEW.execution_time_seconds),
        NEW.status
    );
END;

-- محفز حذف النسخ الاحتياطية القديمة تلقائياً
-- ملاحظة: هذا محفز مثال - يمكن تحسينه بجدولة خارجية
CREATE TRIGGER IF NOT EXISTS cleanup_old_backups
AFTER INSERT ON backup_history
FOR EACH ROW
WHEN (SELECT COUNT(*) FROM backup_history) > 50
BEGIN
    DELETE FROM backup_history
    WHERE id IN (
        SELECT id FROM backup_history
        WHERE backup_type = 'automatic'
        ORDER BY created_at ASC
        LIMIT (SELECT COUNT(*) FROM backup_history WHERE backup_type = 'automatic') - 
              CAST((SELECT value FROM system_settings WHERE key = 'backup_keep_count') AS INTEGER)
    );
END;
