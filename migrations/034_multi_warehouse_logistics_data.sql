-- Phase 6: Multi-Warehouse Management & Logistics Integration
-- Data Migration (Production-Safe)
--
-- ملاحظة: تم حذف البيانات التجريبية (مستودعات وهمية، شركات نقل وهمية).
-- المستخدم سيُدخل بيانات المستودعات وشركات النقل الحقيقية من واجهة النظام.
-- لبيانات اختبار، استخدم: scripts/generate_dummy_data.py

PRAGMA foreign_keys = ON;

-- لا توجد بيانات هيكلية مطلوبة لهذه المرحلة.
-- جداول warehouses, carriers, routes تم إنشاؤها في 030_multi_warehouse_logistics.sql
