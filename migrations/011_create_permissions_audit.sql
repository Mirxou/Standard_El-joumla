-- Migration: إنشاء نظام الصلاحيات والتدقيق
-- Create Permissions & Audit System

PRAGMA foreign_keys = ON;

-- ==================== Permissions ====================

-- جدول الصلاحيات
CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    resource_type TEXT NOT NULL,
    action TEXT NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_permissions_code ON permissions(code);
CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions(resource_type);

-- ==================== Roles ====================

-- جدول الأدوار
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    code TEXT NOT NULL UNIQUE,
    description TEXT,
    is_system BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_roles_code ON roles(code);
CREATE INDEX IF NOT EXISTS idx_roles_active ON roles(is_active);

-- ==================== Role Permissions ====================

-- جدول ربط الأدوار بالصلاحيات
CREATE TABLE IF NOT EXISTS role_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE(role_id, permission_id)
);

CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_perm ON role_permissions(permission_id);

-- ==================== Users ====================

-- جدول المستخدمين
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    password_hash TEXT NOT NULL,
    role_id INTEGER,
    status TEXT DEFAULT 'ACTIVE', -- ACTIVE, INACTIVE, SUSPENDED, LOCKED
    last_login TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    is_locked BOOLEAN DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL AND email != '';

-- ==================== Audit Logs ====================

-- جدول سجلات التدقيق
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id INTEGER,
    old_value TEXT, -- JSON
    new_value TEXT, -- JSON
    ip_address TEXT,
    user_agent TEXT,
    status TEXT DEFAULT 'success', -- success, failed, warning
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_date ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_status ON audit_logs(status);

-- ==================== Login History ====================

-- جدول سجل تسجيل الدخول
CREATE TABLE IF NOT EXISTS login_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT NOT NULL,
    status TEXT NOT NULL, -- success, failed
    ip_address TEXT,
    user_agent TEXT,
    failure_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_login_user ON login_history(user_id);
CREATE INDEX IF NOT EXISTS idx_login_username ON login_history(username);
CREATE INDEX IF NOT EXISTS idx_login_status ON login_history(status);
CREATE INDEX IF NOT EXISTS idx_login_date ON login_history(created_at);
CREATE INDEX IF NOT EXISTS idx_login_ip ON login_history(ip_address);

-- ==================== Views ====================

-- عرض المستخدمين مع الأدوار
CREATE VIEW IF NOT EXISTS v_users_with_roles AS
SELECT 
    u.id,
    u.username,
    u.full_name,
    u.email,
    u.phone,
    u.status,
    u.last_login,
    u.failed_login_attempts,
    u.is_locked,
    r.id as role_id,
    r.name as role_name,
    r.code as role_code
FROM users u
LEFT JOIN roles r ON u.role_id = r.id;

-- عرض الأدوار مع عدد الصلاحيات
CREATE VIEW IF NOT EXISTS v_roles_with_permissions_count AS
SELECT 
    r.id,
    r.name,
    r.code,
    r.description,
    r.is_system,
    r.is_active,
    COUNT(rp.permission_id) as permissions_count
FROM roles r
LEFT JOIN role_permissions rp ON r.id = rp.role_id
GROUP BY r.id;

-- عرض نشاط المستخدمين (آخر 30 يوم)
CREATE VIEW IF NOT EXISTS v_user_activity_summary AS
SELECT 
    u.id,
    u.username,
    u.full_name,
    u.last_login,
    COUNT(DISTINCT al.id) as total_actions,
    COUNT(DISTINCT CASE WHEN al.status = 'success' THEN al.id END) as successful_actions,
    COUNT(DISTINCT CASE WHEN al.status = 'failed' THEN al.id END) as failed_actions
FROM users u
LEFT JOIN audit_logs al ON u.id = al.user_id 
    AND al.created_at >= datetime('now', '-30 days')
GROUP BY u.id;

-- ==================== Triggers ====================

-- محفز تحديث وقت التعديل للأدوار
CREATE TRIGGER IF NOT EXISTS update_roles_timestamp 
AFTER UPDATE ON roles
FOR EACH ROW
BEGIN
    UPDATE roles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- محفز تحديث وقت التعديل للمستخدمين
CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- محفز تسجيل حذف المستخدم في سجل التدقيق
CREATE TRIGGER IF NOT EXISTS log_user_deletion
BEFORE DELETE ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, username, action, resource_type, resource_id, old_value, status)
    VALUES (
        OLD.id,
        OLD.username,
        'DELETE_USER',
        'USERS',
        OLD.id,
        json_object('username', OLD.username, 'full_name', OLD.full_name),
        'success'
    );
END;

-- محفز تسجيل تعديل دور المستخدم
CREATE TRIGGER IF NOT EXISTS log_user_role_change
AFTER UPDATE OF role_id ON users
FOR EACH ROW
WHEN OLD.role_id IS NOT NEW.role_id
BEGIN
    INSERT INTO audit_logs (user_id, username, action, resource_type, resource_id, old_value, new_value, status)
    VALUES (
        NEW.id,
        NEW.username,
        'UPDATE_USER_ROLE',
        'USERS',
        NEW.id,
        json_object('role_id', OLD.role_id),
        json_object('role_id', NEW.role_id),
        'success'
    );
END;
