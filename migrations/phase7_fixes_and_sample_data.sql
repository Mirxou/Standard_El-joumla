-- إصلاحات المرحلة 7: إضافة أعمدة مفقودة
-- Phase 7 Schema Fixes: Add missing columns only (sample data removed for production safety)

PRAGMA foreign_keys = ON;

-- إضافة عمود algorithm إلى جدول ai_models (إذا لم يكن موجوداً)
ALTER TABLE ai_models ADD COLUMN algorithm TEXT;

-- إضافة عمود source إلى جدول training_data (إذا لم يكن موجوداً)
ALTER TABLE training_data ADD COLUMN source TEXT DEFAULT 'system';