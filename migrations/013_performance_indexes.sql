-- تحسين الأداء - إضافة فهارس محسّنة
-- Performance Optimization - Enhanced Indexes

-- ==================== فهارس المبيعات ====================

-- فهرس لتسريع البحث حسب التاريخ
CREATE INDEX IF NOT EXISTS idx_sales_date 
ON sales(sale_date DESC);

-- فهرس مركب للبحث حسب العميل والتاريخ
CREATE INDEX IF NOT EXISTS idx_sales_customer_date 
ON sales(customer_id, sale_date DESC);

-- فهرس لطريقة الدفع (للتقارير)
CREATE INDEX IF NOT EXISTS idx_sales_payment_method 
ON sales(payment_method);

-- فهرس للحالة (pending, completed, etc.)
CREATE INDEX IF NOT EXISTS idx_sales_status 
ON sales(status) WHERE status IS NOT NULL;

-- ==================== فهارس عناصر المبيعات ====================

-- فهرس للمنتج (لتقارير المنتجات الأكثر مبيعاً)
CREATE INDEX IF NOT EXISTS idx_sale_items_product 
ON sale_items(product_id);

-- فهرس مركب للفاتورة والمنتج
CREATE INDEX IF NOT EXISTS idx_sale_items_sale_product 
ON sale_items(sale_id, product_id);

-- ==================== فهارس المنتجات ====================

-- فهرس لـ SKU (للبحث السريع)
CREATE INDEX IF NOT EXISTS idx_products_sku 
ON products(sku) WHERE sku IS NOT NULL;

-- فهرس للباركود
CREATE INDEX IF NOT EXISTS idx_products_barcode 
ON products(barcode) WHERE barcode IS NOT NULL;

-- فهرس للفئة (للتقارير حسب الفئة)
CREATE INDEX IF NOT EXISTS idx_products_category 
ON products(category_id);

-- فهرس للمخزون المنخفض
CREATE INDEX IF NOT EXISTS idx_products_low_stock 
ON products(current_stock) WHERE current_stock <= min_stock;

-- فهرس للبحث النصي في الاسم
CREATE INDEX IF NOT EXISTS idx_products_name 
ON products(name COLLATE NOCASE);

-- ==================== فهارس العملاء ====================

-- فهرس للبحث بالاسم
CREATE INDEX IF NOT EXISTS idx_customers_name 
ON customers(name COLLATE NOCASE);

-- فهرس للهاتف
CREATE INDEX IF NOT EXISTS idx_customers_phone 
ON customers(phone) WHERE phone IS NOT NULL;

-- فهرس للبريد الإلكتروني
CREATE INDEX IF NOT EXISTS idx_customers_email 
ON customers(email) WHERE email IS NOT NULL;

-- فهرس للرصيد الحالي (للعملاء ذوي الأرصدة)
CREATE INDEX IF NOT EXISTS idx_customers_balance 
ON customers(current_balance) WHERE current_balance > 0;

-- ==================== فهارس الموردين ====================

-- فهرس للبحث بالاسم
CREATE INDEX IF NOT EXISTS idx_suppliers_name 
ON suppliers(name COLLATE NOCASE);

-- فهرس للهاتف
CREATE INDEX IF NOT EXISTS idx_suppliers_phone 
ON suppliers(phone) WHERE phone IS NOT NULL;

-- ==================== فهارس المشتريات ====================

-- فهرس للتاريخ
CREATE INDEX IF NOT EXISTS idx_purchases_date 
ON purchases(purchase_date DESC);

-- فهرس مركب للمورد والتاريخ
CREATE INDEX IF NOT EXISTS idx_purchases_supplier_date 
ON purchases(supplier_id, purchase_date DESC);

-- فهرس للحالة
CREATE INDEX IF NOT EXISTS idx_purchases_status 
ON purchases(status) WHERE status IS NOT NULL;

-- ==================== فهارس الدفعات ====================

-- فهرس لتاريخ الدفع
CREATE INDEX IF NOT EXISTS idx_payments_date 
ON payments(payment_date DESC);

-- فهرس لنوع الدفع (received/paid)
CREATE INDEX IF NOT EXISTS idx_payments_type 
ON payments(payment_type);

-- فهرس مركب للعميل/المورد والتاريخ
CREATE INDEX IF NOT EXISTS idx_payments_reference_date 
ON payments(reference_type, reference_id, payment_date DESC);

-- ==================== فهارس خطط الدفع ====================

-- فهرس للفاتورة
CREATE INDEX IF NOT EXISTS idx_payment_plans_invoice 
ON payment_plans(invoice_id);

-- فهرس للحالة
CREATE INDEX IF NOT EXISTS idx_payment_plans_status 
ON payment_plans(status);

-- فهرس للأقساط المستحقة
CREATE INDEX IF NOT EXISTS idx_installments_due_date 
ON installments(due_date) WHERE status = 'pending';

-- فهرس مركب لخطة الدفع والحالة
CREATE INDEX IF NOT EXISTS idx_installments_plan_status 
ON installments(plan_id, status);

-- ==================== فهارس المحاسبة ====================

-- فهرس لنوع الحساب
CREATE INDEX IF NOT EXISTS idx_accounts_type 
ON chart_of_accounts(account_type);

-- فهرس للحساب الرئيسي
CREATE INDEX IF NOT EXISTS idx_accounts_parent 
ON chart_of_accounts(parent_account_id) WHERE parent_account_id IS NOT NULL;

-- فهرس لتاريخ القيد
CREATE INDEX IF NOT EXISTS idx_journal_date 
ON general_journal(journal_date DESC);

-- فهرس للفترة المحاسبية
CREATE INDEX IF NOT EXISTS idx_journal_period 
ON general_journal(period_id);

-- فهرس للحساب في سطور القيد
CREATE INDEX IF NOT EXISTS idx_journal_lines_account 
ON journal_lines(account_id);

-- ==================== فهارس الجرد الدوري ====================

-- فهرس للخطة
CREATE INDEX IF NOT EXISTS idx_cycle_sessions_plan 
ON cycle_count_sessions(plan_id);

-- فهرس للحالة
CREATE INDEX IF NOT EXISTS idx_cycle_sessions_status 
ON cycle_count_sessions(status);

-- فهرس لتاريخ البدء
CREATE INDEX IF NOT EXISTS idx_cycle_sessions_start 
ON cycle_count_sessions(started_at DESC);

-- فهرس للجلسة والمنتج
CREATE INDEX IF NOT EXISTS idx_cycle_items_session_product 
ON cycle_count_items(session_id, product_id);

-- ==================== فهارس عروض الأسعار ====================

-- فهرس للعميل
CREATE INDEX IF NOT EXISTS idx_quotes_customer 
ON quotes(customer_id);

-- فهرس لتاريخ الانتهاء
CREATE INDEX IF NOT EXISTS idx_quotes_valid_until 
ON quotes(valid_until);

-- فهرس للحالة
CREATE INDEX IF NOT EXISTS idx_quotes_status 
ON quotes(status);

-- ==================== فهارس المرتجعات ====================

-- فهرس للفاتورة الأصلية
CREATE INDEX IF NOT EXISTS idx_returns_original_sale 
ON return_invoices(original_sale_id);

-- فهرس للتاريخ
CREATE INDEX IF NOT EXISTS idx_returns_date 
ON return_invoices(return_date DESC);

-- فهرس للحالة
CREATE INDEX IF NOT EXISTS idx_returns_status 
ON return_invoices(status);

-- ==================== فهارس تقييم الموردين ====================

-- فهرس للمورد
CREATE INDEX IF NOT EXISTS idx_vendor_ratings_supplier 
ON vendor_ratings(supplier_id);

-- فهرس للتاريخ
CREATE INDEX IF NOT EXISTS idx_vendor_ratings_date 
ON vendor_ratings(rating_date DESC);

-- ==================== فهارس الفلاتر المحفوظة ====================

-- فهرس للمستخدم ونوع الفلتر
CREATE INDEX IF NOT EXISTS idx_saved_filters_user_type 
ON saved_filters(user_id, filter_type);

-- فهرس للمفضلة
CREATE INDEX IF NOT EXISTS idx_saved_filters_favorite 
ON saved_filters(is_favorite) WHERE is_favorite = 1;

-- ==================== إحصائيات التحسين ====================

-- تحليل الجداول لتحسين الفهارس
ANALYZE;

-- إعادة بناء الفهارس لتحسين الأداء
VACUUM;

-- نهاية الملف
