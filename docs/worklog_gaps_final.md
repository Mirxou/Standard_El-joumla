# سجل العمل — إغلاق الفجوات المتبقية (GAP-1.3, 2.2, 3.2, 5.1, 5.2)

**التاريخ:** 2026-11-08 | **الأساس:** SRS_ARCHITECTURE.md — بعد إغلاق GAP-1.1/1.2/2.1/2.3/3.1/4.1/4.2 سابقاً

## الفجوات المُغلقة في هذه الجلسة (141/141 اختبار ناجح على SQLite حقيقي)

| GAP | الميزة | الأولوية | التنفيذ | الاختبارات |
|-----|--------|----------|---------|------------|
| **2.2** | طابعة إيصالات حرارية ESC/POS + درج النقدية | 🔴 حرجة | `escpos_printer_service.py` + `cash_drawer_service.py` + migration 009 (`hardware_config`) — إيصال كامل بقالب SRS (32 عمود)، تقارير X/Z، فتح الدرج بنبضة RJ11، ترميز عربي cp864→cp1256→cp720→utf-8، وضع dry_run آمن عند غياب العتاد | 33 |
| **1.3** | توليد باركود 1D + تكامل الماسح | 🟠 عالية | `barcode_service.py` + `scanner_service.py` — EAN-13 حتمي بنطاق المتجر GS1 "200" + رقم تحقق صحيح، Code128-B كامل (جدول 107 نمط ISO، مُتحقق ضد reportlab)، حلّ الباركود مع حارس المسح الابتعادي، ماسح keyboard-wedge بنافذة 150ms تميّز الكتابة البشرية عن الماسح | 43 |
| **3.2** | سير عمل مرتجع المشتريات | 🟠 عالية | `purchase_return_service.py` — دورة draft→approve→complete→cancel ذرية، تخصيص دفعات **FEFO-عكسي** (الأحدث صلاحية أولاً)، حارس الكمية القابلة للإرجاع (مشتريات − مرتجعات)، قيد محاسبي مدين 2100/دائن 4100 (إشعار دائن) أو 1000 (نقدي)، تسوية رصيد المورد + خفض paid_amount بأسلوب FIFO متوافق مع Gap #7 | 17 |
| **5.1** | اكتشاف أجهزة LAN (mDNS) | 🟠 عالية | `lan_discovery_service.py` — إعلان/استكشاف `_erp-standard-joumla._tcp.local.` عبر zeroconf مع تراجع رشيق لـ HTTP-fallback (فحص /health، حد 64 مرشح)، UPSERT للأجهزة المكتشفة، ping TCP بأمان | ضمن 28 |
| **5.2** | تفريغ طابور المزامنة تلقائياً | 🟠 عالية | `sync_queue_flush_service.py` — ربط انتقال offline→online عبر ربط بطار (`on_state_change` أُضيف لـ connectivity_monitor + إشارات Qt)، تهدئة 20 ساعة بقابلية حقن الساعة، نتائج صريحة بلا نجاح مزيف، تكيّف مع مخططي sync_queue الحقيقيين | ضمن 28 |

## إصلاح جذري إضافي

- **اتفاقية التسجيل**: `tests/unit/conftest.py` يفشل أي اختبار تسجّل فيه الخدمة ERROR — تم تحويل سجلات الشروط المُلتقطة/الإعدادية في `sync_queue_flush_service.py` (لا مُنفّذ تفريغ، فشل تفريغ مُلتقط، فشل قراءة عمق الطابور) من `logger.error` إلى `logger.warning` حسب اتفاقية المشروع.

## المعمارية والتوافق

- **الترميز العربي**: cp864 → cp1256 → cp720 → utf-8 مع تذكر الترميز الناجح للفك العكسي المطابق.
- **العتاد غائب ≠ عطل**: كل I/O مُغلَّف بـ try/except مع تراجع dry_run (`last_output` للتفتيش) — فشل الطابعة لا يُسقط تدفق البيع أبداً.
- **استيرادات مؤجلة**: pyserial/pyusb/PIL/zeroconf لا تُستورد إلا عند الاستخدام الفعلي — التطبيق يعمل بدونها.
- **عزلة الوحدات**: الخدمات الجديدة لا تعدل الخدمات الموجودة؛ الدمج في routes/UI لاحق دون تعارض.
- **Decimal** لكل الأموال، docstrings ثنائية اللغة (عربي/إنجليزي)، Python 3.10+ type hints.

## الملفات

```
src/services/escpos_printer_service.py      (جديد)
src/services/cash_drawer_service.py         (جديد)
src/services/barcode_service.py             (جديد)
src/services/scanner_service.py             (جديد)
src/services/purchase_return_service.py     (جديد)
src/services/lan_discovery_service.py       (جديد)
src/services/sync_queue_flush_service.py    (جديد)
src/core/local_migrations/migrations/009_add_hardware_config.py (جديد)
src/core/connectivity_monitor.py            (إضافة طفيفة: on_state_change hook)
tests/unit/services/test_escpos_hardware.py (جديد — 33)
tests/unit/services/test_barcode_scanner.py (جديد — 43)
tests/unit/services/test_purchase_return.py (جديد — 17)
tests/unit/services/test_lan_sync_gaps.py   (جديد — 28)
```

## نقاط الدمج المستقبلية (لا تعديلات مطلوبة الآن)

1. **الإيصال بعد البيع**: بعد نجاح `create_sale` — بناء dict من الـ Sale واستدعاء `ESCPOSPrinterService(db).print_receipt(sale_dict)` (fire-and-forget، يُفشل برفق دائماً).
2. **زر فتح الدرج / بعد الدفع النقدي**: `CashDrawerService(db).open_and_log(reason)`.
3. **POS keyPressEvent**: `event = self.scanner.feed(key.text())` ثم `product = self.scanner.process_scan_event(event)`.
4. **API**: `POST /purchase-returns` + `/approve|complete|cancel` + `GET /purchase-returns/returnable`.
5. **الإعدادات**: إدراج صف في `hardware_config` يكفي لتوصيل أي جهاز (network/serial/file/usb).

## الحالة النهائية لخريطة فجوات SRS

| GAP | الحالة |
|-----|--------|
| 1.1 وحدات، 1.2 FEFO، 1.3 باركود | ✅ ✅ ✅ |
| 2.1 سقف ائتماني، 2.2 ESC/POS، 2.3 ورديات | ✅ ✅ ✅ |
| 3.1 دفعات FIFO، 3.2 مرتجع مشتريات | ✅ ✅ |
| 4.1 تسعير، 4.2 مصاريف | ✅ ✅ |
| 5.1 اكتشاف LAN، 5.2 تفريغ تلقائي | ✅ ✅ |
| 5.3 تحرير تعاوني (متوسطة) | ⏳ مؤجلة — الوحيدة المتبقية |

**الاختبارات:** `python3 -m pytest tests/unit/services/ -q` (المتأثرة الجديدة كلها خضراء؛ أخطاء قديمة معروفة في test_payment_service/ملفات AI مفقودة — سابقة عن هذه التغييرات).

---

## الجولة الثانية — الدمج في API + إغلاق GAP-5.3 (التحرير التعاوني)

**التاريخ:** 2026-11-08 | **النتيجة:** 13/13 فجوات SRS مُغلقة كاملةً

### اكتشاف حرج مُصلَح: راوتر API كان معطلاً بالكامل بصمت
`import src.api.routes` كان يرمي `NameError: get_sales_service` (مُعرَّف سطر 2576 لكن مستخدم في `Depends()` سطر 1646) — و`app.register_routes()` يبتلع الاستثناء بـ warning → **كل نقاط `/api/v1` كانت ترجع 404**. الإصلاح: نقل التبعية أعلى الملف + إصلاح 3 أعطال كامنة في نقاط البيع (`Sale(created_by)`، `SaleItem(discount_amount)`، حقول ناقصة في `SaleResponse`).

### نقاط API المضافة (16، خلف المصادقة مثل باقي النقاط)
| المجموعة | النقاط |
|---|---|
| Purchase Returns (7) | `POST /purchase-returns` (+`/approve`,`/complete`,`/cancel`)، `GET /purchase-returns` (+`/{id}`، `/returnable`) — أخطاء الأعمال → HTTP 422 بتفاصيل ثنائية اللغة |
| POS Hardware (7) | `POST /sales/{id}/receipt`، `POST /pos/cash-drawer/open` + `GET status`، `POST /pos/reports/x|z`، `GET /products/scan/{barcode}`، `POST /products/{id}/assign-barcode`، `POST /products/{id}/barcode-label` |
| Sync & LAN (2) | `GET /lan/discover`، `POST /sync/flush` |

- **الطباعة بعد البيع**: انضمام اختياري `POST /sales?print_receipt=true` + حقل `receipt_preview` في الاستجابة (طباعة fire-and-forget لا تُفشل البيع أبداً — سبب الاختيار: الطابعة المتوقفة قد تُجمّد الطلب 3 ثوانٍ).
- **أثر جانبي إيجابي**: إصلاح الاستيراد أصلح اختبارين في test_websocket_endpoints كانا يفشلان.

### GAP-5.3 التحرير التعاوني — الفجوة الأخيرة (13/13)
- `src/services/collaboration_service.py` (855 سطر): أقفال تشاؤمية (acquire/release/heartbeat/purge) بساعة قابلة للحقن + تنازلية انزلاقية، بث WebSocket محمي (`notify_edit`/`notify_lock_change` عبر `WebSocketManager.broadcast` الحقيقي)، دفتر تعارضات الإصدارات (detect/resolve/list/get)، `get_record_version` (عمود version أو sha256(updated_at)).
- `src/services/collab_edit_guard.py`: سياق `guarded_edit()` بسطر واحد + `RecordLockedError` ثنائي اللغة.
- **وعي بالمخطط**: migration 026 يمتلك `sync_conflicts` بشكل متوافق-غير قابل لإعادة الاستخدام → جدول موازٍ `collab_sync_conflicts` للمخطط الجديد بلمس المخطط القديم.

### الاختبارات
- API الجديد: **16 passed** | التعاون: **38 passed** (10 تشغيلات مستقرة، اختبار تزامن 2 خيوط × 20 جولة) | الانحدار: **141 passed**
- الإجمالي التراكمي للجولتين: **195 اختبار ناجح**
