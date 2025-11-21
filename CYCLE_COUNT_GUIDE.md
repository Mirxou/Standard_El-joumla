# دليل نظام الجرد الدوري (Cycle Count)

هذا الدليل يشرح كيفية استخدام نظام الجرد الدوري الذي تمت إضافته في الإصدار v4.2.0.

## نظرة عامة

- إدارة خطط الجرد حسب التكرار والاستراتيجية (Full/Partial/ABC/Random)
- بدء جلسات جرد للمواقع والمستودعات
- تسجيل الفروقات لكل صنف مع أسباب الاختلاف
- تقارير الدقة وقيمة الفروقات والتحليلات

## قاعدة البيانات (Migration 012)

الجداول:
- `cycle_count_plans`
- `cycle_count_sessions`
- `cycle_count_items`
- `variance_reasons`

المشاهدات:
- `v_cycle_count_summary`
- `v_cycle_count_abc_analysis`

## الخدمة

استخدم `src/services/cycle_count_service.py`.

مثال سريع:

```python
from src.services.cycle_count_service import CycleCountService

svc = CycleCountService(db_path="app.db")
plan_id = svc.create_plan("جرد ABC الربع سنوي", frequency="quarterly", strategy="abc")
session_id = svc.start_session(plan_id, counted_by="المخزون")
svc.add_item_count(session_id, product_id=101, location_id=None, expected_qty=10, counted_qty=9, unit_cost=1500.0)
svc.close_session(session_id)
summary = svc.get_session_summary(session_id)
print(summary)
```

## الواجهة (UI)

نافذة أولية باسم `CycleCountWindow` تم توفيرها في:
`src/ui/windows/cycle_count_window.py`

> ملاحظة: النافذة حالياً هي هيكل أساسي قابل للتوصيل بالخدمة لاحقاً.

## التقارير ولوحة التحكم

- استخدم الدالة `get_dashboard_summary` للحصول على ملخص سريع للوحة التحكم.
- يمكن ربط هذه المؤشرات بواجهة العرض الرئيسية لاحقاً.

## أفضل الممارسات

- ابدأ بجلسات صغيرة متكررة بدلاً من جرد شامل نادر.
- راجع أسباب التباين وحدّث قائمة `variance_reasons` بشكل دوري.
- راقب مؤشر الدقة وقيمة التباين أسبوعياً.

## الأسئلة الشائعة

- هل يؤثر الجرد الدوري على رصيد المخزون؟
  - لا بشكل مباشر. التعديلات تتم من خلال عمليات تسوية منفصلة حسب السياسات.

- هل يمكن تخصيص الاستراتيجيات؟
  - نعم، عبر الحقل `strategy` في الخطط مع منطق مخصص في الخدمة.
