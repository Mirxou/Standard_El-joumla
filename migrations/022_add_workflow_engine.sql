-- =====================================================
-- Migration 022: Advanced Workflow Engine
-- محرك موافقات متقدم
-- =====================================================

PRAGMA foreign_keys = ON;

-- =====================================================
-- 1. جدول Workflows (سير العمل)
-- =====================================================
CREATE TABLE IF NOT EXISTS workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                          -- اسم سير العمل
    description TEXT,                            -- وصف سير العمل
    entity_type TEXT NOT NULL,                   -- نوع الكيان (purchase_order, sale, payment, etc.)
    is_active INTEGER DEFAULT 1,                -- نشط/غير نشط
    is_default INTEGER DEFAULT 0,               -- سير العمل الافتراضي لهذا النوع
    trigger_condition TEXT,                      -- شرط التفعيل (JSON)
    company_id INTEGER,                          -- معرف الشركة (Multi-Company Support)
    created_by INTEGER,                          -- المستخدم الذي أنشأ سير العمل
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- =====================================================
-- 2. جدول Workflow Steps (خطوات سير العمل)
-- =====================================================
CREATE TABLE IF NOT EXISTS workflow_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL,                -- معرف سير العمل
    step_order INTEGER NOT NULL,                -- ترتيب الخطوة (1, 2, 3, ...)
    name TEXT NOT NULL,                         -- اسم الخطوة
    step_type TEXT NOT NULL,                    -- نوع الخطوة (approval, notification, condition, action)
    approver_type TEXT,                         -- نوع الموافق (user, role, department)
    approver_id INTEGER,                         -- معرف الموافق (user_id أو role_id)
    approver_role TEXT,                          -- دور الموافق (manager, director, etc.)
    condition_expression TEXT,                  -- شرط تنفيذ الخطوة (JSON)
    action_type TEXT,                            -- نوع الإجراء (email, sms, webhook, etc.)
    action_config TEXT,                          -- إعدادات الإجراء (JSON)
    timeout_hours INTEGER,                       -- مهلة الانتظار (بالساعات)
    is_required INTEGER DEFAULT 1,              -- هل الخطوة إلزامية؟
    can_delegate INTEGER DEFAULT 0,             -- هل يمكن التفويض؟
    auto_approve INTEGER DEFAULT 0,             -- الموافقة التلقائية عند استيفاء الشرط
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    FOREIGN KEY (approver_id) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE(workflow_id, step_order)
);

-- =====================================================
-- 3. جدول Workflow Instances (مثيلات سير العمل)
-- =====================================================
CREATE TABLE IF NOT EXISTS workflow_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL,                -- معرف سير العمل
    entity_type TEXT NOT NULL,                   -- نوع الكيان
    entity_id INTEGER NOT NULL,                 -- معرف الكيان (purchase_order_id, sale_id, etc.)
    status TEXT NOT NULL DEFAULT 'pending',     -- الحالة (pending, in_progress, approved, rejected, cancelled)
    current_step_id INTEGER,                     -- معرف الخطوة الحالية
    initiated_by INTEGER NOT NULL,              -- المستخدم الذي بدأ سير العمل
    initiated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,                      -- تاريخ الإكمال
    completed_by INTEGER,                        -- المستخدم الذي أكمل سير العمل
    notes TEXT,                                  -- ملاحظات
    metadata TEXT,                               -- بيانات إضافية (JSON)
    company_id INTEGER,                          -- معرف الشركة (Multi-Company Support)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    FOREIGN KEY (current_step_id) REFERENCES workflow_steps(id) ON DELETE SET NULL,
    FOREIGN KEY (initiated_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (completed_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(entity_type, entity_id)
);

-- =====================================================
-- 4. جدول Workflow Approvals (الموافقات)
-- =====================================================
CREATE TABLE IF NOT EXISTS workflow_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id INTEGER NOT NULL,               -- معرف مثيل سير العمل
    step_id INTEGER NOT NULL,                   -- معرف الخطوة
    approver_id INTEGER NOT NULL,               -- معرف الموافق
    status TEXT NOT NULL DEFAULT 'pending',     -- الحالة (pending, approved, rejected, delegated)
    decision TEXT,                               -- القرار (approve, reject, delegate)
    comments TEXT,                               -- تعليقات الموافق
    delegated_to INTEGER,                        -- معرف المستخدم المفوض إليه
    approved_at DATETIME,                        -- تاريخ الموافقة
    rejected_at DATETIME,                        -- تاريخ الرفض
    deadline DATETIME,                           -- الموعد النهائي
    notified_at DATETIME,                        -- تاريخ الإشعار
    reminder_sent INTEGER DEFAULT 0,            -- هل تم إرسال تذكير؟
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES workflow_instances(id) ON DELETE CASCADE,
    FOREIGN KEY (step_id) REFERENCES workflow_steps(id) ON DELETE CASCADE,
    FOREIGN KEY (approver_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (delegated_to) REFERENCES users(id) ON DELETE SET NULL
);

-- =====================================================
-- 5. جدول Workflow History (سجل سير العمل)
-- =====================================================
CREATE TABLE IF NOT EXISTS workflow_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id INTEGER NOT NULL,               -- معرف مثيل سير العمل
    step_id INTEGER,                             -- معرف الخطوة
    action TEXT NOT NULL,                        -- الإجراء (started, approved, rejected, delegated, etc.)
    performed_by INTEGER,                         -- المستخدم الذي قام بالإجراء
    performed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    details TEXT,                                 -- تفاصيل الإجراء (JSON)
    comments TEXT,                                -- تعليقات
    
    FOREIGN KEY (instance_id) REFERENCES workflow_instances(id) ON DELETE CASCADE,
    FOREIGN KEY (step_id) REFERENCES workflow_steps(id) ON DELETE SET NULL,
    FOREIGN KEY (performed_by) REFERENCES users(id) ON DELETE SET NULL
);

-- =====================================================
-- 6. فهارس لتحسين الأداء
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_workflows_entity_type ON workflows(entity_type);
CREATE INDEX IF NOT EXISTS idx_workflows_is_active ON workflows(is_active);
CREATE INDEX IF NOT EXISTS idx_workflows_is_default ON workflows(is_default);
CREATE INDEX IF NOT EXISTS idx_workflows_company ON workflows(company_id);

CREATE INDEX IF NOT EXISTS idx_workflow_steps_workflow ON workflow_steps(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_steps_order ON workflow_steps(workflow_id, step_order);

CREATE INDEX IF NOT EXISTS idx_workflow_instances_workflow ON workflow_instances(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_instances_entity ON workflow_instances(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_workflow_instances_status ON workflow_instances(status);
CREATE INDEX IF NOT EXISTS idx_workflow_instances_company ON workflow_instances(company_id);

CREATE INDEX IF NOT EXISTS idx_workflow_approvals_instance ON workflow_approvals(instance_id);
CREATE INDEX IF NOT EXISTS idx_workflow_approvals_step ON workflow_approvals(step_id);
CREATE INDEX IF NOT EXISTS idx_workflow_approvals_approver ON workflow_approvals(approver_id);
CREATE INDEX IF NOT EXISTS idx_workflow_approvals_status ON workflow_approvals(status);

CREATE INDEX IF NOT EXISTS idx_workflow_history_instance ON workflow_history(instance_id);
CREATE INDEX IF NOT EXISTS idx_workflow_history_performed_at ON workflow_history(performed_at);

-- =====================================================
-- 7. إدراج سير عمل افتراضي (مثال)
-- =====================================================
-- سير عمل موافقة على طلبات الشراء
INSERT OR IGNORE INTO workflows (
    name, description, entity_type, is_active, is_default,
    created_at, updated_at
) VALUES (
    'موافقة طلبات الشراء',
    'سير عمل موافقة على طلبات الشراء',
    'purchase_order',
    1,
    1,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- =====================================================
-- ملاحظات مهمة:
-- =====================================================
-- 1. entity_type: يمكن أن يكون purchase_order, sale, payment, etc.
-- 2. step_type: approval, notification, condition, action
-- 3. approver_type: user, role, department
-- 4. status: pending, in_progress, approved, rejected, cancelled
-- 5. decision: approve, reject, delegate
-- 6. جميع الجداول تدعم Multi-Company عبر company_id
-- 7. يمكن تخصيص سير العمل لكل شركة
-- =====================================================

