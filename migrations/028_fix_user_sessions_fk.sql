-- Migration: Fix foreign keys referencing users table
-- إصلاح Foreign Keys التي تشير إلى جدول users
-- المشكلة: بعض الجداول تشير إلى users(user_id) بينما العمود الصحيح هو users(id)

PRAGMA foreign_keys = OFF;

-- ============================================================================
-- 1. إصلاح user_sessions
-- ============================================================================
-- إنشاء جدول مؤقت
CREATE TABLE IF NOT EXISTS user_sessions_temp (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_time TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- نسخ البيانات
INSERT OR IGNORE INTO user_sessions_temp 
SELECT * FROM user_sessions WHERE EXISTS (SELECT 1 FROM user_sessions LIMIT 1);

-- حذف وإعادة تسمية
DROP TABLE IF EXISTS user_sessions;
ALTER TABLE user_sessions_temp RENAME TO user_sessions;

-- إعادة إنشاء الفهارس
CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_active ON user_sessions(user_id, is_active, last_activity DESC) WHERE is_active = 1;
CREATE INDEX IF NOT EXISTS idx_sessions_last_activity ON user_sessions(last_activity) WHERE is_active = 1;
CREATE INDEX IF NOT EXISTS idx_sessions_ip_active ON user_sessions(ip_address, is_active, login_time DESC) WHERE ip_address IS NOT NULL;

-- ============================================================================
-- 2. إصلاح role_permissions
-- ============================================================================
-- إنشاء جدول مؤقت
CREATE TABLE IF NOT EXISTS role_permissions_temp (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(permission_id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL
);

-- نسخ البيانات
INSERT OR IGNORE INTO role_permissions_temp 
SELECT * FROM role_permissions WHERE EXISTS (SELECT 1 FROM role_permissions LIMIT 1);

-- حذف وإعادة تسمية
DROP TABLE IF EXISTS role_permissions;
ALTER TABLE role_permissions_temp RENAME TO role_permissions;

-- إعادة إنشاء الفهارس
CREATE INDEX IF NOT EXISTS idx_role_perms_role ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_perms_perm ON role_permissions(permission_id);

-- ============================================================================
-- 3. إصلاح user_roles
-- ============================================================================
-- إنشاء جدول مؤقت
CREATE TABLE IF NOT EXISTS user_roles_temp (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER,
    expires_at TIMESTAMP,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE SET NULL
);

-- نسخ البيانات
INSERT OR IGNORE INTO user_roles_temp (user_id, role_id, assigned_at, assigned_by)
SELECT user_id, role_id, assigned_at, NULL FROM user_roles WHERE EXISTS (SELECT 1 FROM user_roles LIMIT 1);

-- حذف وإعادة تسمية
DROP TABLE IF EXISTS user_roles;
ALTER TABLE user_roles_temp RENAME TO user_roles;

-- إعادة إنشاء الفهارس
CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id);

-- ============================================================================
-- 4. إصلاح audit_log
-- ============================================================================
-- إنشاء جدول مؤقت
CREATE TABLE IF NOT EXISTS audit_log_temp (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT NOT NULL,
    action TEXT NOT NULL,
    module TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    old_values TEXT,
    new_values TEXT,
    changes_summary TEXT,
    ip_address TEXT,
    user_agent TEXT,
    session_id TEXT,
    status TEXT DEFAULT 'success',
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- نسخ البيانات
INSERT OR IGNORE INTO audit_log_temp (
    audit_id, user_id, action, module, entity_id, old_values, new_values, timestamp,
    username, entity_type, status
)
SELECT 
    id, user_id, action, table_name, record_id, old_values, new_values, timestamp,
    'System', table_name, 'success'
FROM audit_log WHERE EXISTS (SELECT 1 FROM audit_log LIMIT 1);

-- حذف وإعادة تسمية
DROP TABLE IF EXISTS audit_log;
ALTER TABLE audit_log_temp RENAME TO audit_log;

-- إعادة إنشاء الفهارس
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_module ON audit_log(module);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_status ON audit_log(status);
CREATE INDEX IF NOT EXISTS idx_audit_user_time ON audit_log(user_id, timestamp DESC);

PRAGMA foreign_keys = ON;

