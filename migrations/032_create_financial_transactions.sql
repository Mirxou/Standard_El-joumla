-- إنشاء جدول المعاملات المالية للتنبؤات المالية
-- Create financial transactions table for financial forecasting

CREATE TABLE IF NOT EXISTS financial_transactions (
    transaction_id TEXT PRIMARY KEY,
    transaction_date DATETIME NOT NULL,
    transaction_type TEXT NOT NULL, -- 'income', 'expense'
    amount DECIMAL(15,2) NOT NULL,
    category TEXT, -- 'sales', 'cost_of_goods', 'operating_expenses', 'other'
    description TEXT,
    reference_type TEXT, -- 'sale', 'purchase', 'manual_entry', 'adjustment'
    reference_id TEXT,
    account_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- إنشاء فهارس للأداء
CREATE INDEX IF NOT EXISTS idx_financial_date ON financial_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_financial_type ON financial_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_financial_category ON financial_transactions(category);

-- إدراج بيانات تجريبية للمعاملات المالية
INSERT OR IGNORE INTO financial_transactions
(transaction_id, transaction_date, transaction_type, amount, category, description, reference_type)
VALUES
('FIN_001', '2024-01-15', 'income', 15000.00, 'sales', 'مبيعات شهر يناير', 'sale'),
('FIN_002', '2024-01-20', 'expense', 8000.00, 'cost_of_goods', 'تكلفة البضاعة المباعة', 'purchase'),
('FIN_003', '2024-01-31', 'expense', 2000.00, 'operating_expenses', 'مصاريف تشغيلية', 'manual_entry'),
('FIN_004', '2024-02-15', 'income', 18000.00, 'sales', 'مبيعات شهر فبراير', 'sale'),
('FIN_005', '2024-02-20', 'expense', 9500.00, 'cost_of_goods', 'تكلفة البضاعة المباعة', 'purchase'),
('FIN_006', '2024-02-28', 'expense', 2200.00, 'operating_expenses', 'مصاريف تشغيلية', 'manual_entry'),
('FIN_007', '2024-03-15', 'income', 22000.00, 'sales', 'مبيعات شهر مارس', 'sale'),
('FIN_008', '2024-03-20', 'expense', 11000.00, 'cost_of_goods', 'تكلفة البضاعة المباعة', 'purchase'),
('FIN_009', '2024-03-31', 'expense', 2500.00, 'operating_expenses', 'مصاريف تشغيلية', 'manual_entry'),
('FIN_010', '2024-04-15', 'income', 25000.00, 'sales', 'مبيعات شهر أبريل', 'sale'),
('FIN_011', '2024-04-20', 'expense', 12500.00, 'cost_of_goods', 'تكلفة البضاعة المباعة', 'purchase'),
('FIN_012', '2024-04-30', 'expense', 2800.00, 'operating_expenses', 'مصاريف تشغيلية', 'manual_entry'),
('FIN_013', '2024-05-15', 'income', 28000.00, 'sales', 'مبيعات شهر مايو', 'sale'),
('FIN_014', '2024-05-20', 'expense', 14000.00, 'cost_of_goods', 'تكلفة البضاعة المباعة', 'purchase'),
('FIN_015', '2024-05-31', 'expense', 3000.00, 'operating_expenses', 'مصاريف تشغيلية', 'manual_entry'),
('FIN_016', '2024-06-15', 'income', 32000.00, 'sales', 'مبيعات شهر يونيو', 'sale'),
('FIN_017', '2024-06-20', 'expense', 16000.00, 'cost_of_goods', 'تكلفة البضاعة المباعة', 'purchase'),
('FIN_018', '2024-06-30', 'expense', 3200.00, 'operating_expenses', 'مصاريف تشغيلية', 'manual_entry'),
('FIN_019', '2024-07-15', 'income', 35000.00, 'sales', 'مبيعات شهر يوليو', 'sale'),
('FIN_020', '2024-07-20', 'expense', 17500.00, 'cost_of_goods', 'تكلفة البضاعة المباعة', 'purchase'),
('FIN_021', '2024-07-31', 'expense', 3500.00, 'operating_expenses', 'مصاريف تشغيلية', 'manual_entry'),
('FIN_022', '2024-08-15', 'income', 38000.00, 'sales', 'مبيعات شهر أغسطس', 'sale'),
('FIN_023', '2024-08-20', 'expense', 19000.00, 'cost_of_goods', 'تكلفة البضاعة المباعة', 'purchase'),
('FIN_024', '2024-08-31', 'expense', 3800.00, 'operating_expenses', 'مصاريف تشغيلية', 'manual_entry'),
('FIN_025', '2024-09-15', 'income', 42000.00, 'sales', 'مبيعات شهر سبتمبر', 'sale'),
('FIN_026', '2024-09-20', 'expense', 21000.00, 'cost_of_goods', 'تكلفة البضاعة المباعة', 'purchase'),
('FIN_027', '2024-09-30', 'expense', 4200.00, 'operating_expenses', 'مصاريف تشغيلية', 'manual_entry'),
('FIN_028', '2024-10-15', 'income', 45000.00, 'sales', 'مبيعات شهر أكتوبر', 'sale'),
('FIN_029', '2024-10-20', 'expense', 22500.00, 'cost_of_goods', 'تكلفة البضاعة المباعة', 'purchase'),
('FIN_030', '2024-10-31', 'expense', 4500.00, 'operating_expenses', 'مصاريف تشغيلية', 'manual_entry'),
('FIN_031', '2024-11-15', 'income', 48000.00, 'sales', 'مبيعات شهر نوفمبر', 'sale'),
('FIN_032', '2024-11-20', 'expense', 24000.00, 'cost_of_goods', 'تكلفة البضاعة المباعة', 'purchase'),
('FIN_033', '2024-11-30', 'expense', 4800.00, 'operating_expenses', 'مصاريف تشغيلية', 'manual_entry'),
('FIN_034', '2024-12-15', 'income', 52000.00, 'sales', 'مبيعات شهر ديسمبر', 'sale'),
('FIN_035', '2024-12-20', 'expense', 26000.00, 'cost_of_goods', 'تكلفة البضاعة المباعة', 'purchase'),
('FIN_036', '2024-12-31', 'expense', 5200.00, 'operating_expenses', 'مصاريف تشغيلية', 'manual_entry');