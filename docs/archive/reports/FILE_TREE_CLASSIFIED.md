# 🌳 شجرة الملفات المصنفة - Classified File Tree

**التاريخ:** 2025-12-21  
**الهدف:** تصنيف جميع الملفات حسب الأهمية لتسهيل التنظيف والصيانة

---

## 📊 دليل التصنيف

- 🔴 **Critical** - ملفات حرجة (لا يمكن حذفها)
- 🟠 **Important** - ملفات مهمة (يُنصح بالاحتفاظ بها)
- 🟡 **Optional** - ملفات اختيارية (يمكن حذفها إذا لزم الأمر)
- ⚪ **Can Delete** - ملفات يمكن حذفها بأمان (تقارير قديمة، ملفات مؤقتة)

---

## 🔴 Critical Files (ملفات حرجة)

### Root Level
```
🔴 main.py                          # نقطة الدخول الرئيسية للتطبيق
🔴 requirements.txt                 # متطلبات Python
🔴 docker-compose.yml               # إعدادات Docker
🔴 Dockerfile                       # Docker image للتطبيق الكامل
🔴 Dockerfile.api                   # Docker image للـ API فقط
🔴 LICENSE.txt                      # الرخصة
🔴 README.md                        # التوثيق الرئيسي
🔴 .docker.env.example              # مثال متغيرات البيئة
```

### Source Code (`src/`)
```
src/
├── 🔴 __init__.py
├── 🔴 core/
│   ├── 🔴 database_manager.py      # إدارة قاعدة البيانات
│   ├── 🔴 config_manager.py        # إدارة الإعدادات
│   ├── 🔴 permission_manager.py    # إدارة الصلاحيات
│   ├── 🔴 security_service.py      # الخدمات الأمنية
│   └── 🔴 window_manager.py        # إدارة النوافذ
├── 🔴 models/
│   ├── 🔴 product.py               # نموذج المنتج
│   ├── 🔴 sale.py                  # نموذج المبيعات
│   ├── 🔴 purchase.py              # نموذج المشتريات
│   ├── 🔴 user.py                  # نموذج المستخدم
│   ├── 🔴 customer.py              # نموذج العميل
│   ├── 🔴 supplier.py              # نموذج المورد
│   └── 🔴 warehouse.py              # نموذج المستودع
├── 🔴 services/
│   ├── 🔴 inventory_service.py     # خدمة المخزون
│   ├── 🔴 sales_service.py         # خدمة المبيعات
│   ├── 🔴 purchase_service.py      # خدمة المشتريات
│   └── 🔴 payment_service.py       # خدمة الدفع
├── 🔴 api/
│   ├── 🔴 app.py                   # تطبيق FastAPI الرئيسي
│   ├── 🔴 routes.py                # مسارات API
│   ├── 🔴 auth.py                  # المصادقة
│   └── 🔴 middleware.py            # Middleware
└── 🔴 ui/
    ├── 🔴 windows/
    │   ├── 🔴 main_window.py       # النافذة الرئيسية
    │   └── 🔴 [other windows]      # نوافذ أخرى مهمة
    └── 🔴 dialogs/                 # الحوارات
```

### Web App (`web/`)
```
web/
├── 🔴 package.json                 # متطلبات Node.js
├── 🔴 tsconfig.json                # إعدادات TypeScript
├── 🔴 next.config.js               # إعدادات Next.js (إن وجد)
├── 🔴 README.md                    # توثيق Web App
├── 🔴 app/
│   ├── 🔴 layout.tsx               # Layout الرئيسي
│   ├── 🔴 page.tsx                 # الصفحة الرئيسية
│   └── 🔴 api/                    # API Routes
├── 🔴 lib/
│   ├── 🔴 config/api.ts            # تكوين API
│   ├── 🔴 api/client.ts           # عميل API
│   ├── 🔴 auth-context.tsx        # سياق المصادقة
│   └── 🔴 types/index.ts          # أنواع TypeScript
└── 🔴 components/
    ├── 🔴 dashboard-home.tsx      # Dashboard
    ├── 🔴 products-management.tsx  # إدارة المنتجات
    └── 🔴 [other components]      # مكونات أخرى مهمة
```

### Mobile App (`mobile/`)
```
mobile/
├── 🔴 package.json                # متطلبات React Native
├── 🔴 tsconfig.json               # إعدادات TypeScript
├── 🔴 app.json                    # إعدادات Expo
├── 🔴 index.js                    # نقطة الدخول
├── 🔴 README.md                   # توثيق Mobile App
└── 🔴 src/
    ├── 🔴 config/api.ts           # تكوين API
    ├── 🔴 services/api.ts         # خدمة API
    └── 🔴 App.tsx                 # المكون الرئيسي
```

### Configuration Files
```
🔴 config/app_config.json          # إعدادات التطبيق
🔴 .gitignore                      # ملفات Git المهملة
🔴 pytest.ini                      # إعدادات الاختبارات
```

---

## 🟠 Important Files (ملفات مهمة)

### Documentation
```
🟠 docs/
│   ├── 🟠 README.md
│   ├── 🟠 API_DOCUMENTATION.md
│   ├── 🟠 CONFIGURATION_GUIDE.md
│   ├── 🟠 SECURITY_GUIDE.md
│   └── 🟠 [other guides]
🟠 USER_GUIDE_AR.md                # دليل المستخدم بالعربية
🟠 USAGE_GUIDE.md                  # دليل الاستخدام
🟠 QUICK_START_GUIDE.md            # دليل البدء السريع
🟠 TESTING_GUIDE.md                # دليل الاختبارات
🟠 DEPLOYMENT_GUIDE.md             # دليل النشر
🟠 README.DOCKER.md                # دليل Docker
```

### Tests
```
🟠 tests/
│   ├── 🟠 unit/                   # اختبارات الوحدة
│   ├── 🟠 integration/            # اختبارات التكامل
│   └── 🟠 api/                    # اختبارات API
🟠 web/__tests__/                  # اختبارات Web App
```

### Scripts
```
🟠 scripts/
│   ├── 🟠 test_api.py             # اختبار API
│   ├── 🟠 docker-start.sh        # بدء Docker
│   └── 🟠 [other scripts]         # سكريبتات أخرى مفيدة
```

### Migrations
```
🟠 migrations/                      # ملفات الهجرة
```

### Assets
```
🟠 assets/                          # الموارد (أيقونات، قوالب)
🟠 web/public/                      # ملفات عامة للـ Web
```

---

## 🟡 Optional Files (ملفات اختيارية)

### Backup Files
```
🟡 *.backup                         # ملفات النسخ الاحتياطي
🟡 web/components/inventory-management.tsx.backup
```

### Temporary Files
```
🟡 *.tmp
🟡 *.log                            # ملفات السجلات (يمكن إعادة إنشائها)
🟡 logs/                            # مجلد السجلات
```

### Build Artifacts
```
🟡 web/.next/                       # ملفات بناء Next.js (يمكن إعادة إنشائها)
🟡 web/coverage/                    # تقارير التغطية (يمكن إعادة إنشائها)
🟡 htmlcov/                         # تقارير التغطية HTML
🟡 __pycache__/                     # ملفات Python المترجمة
🟡 *.pyc                            # ملفات Python المترجمة
🟡 node_modules/                    # حزم Node.js (يمكن إعادة تثبيتها)
```

### Database Files (Development)
```
🟡 *.db                             # قواعد بيانات SQLite للتطوير
🟡 test_db.db                       # قاعدة بيانات اختبار
🟡 standard.db                      # قاعدة بيانات قياسية
```

---

## ⚪ Can Delete (ملفات يمكن حذفها)

### Old Reports & Summaries (تقارير قديمة)
```
⚪ *_SUMMARY.md
⚪ *_REPORT.md
⚪ *_COMPLETION*.md
⚪ *_STATUS*.md
⚪ *_FINAL*.md
⚪ COMPLETE_FINAL_SUMMARY.md
⚪ FINAL_COMPLETION_REPORT.md
⚪ FINAL_STATUS_REPORT.md
⚪ COMPLETION_SUMMARY.md
⚪ COMPLETION_CONFIRMATION.md
⚪ QUICK_FINAL_SUMMARY.md
⚪ EXECUTIVE_SUMMARY.md
⚪ PROJECT_COMPLETION_SUMMARY.md
⚪ PROJECT_COMPLETE.md
⚪ READY_FOR_LAUNCH.md
⚪ READY_TO_COMMIT.md
⚪ LAUNCH_READY.md
```

### Session Reports (تقارير الجلسات)
```
⚪ SESSION_*.md
⚪ SESSION_*.txt
⚪ SESSION_2_FINAL_REPORT.md
⚪ SESSION_3_SUMMARY.md
⚪ VERIFICATION_REPORT_SESSION_2.md
⚪ FIXES_APPLIED_SESSION_2.md
```

### Phase Reports (تقارير المراحل)
```
⚪ PHASE_*.md
⚪ PHASE_3_ROADMAP.md
⚪ PHASE_5_COMPLETION_REPORT.md
⚪ PHASE_6_COMPLETION_REPORT.md
⚪ PHASE_7_PROPOSAL.md
```

### Coverage Reports (تقارير التغطية)
```
⚪ COVERAGE_*.md
⚪ FINAL_COVERAGE_*.md
⚪ TEST_COVERAGE_PROGRESS.md
⚪ COVERAGE_START_SUMMARY.md
⚪ COVERAGE_EXECUTION_PLAN.md
⚪ COVERAGE_IMPROVEMENT_PLAN.md
⚪ COVERAGE_REPORT.md
⚪ COVERAGE_ACTION_PLAN.md
⚪ web/COVERAGE_95_ROADMAP.md
⚪ web/COVERAGE_PLAN_95_PERCENT.md
```

### Test Reports (تقارير الاختبارات)
```
⚪ TEST_*.md
⚪ TESTING_*.md
⚪ TEST_RESULTS_SUMMARY.md
⚪ FINAL_TEST_REPORT.md
⚪ TESTING_SUMMARY.md
⚪ TESTS_FIXES_SUMMARY.md
⚪ TESTING_INSTRUCTIONS.md
⚪ TEST_SIGNALS_PROTOCOL.md
⚪ web/TEST_REPORT*.md
⚪ web/COMPLETE_TEST_SUMMARY.md
⚪ web/TESTS_README.md
```

### Audit & Review Reports (تقارير المراجعة)
```
⚪ *_AUDIT*.md
⚪ *_REVIEW*.md
⚪ COMPREHENSIVE_AUDIT_REPORT.md
⚪ PROFESSIONAL_REVIEW.md
⚪ web/DEEP_AUDIT_REPORT.md
⚪ web/DEEP_FIXES_REPORT.md
⚪ web/REVIEW_FINAL_REPORT.md
```

### Cleanup Reports (تقارير التنظيف)
```
⚪ CLEANUP_*.md
⚪ CLEANUP_COMPLETE.md
⚪ CLEANUP_PLAN.md
⚪ DEEP_CLEANUP_REPORT.md
⚪ DESKTOP_CLEANUP_SUMMARY.md
⚪ POST_MIGRATION_CLEANUP_SUMMARY.md
```

### Migration Reports (تقارير الهجرة)
```
⚪ *_MIGRATION*.md
⚪ FINAL_MIGRATION_SUMMARY.md
⚪ web/MIGRATION_GUIDE.md            # ⚠️ قد يكون مفيداً - راجع قبل الحذف
```

### Window Manager Reports (تقارير Window Manager)
```
⚪ WINDOW_*.md
⚪ WINDOW_MANAGER_*.md
⚪ WINDOW_AUDIT_*.md
⚪ WINDOW_STATE_*.md
```

### Multi-* Reports (تقارير متعددة)
```
⚪ MULTI_*.md
⚪ MULTI_COMPANY_*.md
⚪ MULTI_CURRENCY_*.md
⚪ MULTI_WAREHOUSE_*.md
```

### Other Old Reports
```
⚪ ACHIEVEMENT_REPORT.md
⚪ ACTION_ITEMS.md
⚪ BENCHMARK_README.md
⚪ CHAOS_TEST_GUIDE.md
⚪ CODE_REVIEW_*.md
⚪ COMMIT_MESSAGE.md
⚪ DATA_FLOW_EXPLANATION.md
⚪ DASHBOARD_CHARTS_FIX.md
⚪ DEADLOCK_FIX_SUMMARY.py          # ⚠️ ملف Python - راجع قبل الحذف
⚪ DETAILED_CHANGELOG.md
⚪ DOCKER_FIX.md
⚪ DOCKER_TROUBLESHOOTING.md
⚪ FILES_REVIEW_REPORT.md            # ⚠️ هذا الملف نفسه - احتفظ به!
⚪ FIXES_APPLIED.md
⚪ INTEGRATE_TELEMETRY.md
⚪ INTEGRATION_TEST_GUIDE.md
⚪ MERGE_STATUS.md
⚪ NEXT_STEPS.md
⚪ PERFORMANCE_*.md
⚪ QUICK_TEST.md
⚪ SALES_DIALOG_MERGE_PLAN.md
⚪ SOLUTION_SUMMARY.py               # ⚠️ ملف Python - راجع قبل الحذف
⚪ TECH_STACK_RESPONSE.md
⚪ TELEMETRY_*.md
⚪ TASKS_COMPLETION_SUMMARY.md
⚪ WHOLESALE_INVOICE_REVIEW.md
⚪ MATH_UTILS_INTEGRATION_PLAN.md
⚪ DEVELOPMENT_ROADMAP_TO_ORACLE_ERP.md
```

### Web App Old Reports
```
⚪ web/ACHIEVEMENT_REPORT.md
⚪ web/ACTION_ITEMS.md
⚪ web/COMPLETE_INDEX.md
⚪ web/COMPLETION_REPORT.md
⚪ web/DOCUMENTATION_INDEX.md
⚪ web/FILE_INDEX.md
⚪ web/FINAL_COMPLETION_REPORT.md
⚪ web/FINAL_STATUS.md
⚪ web/SUMMARY.md
⚪ web/START_HERE.md                # ⚠️ قد يكون مفيداً - راجع قبل الحذف
⚪ web/QUICK_START.md               # ⚠️ قد يكون مفيداً - راجع قبل الحذف
⚪ web/COMPLETE_INDEX.md
⚪ web/PHASE_5_COMPLETION_REPORT.md
```

### Temporary Python Scripts
```
⚪ _gen_tree.py                     # سكريبت مؤقت
⚪ _tree_gen.py                     # سكريبت مؤقت
⚪ check_*.py                        # سكريبتات فحص مؤقتة
⚪ fix_*.py                          # سكريبتات إصلاح مؤقتة
⚪ setup_*.py                        # سكريبتات إعداد مؤقتة
⚪ test_*.py                         # سكريبتات اختبار مؤقتة (في root)
⚪ simulate_*.py                     # سكريبتات محاكاة
⚪ clear_cache.py
⚪ generate_dummy_data.py
⚪ rename_report.py
```

### Old/Unused Files
```
⚪ App.tsx                          # في root - قديم
⚪ InventoryPage.tsx                # في root - قديم
⚪ index.ts                         # في root - قديم
⚪ productService.ts                # في root - قديم
⚪ package.json                     # في root - قديم (يوجد في web/ و mobile/)
⚪ package-lock.json                # في root - قديم
⚪ tree-full.txt                    # ملف شجرة قديم
⚪ file_tree_raw.txt                # ملف مؤقت
⚪ test_output.txt                  # ملف اختبار مؤقت
⚪ coverage.xml                     # تقرير تغطية قديم
```

---

## 📋 ملخص التصنيف

### إحصائيات سريعة:
- 🔴 **Critical:** ~150 ملف (لا يمكن حذفها)
- 🟠 **Important:** ~100 ملف (يُنصح بالاحتفاظ بها)
- 🟡 **Optional:** ~50 ملف (يمكن حذفها إذا لزم الأمر)
- ⚪ **Can Delete:** ~200+ ملف (تقارير قديمة وملفات مؤقتة)

### توصيات التنظيف:

1. **حذف آمن فوراً:**
   - جميع ملفات `*_SUMMARY.md`, `*_REPORT.md`, `*_COMPLETION*.md`
   - ملفات `SESSION_*.md`
   - ملفات `PHASE_*.md`
   - ملفات `COVERAGE_*.md`
   - ملفات `WINDOW_*.md`
   - ملفات `MULTI_*.md`

2. **مراجعة قبل الحذف:**
   - `web/MIGRATION_GUIDE.md` - قد يكون مفيداً للمطورين الجدد
   - `web/START_HERE.md` - قد يكون مفيداً للمبتدئين
   - `web/QUICK_START.md` - قد يكون مفيداً للبدء السريع
   - ملفات Python في root (`check_*.py`, `fix_*.py`) - قد تكون مفيدة للصيانة

3. **احتفظ دائماً:**
   - جميع ملفات `README.md`
   - جميع ملفات `requirements.txt`, `package.json`
   - جميع ملفات الإعدادات (`*.json`, `*.yml`, `*.yaml`)
   - جميع ملفات الكود المصدري (`*.py`, `*.ts`, `*.tsx`)

---

## 🗑️ سكريبت التنظيف المقترح

يمكن إنشاء سكريبت PowerShell/Bash لحذف الملفات غير المهمة تلقائياً:

```powershell
# PowerShell Script (مثال)
Get-ChildItem -Recurse -File | Where-Object {
    $_.Name -match '.*_(SUMMARY|REPORT|COMPLETION|STATUS|FINAL|SESSION|PHASE|COVERAGE|AUDIT|REVIEW|CLEANUP|MIGRATION|WINDOW|MULTI)\.md$'
} | Remove-Item -WhatIf  # استخدم -WhatIf أولاً للاختبار
```

---

**ملاحظة:** قبل حذف أي ملف، تأكد من:
1. ✅ عمل نسخة احتياطية من المشروع
2. ✅ مراجعة الملفات المهمة في قسم "مراجعة قبل الحذف"
3. ✅ اختبار السكريبت باستخدام `-WhatIf` أولاً

---

**تم إنشاء التقرير:** 2025-12-21  
**آخر تحديث:** 2025-12-21

