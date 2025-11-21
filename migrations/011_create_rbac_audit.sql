-- Migration 011: Enhanced RBAC and Audit Log System
-- Created: 2025-11-22
-- Description: Role-Based Access Control with comprehensive audit trail

-- ============================================================================
-- 1. ROLES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS roles (
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    is_system BOOLEAN DEFAULT 0,  -- System roles cannot be deleted
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. PERMISSIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS permissions (
    permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    permission_name TEXT NOT NULL UNIQUE,
    module TEXT NOT NULL,  -- sales, inventory, accounting, etc.
    action TEXT NOT NULL,  -- read, write, delete, approve, etc.
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 3. ROLE_PERMISSIONS (Many-to-Many)
-- ============================================================================
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(permission_id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES users(user_id)
);

-- ============================================================================
-- 4. USER_ROLES (Many-to-Many)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER,
    expires_at TIMESTAMP,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES users(user_id)
);

-- ============================================================================
-- 5. AUDIT_LOG TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT NOT NULL,
    action TEXT NOT NULL,
    module TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    old_values TEXT,  -- JSON
    new_values TEXT,  -- JSON
    changes_summary TEXT,  -- Auto-computed diff
    ip_address TEXT,
    user_agent TEXT,
    session_id TEXT,
    status TEXT DEFAULT 'success',  -- success, failed, warning
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- ============================================================================
-- 6. USER_SESSIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_time TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Roles indexes
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(role_name);
CREATE INDEX IF NOT EXISTS idx_roles_active ON roles(is_active);

-- Permissions indexes
CREATE INDEX IF NOT EXISTS idx_permissions_name ON permissions(permission_name);
CREATE INDEX IF NOT EXISTS idx_permissions_module ON permissions(module);
CREATE INDEX IF NOT EXISTS idx_permissions_action ON permissions(action);
CREATE INDEX IF NOT EXISTS idx_permissions_module_action ON permissions(module, action);

-- Role permissions indexes
CREATE INDEX IF NOT EXISTS idx_role_perms_role ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_perms_perm ON role_permissions(permission_id);

-- User roles indexes
CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role ON user_roles(role_id);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_module ON audit_log(module);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_status ON audit_log(status);
CREATE INDEX IF NOT EXISTS idx_audit_user_time ON audit_log(user_id, timestamp DESC);

-- Sessions indexes
CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON user_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_login ON user_sessions(login_time DESC);

-- ============================================================================
-- DEFAULT ROLES
-- ============================================================================
INSERT OR IGNORE INTO roles (role_name, display_name, description, is_system) VALUES
('admin', 'مدير النظام', 'صلاحيات كاملة على جميع الوحدات', 1),
('manager', 'مدير', 'إدارة المبيعات والمخزون والتقارير', 1),
('accountant', 'محاسب', 'صلاحيات المحاسبة والتقارير المالية', 1),
('sales_rep', 'مندوب مبيعات', 'إنشاء فواتير المبيعات فقط', 1),
('inventory_clerk', 'أمين مخزن', 'إدارة المخزون والاستلام', 1),
('viewer', 'عارض', 'عرض البيانات فقط بدون تعديل', 1);

-- ============================================================================
-- DEFAULT PERMISSIONS
-- ============================================================================

-- Sales permissions
INSERT OR IGNORE INTO permissions (permission_name, module, action, description) VALUES
('sales.read', 'sales', 'read', 'عرض المبيعات'),
('sales.create', 'sales', 'create', 'إنشاء فواتير مبيعات'),
('sales.update', 'sales', 'update', 'تعديل فواتير المبيعات'),
('sales.delete', 'sales', 'delete', 'حذف فواتير المبيعات'),
('sales.approve', 'sales', 'approve', 'اعتماد المبيعات'),
('sales.refund', 'sales', 'refund', 'استرداد المبيعات');

-- Inventory permissions
INSERT OR IGNORE INTO permissions (permission_name, module, action, description) VALUES
('inventory.read', 'inventory', 'read', 'عرض المخزون'),
('inventory.create', 'inventory', 'create', 'إضافة منتجات'),
('inventory.update', 'inventory', 'update', 'تعديل المنتجات'),
('inventory.delete', 'inventory', 'delete', 'حذف المنتجات'),
('inventory.adjust', 'inventory', 'adjust', 'تسويات المخزون'),
('inventory.count', 'inventory', 'count', 'جرد المخزون');

-- Accounting permissions
INSERT OR IGNORE INTO permissions (permission_name, module, action, description) VALUES
('accounting.read', 'accounting', 'read', 'عرض الحسابات'),
('accounting.create', 'accounting', 'create', 'إنشاء قيود'),
('accounting.update', 'accounting', 'update', 'تعديل القيود'),
('accounting.delete', 'accounting', 'delete', 'حذف القيود'),
('accounting.approve', 'accounting', 'approve', 'اعتماد القيود'),
('accounting.close_period', 'accounting', 'close_period', 'إغلاق الفترات');

-- Purchase permissions
INSERT OR IGNORE INTO permissions (permission_name, module, action, description) VALUES
('purchase.read', 'purchase', 'read', 'عرض المشتريات'),
('purchase.create', 'purchase', 'create', 'إنشاء طلبات شراء'),
('purchase.update', 'purchase', 'update', 'تعديل طلبات الشراء'),
('purchase.delete', 'purchase', 'delete', 'حذف طلبات الشراء'),
('purchase.approve', 'purchase', 'approve', 'اعتماد المشتريات'),
('purchase.receive', 'purchase', 'receive', 'استلام المشتريات');

-- Reports permissions
INSERT OR IGNORE INTO permissions (permission_name, module, action, description) VALUES
('reports.read', 'reports', 'read', 'عرض التقارير'),
('reports.export', 'reports', 'export', 'تصدير التقارير'),
('reports.financial', 'reports', 'financial', 'التقارير المالية');

-- Users permissions
INSERT OR IGNORE INTO permissions (permission_name, module, action, description) VALUES
('users.read', 'users', 'read', 'عرض المستخدمين'),
('users.create', 'users', 'create', 'إنشاء مستخدمين'),
('users.update', 'users', 'update', 'تعديل المستخدمين'),
('users.delete', 'users', 'delete', 'حذف المستخدمين'),
('users.manage_roles', 'users', 'manage_roles', 'إدارة الأدوار');

-- System permissions
INSERT OR IGNORE INTO permissions (permission_name, module, action, description) VALUES
('system.backup', 'system', 'backup', 'النسخ الاحتياطي'),
('system.settings', 'system', 'settings', 'إعدادات النظام'),
('system.audit', 'system', 'audit', 'عرض سجلات التدقيق');

-- ============================================================================
-- ASSIGN PERMISSIONS TO ADMIN ROLE
-- ============================================================================
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r
CROSS JOIN permissions p
WHERE r.role_name = 'admin';

-- ============================================================================
-- ASSIGN PERMISSIONS TO MANAGER ROLE
-- ============================================================================
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r
CROSS JOIN permissions p
WHERE r.role_name = 'manager'
AND p.permission_name IN (
    'sales.read', 'sales.create', 'sales.update', 'sales.approve',
    'inventory.read', 'inventory.create', 'inventory.update', 'inventory.adjust',
    'purchase.read', 'purchase.create', 'purchase.update', 'purchase.approve',
    'reports.read', 'reports.export', 'reports.financial'
);

-- ============================================================================
-- ASSIGN PERMISSIONS TO ACCOUNTANT ROLE
-- ============================================================================
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r
CROSS JOIN permissions p
WHERE r.role_name = 'accountant'
AND p.permission_name LIKE 'accounting.%' OR p.permission_name IN (
    'sales.read', 'purchase.read', 'reports.read', 'reports.financial'
);

-- ============================================================================
-- ASSIGN PERMISSIONS TO SALES_REP ROLE
-- ============================================================================
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r
CROSS JOIN permissions p
WHERE r.role_name = 'sales_rep'
AND p.permission_name IN (
    'sales.read', 'sales.create',
    'inventory.read',
    'reports.read'
);

-- ============================================================================
-- ASSIGN PERMISSIONS TO INVENTORY_CLERK ROLE
-- ============================================================================
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r
CROSS JOIN permissions p
WHERE r.role_name = 'inventory_clerk'
AND p.permission_name LIKE 'inventory.%' OR p.permission_name IN (
    'purchase.read', 'purchase.receive'
);

-- ============================================================================
-- ASSIGN PERMISSIONS TO VIEWER ROLE
-- ============================================================================
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r
CROSS JOIN permissions p
WHERE r.role_name = 'viewer'
AND p.action = 'read';

-- ============================================================================
-- VIEWS
-- ============================================================================

-- User permissions view
CREATE VIEW IF NOT EXISTS v_user_permissions AS
SELECT 
    u.user_id,
    u.username,
    u.full_name,
    r.role_id,
    r.role_name,
    r.display_name AS role_display_name,
    p.permission_id,
    p.permission_name,
    p.module,
    p.action,
    ur.assigned_at,
    ur.expires_at,
    CASE 
        WHEN ur.expires_at IS NULL THEN 1
        WHEN ur.expires_at > CURRENT_TIMESTAMP THEN 1
        ELSE 0
    END AS is_active
FROM users u
INNER JOIN user_roles ur ON u.user_id = ur.user_id
INNER JOIN roles r ON ur.role_id = r.role_id
INNER JOIN role_permissions rp ON r.role_id = rp.role_id
INNER JOIN permissions p ON rp.permission_id = p.permission_id
WHERE u.is_active = 1 AND r.is_active = 1;

-- Audit summary view
CREATE VIEW IF NOT EXISTS v_audit_summary AS
SELECT 
    date(timestamp) AS audit_date,
    user_id,
    username,
    module,
    action,
    COUNT(*) AS action_count,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count
FROM audit_log
GROUP BY date(timestamp), user_id, username, module, action;

-- Active sessions view
CREATE VIEW IF NOT EXISTS v_active_sessions AS
SELECT 
    s.session_id,
    s.user_id,
    u.username,
    u.full_name,
    s.login_time,
    s.last_activity,
    s.ip_address,
    s.user_agent,
    ROUND((JULIANDAY('now') - JULIANDAY(s.last_activity)) * 24 * 60, 2) AS idle_minutes
FROM user_sessions s
INNER JOIN users u ON s.user_id = u.user_id
WHERE s.is_active = 1 AND s.logout_time IS NULL;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update roles timestamp
CREATE TRIGGER IF NOT EXISTS trg_roles_updated
AFTER UPDATE ON roles
BEGIN
    UPDATE roles SET updated_at = CURRENT_TIMESTAMP
    WHERE role_id = NEW.role_id;
END;

-- Log session activity
CREATE TRIGGER IF NOT EXISTS trg_session_activity
AFTER UPDATE ON user_sessions
WHEN NEW.is_active = 1 AND OLD.is_active = 1
BEGIN
    UPDATE user_sessions SET last_activity = CURRENT_TIMESTAMP
    WHERE session_id = NEW.session_id;
END;
