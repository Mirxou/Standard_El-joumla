# سجل العمل — إغلاق الفجوات #5–#8 + إصلاح 5 أخطاء دمج حرجة

**التاريخ:** 2026-11-08 | **Commit:** `106a91c`

## الفجوات المُغلقة (كلها مُتحقق منها بـ 20 اختبار SQLite حقيقي)

| # | الفجوة | التنفيذ |
|---|--------|---------|
| 5 | تحويل الوحدات | `POST /sales` يمر عبر `SalesService` الآن (كان يتجاوز **كل** قواعد الأعمال!) + `SaleItem.sale_unit` يتحول للوحدة الأساسية قبل الخصم + تسعير الوحدات من `unit_prices` + endpoints إدارة التحويلات والأسعار |
| 6 | الإرجاع الذري | `complete_return()` ذرية: استعادة مخزون + حركة `in/return` + استعادة دفعة + قيد عكسي (مدين 4001 / دائن صندوق أو عملاء حسب طريقة الاسترداد) + مواءمة المخطط مع هجرة 004 الغنية + تحويل Enum آمن |
| 7 | دفعات الموردين FIFO | جدول `payment_allocations` + تخصيص تلقائي للأقدم أولاً + تتبع `purchases.paid_amount`/`payment_status` + `GET /payments/{id}/allocations` |
| 8 | نظام المصاريف | `expense_service.py` كامل: تصنيفات مرتبطة بدليل الحسابات + دورة موافقة مع قيد تلقائي + قوالب متكررة (يومي/أسبوعي/شهري/سنوي) مع catch-up + REST API `/expenses` |

## الأخطاء الحرجة المُكتشفة والمُصلحة (اكتُشفت بالاختبار على DB حقيقي)

1. **خصم مخزون مزدوج** في `SalesService.create_sale` — `SaleManager` يخصم أصلاً (batches FEFO + products + movements) وحلقة FEFO في `SalesService` كانت تخصم **مرة ثانية** → المخزون كان ينقص الضعف في كل بيع POS!
2. **فحص السقف الائتماني لا يعمل أبداً** — `PaymentMethod.CREDIT` (enum) لا يساوي `"آجل"` (نص) في المقارنة → تطبيع enum→value.
3. **CreditLimitError كان يُبتلع** إلى `None` صامتة → يُرفع الآن صراحة + API يعيد HTTP 422 مع تفاصيل السقف.
4. **FK failure** على `sale_items.batch_id=1` الافتراضي مع دفعات فارغة → إنشاء دفعة AUTO داخل المعاملة + احترام `cost_price` المحسوب من CostingService.
5. **منتجات بدون دفعات غير قابلة للبيع** — رسالة "الرصيد غير كافٍ ولا يوجد كرتون" رغم توفر المخزون المباشر → fallback إلى `products.current_stock` قبل فك الكراتين.

## الاختبارات

- `tests/unit/services/test_business_gaps.py` — **20 PASSED** (0.73s)
- انحدارات: **صفر** (أخطاء `test_payment_service`/`test_sales_service` القديمة موجودة قبل التغييرات — تحقق بـ git stash)

## الرفع على GitHub

الـ commit جاهز محلياً. التوكن نُظف من البيئة سابقاً (أمان). للرفع:

```bash
cd erp-project
git push https://x-access-token:<YOUR_PAT>@github.com/Mirxou/Standard_El-joumla.git main
```

أو استخدم `scripts/push.sh <TOKEN>` المرفق.
