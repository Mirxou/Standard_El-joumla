# معايير الانتقال إلى PostgreSQL - Migration Criteria

## نظرة عامة

هذا المستند يحدد المعايير التي يجب مراعاتها عند اتخاذ قرار الانتقال من SQLite إلى PostgreSQL.

## معايير الانتقال

### 1. معايير الأداء (Performance)

**الانتقال مطلوب عندما:**

- ✅ **Average query time > 1000ms** (متوسط وقت الاستجابة > ثانية)
- ✅ **Frequent database locks** (قفل قاعدة البيانات متكرر)
- ✅ **Concurrent writes > 5** (كتابات متزامنة مستمرة > 5)
- ✅ **Lock wait time > 500ms** (وقت انتظار القفل > 500ms)

**القياس:**
- استخدام `scripts/test_sqlite_wal_performance.py`
- مراقبة Database Metrics في Desktop App
- مراجعة slow_queries table

### 2. معايير الحجم (Scale)

**الانتقال مطلوب عندما:**

- ✅ **عدد المستخدمين المتزامنين > 10**
- ✅ **حجم قاعدة البيانات > 10GB**
- ✅ **عدد الجداول > 50 جدول**
- ✅ **عدد الصفوف في الجداول الرئيسية > 1M صف**

### 3. معايير الميزات (Features)

**الانتقال مطلوب عندما تحتاج:**

- ✅ **Replication** (Master-Slave, Master-Master)
- ✅ **Advanced backup** (Point-in-time recovery)
- ✅ **Full-text search** (tsvector/tsquery)
- ✅ **Partitioning** (لجداول كبيرة)
- ✅ **Materialized views**
- ✅ **Stored procedures**

### 4. معايير الأمان (Security)

**الانتقال مطلوب عندما تحتاج:**

- ✅ **Row-level security (RLS)**
- ✅ **Advanced authentication** (LDAP, PAM)
- ✅ **Audit logging متقدم**

## عملية التقييم

### الخطوة 1: مراقبة الأداء (شهرياً)

```bash
# تشغيل اختبار الأداء
python scripts/test_sqlite_wal_performance.py

# مراجعة Database Metrics في Desktop App
# Window > Database Metrics
```

### الخطوة 2: تحليل النتائج

**إذا كانت النتائج تقع ضمن المعايير:**
- ✅ الاستمرار مع SQLite
- ✅ مراقبة مستمرة

**إذا تجاوزت المعايير:**
- ⚠️ النظر في PostgreSQL
- ⚠️ تقييم الجهد المطلوب
- ⚠️ اتخاذ قرار

### الخطوة 3: اتخاذ القرار

**قرار الانتقال يتطلب:**
1. تأكيد تجاوز المعايير
2. تقييم التكلفة/الفائدة
3. خطة ترحيل واضحة
4. خطة rollback

## مؤشرات التحذير المبكر

### تحذيرات (تحتاج مراقبة):

- Average query time: 500-1000ms
- Concurrent writes: 3-5
- Database size: 5-10GB

### إنذارات (تفكير جدي في الانتقال):

- Average query time: > 1000ms
- Frequent locks
- Concurrent writes: > 5
- Database size: > 10GB

## خطة المراقبة المستمرة

### يومياً:
- مراجعة Database Metrics dashboard
- فحص slow queries

### أسبوعياً:
- مراجعة إحصائيات الأداء
- تحليل trends

### شهرياً:
- تشغيل performance tests
- تقييم مقابل المعايير

## التوصيات

### للاستخدام الحالي:
- ✅ **SQLite كافٍ** للاستخدام الحالي
- ✅ WAL mode يدعم concurrent access جيداً
- ✅ البساطة أفضل من التعقيد

### للمستقبل:
- 🔄 **مراقبة مستمرة** للأداء
- 🔄 **Abstraction layer** جاهز للترحيل
- 🔄 **الانتقال عند الحاجة** الفعلية

## الخلاصة

**قاعدة القرار:**
- استخدم SQLite حتى تظهر حاجة حقيقية لـ PostgreSQL
- Abstraction layer يسهل الانتقال عند الحاجة
- المراقبة المستمرة تساعد في اتخاذ قرار مبكر

