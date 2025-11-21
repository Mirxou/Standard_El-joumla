-- ====================================
-- Migration: 010 - Advanced Search System
-- Created: 2025-11-17
-- Description: Tables for saved filters and search history
-- ====================================

-- ====================================
-- جدول الفلاتر المحفوظة (Saved Filters)
-- ====================================
CREATE TABLE IF NOT EXISTS saved_filters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    entity TEXT NOT NULL,  -- SearchEntity enum name
    query_data TEXT NOT NULL,  -- JSON serialized SearchQuery
    
    -- Sharing and defaults
    is_default BOOLEAN DEFAULT 0,
    is_shared BOOLEAN DEFAULT 0,
    
    -- Audit
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_saved_filters_entity ON saved_filters(entity);
CREATE INDEX IF NOT EXISTS idx_saved_filters_user ON saved_filters(created_by);
CREATE INDEX IF NOT EXISTS idx_saved_filters_default ON saved_filters(is_default);

-- ====================================
-- جدول تاريخ البحث (Search History)
-- ====================================
CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    entity TEXT NOT NULL,
    keyword TEXT,
    query_data TEXT,  -- JSON serialized SearchQuery
    results_count INTEGER DEFAULT 0,
    execution_time_ms REAL DEFAULT 0.0,
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_search_history_user ON search_history(user_id);
CREATE INDEX IF NOT EXISTS idx_search_history_entity ON search_history(entity);
CREATE INDEX IF NOT EXISTS idx_search_history_date ON search_history(searched_at);

-- ====================================
-- Insert default filters
-- ====================================

-- Products: Low Stock
INSERT OR IGNORE INTO saved_filters (name, description, entity, query_data, is_default, is_shared)
VALUES (
    'منتجات منخفضة المخزون',
    'المنتجات التي وصلت إلى الحد الأدنى للمخزون',
    'PRODUCTS',
    '{"entity":"PRODUCTS","keyword":"","filters":[{"field":"current_stock","operator":"LESS_OR_EQUAL","value":10}],"sort_by":[{"field":"current_stock","direction":"ASC"}],"limit":100,"offset":0}',
    1,
    1
);

-- Customers: Active with Balance
INSERT OR IGNORE INTO saved_filters (name, description, entity, query_data, is_default, is_shared)
VALUES (
    'عملاء بأرصدة مستحقة',
    'العملاء النشطون الذين لديهم أرصدة مستحقة',
    'CUSTOMERS',
    '{"entity":"CUSTOMERS","keyword":"","filters":[{"field":"current_balance","operator":"GREATER_THAN","value":0},{"field":"is_active","operator":"EQUALS","value":1}],"sort_by":[{"field":"current_balance","direction":"DESC"}],"limit":100,"offset":0}',
    1,
    1
);

-- Sales: This Month
INSERT OR IGNORE INTO saved_filters (name, description, entity, query_data, is_default, is_shared)
VALUES (
    'مبيعات الشهر الحالي',
    'جميع فواتير المبيعات للشهر الحالي',
    'SALES',
    '{"entity":"SALES","keyword":"","filters":[],"sort_by":[{"field":"sale_date","direction":"DESC"}],"limit":100,"offset":0}',
    1,
    1
);

-- Quotes: Pending
INSERT OR IGNORE INTO saved_filters (name, description, entity, query_data, is_default, is_shared)
VALUES (
    'عروض أسعار معلقة',
    'عروض الأسعار المرسلة وبانتظار الرد',
    'QUOTES',
    '{"entity":"QUOTES","keyword":"","filters":[{"field":"status","operator":"EQUALS","value":"SENT"}],"sort_by":[{"field":"quote_date","direction":"DESC"}],"limit":100,"offset":0}',
    1,
    1
);
