-- إصلاحات المرحلة 7: إضافة أعمدة مفقودة وبيانات تجريبية
-- Phase 7 Fixes: Add missing columns and sample data

-- إضافة عمود algorithm إلى جدول ai_models
ALTER TABLE ai_models ADD COLUMN algorithm TEXT;

-- إضافة عمود source إلى جدول training_data
ALTER TABLE training_data ADD COLUMN source TEXT DEFAULT 'sample_data';

-- إدراج بيانات مبيعات تجريبية للتنبؤ (إذا كان الجدول موجوداً)
INSERT OR IGNORE INTO sales (customer_id, total_amount, created_at, status)
SELECT
    'CUST_' || printf('%04d', ABS(RANDOM()) % 500) as customer_id,
    ROUND(ABS(RANDOM()) % 1000 + 100, 2) as total_amount,
    DATE('now', '-' || (ABS(RANDOM()) % 365) || ' days') as created_at,
    'completed' as status
FROM (SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5) t1
CROSS JOIN (SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5) t2
LIMIT 100;

-- إدراج بيانات عملاء تجريبية (إذا كان الجدول موجوداً)
INSERT OR IGNORE INTO customers (name, email, phone, created_at)
SELECT
    'Customer ' || printf('%04d', ROW_NUMBER() OVER (ORDER BY (SELECT NULL))) as name,
    'customer' || printf('%04d', ROW_NUMBER() OVER (ORDER BY (SELECT NULL))) || '@example.com' as email,
    '+9665' || printf('%08d', ABS(RANDOM()) % 100000000) as phone,
    DATE('now', '-' || (ABS(RANDOM()) % 365) || ' days') as created_at
FROM (SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5) t1
LIMIT 50;

-- إدراج بيانات تدريب تجريبية للذكاء الاصطناعي
INSERT OR IGNORE INTO training_data (data_id, data_type, data_content, labels, quality_score, source)
VALUES
('TRAIN_001', 'customer_classification', '[10, 150.0, 1500.0, 5]', '1', 0.9, 'sample_data'),
('TRAIN_002', 'customer_classification', '[25, 300.0, 7500.0, 15]', '1', 0.95, 'sample_data'),
('TRAIN_003', 'customer_classification', '[3, 80.0, 240.0, 120]', '0', 0.8, 'sample_data'),
('TRAIN_004', 'customer_classification', '[1, 50.0, 50.0, 200]', '0', 0.7, 'sample_data'),
('TRAIN_005', 'customer_classification', '[50, 500.0, 25000.0, 2]', '1', 0.98, 'sample_data');