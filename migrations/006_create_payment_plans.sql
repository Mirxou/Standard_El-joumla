-- ============================================================================
-- Migration 006: Create Payment Plans and Installments System
-- نظام خطط الدفع الجزئي والتقسيط
-- ============================================================================

-- ============================================================================
-- 1. جدول خطط الدفع (Payment Plans)
-- ============================================================================
CREATE TABLE IF NOT EXISTS payment_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_number TEXT NOT NULL UNIQUE,
    
    -- العلاقات
    invoice_id INTEGER,
    invoice_number TEXT,
    customer_id INTEGER NOT NULL,
    customer_name TEXT,
    
    -- معلومات الخطة
    plan_name TEXT,
    description TEXT,
    
    -- التواريخ
    start_date DATE NOT NULL,
    end_date DATE,
    
    -- المبالغ
    total_amount DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    down_payment DECIMAL(15, 2) DEFAULT 0.00,       -- الدفعة المقدمة
    financed_amount DECIMAL(15, 2) DEFAULT 0.00,    -- المبلغ المقسط
    
    -- شروط التقسيط
    number_of_installments INTEGER NOT NULL DEFAULT 1,
    installment_amount DECIMAL(15, 2) DEFAULT 0.00,
    frequency TEXT DEFAULT 'MONTHLY',  -- DAILY, WEEKLY, BIWEEKLY, MONTHLY, etc.
    
    -- الفائدة
    interest_rate DECIMAL(5, 2) DEFAULT 0.00,     -- نسبة الفائدة السنوية
    total_interest DECIMAL(15, 2) DEFAULT 0.00,   -- إجمالي الفائدة
    
    -- غرامات التأخير
    late_fee_type TEXT DEFAULT 'NONE',  -- NONE, FIXED, PERCENTAGE, COMPOUNDING
    late_fee_value DECIMAL(10, 2) DEFAULT 0.00,
    grace_period_days INTEGER DEFAULT 0,
    
    -- الحالة
    status TEXT NOT NULL DEFAULT 'DRAFT',  -- DRAFT, ACTIVE, COMPLETED, CANCELLED, DEFAULTED
    
    -- الملخص المالي
    total_paid DECIMAL(15, 2) DEFAULT 0.00,
    total_remaining DECIMAL(15, 2) DEFAULT 0.00,
    total_late_fees DECIMAL(15, 2) DEFAULT 0.00,
    
    -- الملاحظات
    notes TEXT,
    terms_conditions TEXT,
    
    -- التتبع
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- العلاقات
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (invoice_id) REFERENCES sales(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- الفهارس لجدول خطط الدفع
CREATE INDEX IF NOT EXISTS idx_pp_plan_number ON payment_plans(plan_number);
CREATE INDEX IF NOT EXISTS idx_pp_customer ON payment_plans(customer_id);
CREATE INDEX IF NOT EXISTS idx_pp_invoice ON payment_plans(invoice_id);
CREATE INDEX IF NOT EXISTS idx_pp_status ON payment_plans(status);
CREATE INDEX IF NOT EXISTS idx_pp_start_date ON payment_plans(start_date);
CREATE INDEX IF NOT EXISTS idx_pp_end_date ON payment_plans(end_date);

-- ============================================================================
-- 2. جدول الأقساط (Payment Installments)
-- ============================================================================
CREATE TABLE IF NOT EXISTS payment_installments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_plan_id INTEGER NOT NULL,
    
    -- معلومات القسط
    installment_number INTEGER NOT NULL,
    due_date DATE NOT NULL,
    
    -- المبالغ
    principal_amount DECIMAL(15, 2) NOT NULL DEFAULT 0.00,  -- المبلغ الأصلي
    interest_amount DECIMAL(15, 2) DEFAULT 0.00,            -- الفائدة
    late_fee DECIMAL(15, 2) DEFAULT 0.00,                   -- غرامة التأخير
    total_amount DECIMAL(15, 2) NOT NULL DEFAULT 0.00,      -- الإجمالي
    
    amount_paid DECIMAL(15, 2) DEFAULT 0.00,                -- المدفوع
    remaining_amount DECIMAL(15, 2) DEFAULT 0.00,           -- المتبقي
    
    -- الحالة
    status TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING, PAID, PARTIALLY_PAID, OVERDUE, CANCELLED, WAIVED
    
    -- الدفع
    payment_date DATE,
    payment_method TEXT,
    payment_reference TEXT,
    
    -- الملاحظات
    notes TEXT,
    
    -- التتبع
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- العلاقات
    FOREIGN KEY (payment_plan_id) REFERENCES payment_plans(id) ON DELETE CASCADE
);

-- الفهارس لجدول الأقساط
CREATE INDEX IF NOT EXISTS idx_pi_plan ON payment_installments(payment_plan_id);
CREATE INDEX IF NOT EXISTS idx_pi_due_date ON payment_installments(due_date);
CREATE INDEX IF NOT EXISTS idx_pi_status ON payment_installments(status);
CREATE INDEX IF NOT EXISTS idx_pi_payment_date ON payment_installments(payment_date);

-- ============================================================================
-- 3. جدول سجل الدفعات (Payment History)
-- ============================================================================
CREATE TABLE IF NOT EXISTS payment_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- العلاقات
    payment_plan_id INTEGER NOT NULL,
    installment_id INTEGER,
    
    -- معلومات الدفعة
    payment_date DATE NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    payment_method TEXT,
    payment_reference TEXT,
    
    -- التفاصيل
    notes TEXT,
    receipt_number TEXT,
    
    -- التتبع
    processed_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- العلاقات
    FOREIGN KEY (payment_plan_id) REFERENCES payment_plans(id),
    FOREIGN KEY (installment_id) REFERENCES payment_installments(id),
    FOREIGN KEY (processed_by) REFERENCES users(id)
);

-- الفهارس لجدول سجل الدفعات
CREATE INDEX IF NOT EXISTS idx_ph_plan ON payment_history(payment_plan_id);
CREATE INDEX IF NOT EXISTS idx_ph_installment ON payment_history(installment_id);
CREATE INDEX IF NOT EXISTS idx_ph_date ON payment_history(payment_date);

-- ============================================================================
-- 4. Views للتقارير
-- ============================================================================

-- عرض ملخص خطط الدفع
CREATE VIEW IF NOT EXISTS v_payment_plans_summary AS
SELECT 
    pp.id,
    pp.plan_number,
    pp.customer_name,
    pp.start_date,
    pp.end_date,
    pp.status,
    pp.total_amount,
    pp.down_payment,
    pp.financed_amount,
    pp.number_of_installments,
    pp.total_paid,
    pp.total_remaining,
    pp.total_late_fees,
    COUNT(pi.id) as total_installments,
    SUM(CASE WHEN pi.status = 'PAID' THEN 1 ELSE 0 END) as paid_installments,
    SUM(CASE WHEN pi.status = 'PENDING' AND pi.due_date < date('now') THEN 1 ELSE 0 END) as overdue_installments,
    CASE 
        WHEN pp.financed_amount > 0 
        THEN (pp.total_paid / pp.financed_amount) * 100
        ELSE 0 
    END as completion_percentage
FROM payment_plans pp
LEFT JOIN payment_installments pi ON pp.id = pi.payment_plan_id
GROUP BY pp.id;

-- عرض الأقساط المستحقة قريباً
CREATE VIEW IF NOT EXISTS v_upcoming_installments AS
SELECT 
    pi.id,
    pi.installment_number,
    pi.due_date,
    pi.total_amount,
    pi.remaining_amount,
    pi.status,
    pp.plan_number,
    pp.customer_name,
    julianday(pi.due_date) - julianday('now') as days_until_due
FROM payment_installments pi
JOIN payment_plans pp ON pi.payment_plan_id = pp.id
WHERE pi.status IN ('PENDING', 'PARTIALLY_PAID')
AND pi.due_date >= date('now')
AND pi.due_date <= date('now', '+30 days')
ORDER BY pi.due_date;

-- عرض الأقساط المتأخرة
CREATE VIEW IF NOT EXISTS v_overdue_installments AS
SELECT 
    pi.id,
    pi.installment_number,
    pi.due_date,
    pi.total_amount,
    pi.remaining_amount,
    pi.late_fee,
    pi.status,
    pp.plan_number,
    pp.customer_id,
    pp.customer_name,
    julianday('now') - julianday(pi.due_date) as days_overdue
FROM payment_installments pi
JOIN payment_plans pp ON pi.payment_plan_id = pp.id
WHERE pi.status IN ('PENDING', 'PARTIALLY_PAID')
AND pi.due_date < date('now')
ORDER BY days_overdue DESC;

-- عرض ملخص العملاء
CREATE VIEW IF NOT EXISTS v_customer_payment_summary AS
SELECT 
    pp.customer_id,
    pp.customer_name,
    COUNT(DISTINCT pp.id) as total_plans,
    SUM(pp.total_amount) as total_financed,
    SUM(pp.total_paid) as total_paid,
    SUM(pp.total_remaining) as total_remaining,
    SUM(pp.total_late_fees) as total_late_fees,
    COUNT(CASE WHEN pp.status = 'ACTIVE' THEN 1 END) as active_plans,
    COUNT(CASE WHEN pp.status = 'DEFAULTED' THEN 1 END) as defaulted_plans
FROM payment_plans pp
GROUP BY pp.customer_id;

-- ============================================================================
-- 5. Triggers للتحديث التلقائي
-- ============================================================================

-- تحديث updated_at عند التحديث
CREATE TRIGGER IF NOT EXISTS update_pp_timestamp 
AFTER UPDATE ON payment_plans
FOR EACH ROW
BEGIN
    UPDATE payment_plans SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_pi_timestamp 
AFTER UPDATE ON payment_installments
FOR EACH ROW
BEGIN
    UPDATE payment_installments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- تحديث حالة القسط عند التأخير (يتم تشغيله عند القراءة)
-- ملاحظة: SQLite لا يدعم triggers مجدولة، يجب تشغيل هذا من التطبيق

-- ============================================================================
-- 6. البيانات الأولية (Optional)
-- ============================================================================

-- يمكن إضافة قوالب خطط دفع افتراضية هنا إذا لزم الأمر

-- ============================================================================
-- النهاية
-- ============================================================================
