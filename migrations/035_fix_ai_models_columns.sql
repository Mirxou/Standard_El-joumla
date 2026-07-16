-- Migration 035: Fix ai_models columns
-- إضافة الأعمدة المفقودة لجدول نماذج الذكاء الاصطناعي لضمان التوافق مع AIModel dataclass

-- 1. إضافة الأعمدة المفقودة
ALTER TABLE ai_models ADD COLUMN algorithm TEXT;
ALTER TABLE ai_models ADD COLUMN feature_importance TEXT; -- JSON
ALTER TABLE ai_models ADD COLUMN confusion_matrix TEXT; -- JSON
ALTER TABLE ai_models ADD COLUMN cross_validation_scores TEXT; -- JSON
ALTER TABLE ai_models ADD COLUMN hyperparameters TEXT; -- JSON
ALTER TABLE ai_models ADD COLUMN feature_names TEXT; -- JSON
