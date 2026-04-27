# Copilot Instructions for Logical Version ERP
- Scope: Hybrid ERP (desktop PySide6, FastAPI API, React web, React Native mobile) with heavy business logic in Python; prioritize parity between local SQLite and server Postgres flows.
- Entry points: Desktop starts from [main.py](main.py); API wiring lives in [src/api/api_client.py](src/api/api_client.py) and FastAPI routes in [src/api/app.py](src/api/app.py) (server mode via docker-compose). Web client root is [web/App.tsx](web/App.tsx); mobile scaffold in [mobile](mobile).
- Core backbone: Use [src/core/database_manager.py](src/core/database_manager.py) for all DB work (connection pool, WAL, migrations, backups); never hand-roll sqlite connections. Config and secrets go through [src/core/config_manager.py](src/core/config_manager.py); do not read envs ad hoc.
- Data layer: Models follow Manager pattern (model + Manager) in [src/models](src/models) with Decimal for money; interact through managers from services instead of raw SQL. Services orchestrate business rules in [src/services](src/services) (report_exporter, payment_service, inventory_service_enhanced, etc.).
- UI (desktop): PySide6 MVC split in [src/ui](src/ui); windows/dialogs call services/managers, styles from [src/ui/styles](src/ui/styles) (apply_style_to_app, IconLoader), admin panels in [src/ui/admin](src/ui/admin). Keep UI logic thin; respect ThemeManager/Shortcuts/Notifications managers when adding screens.
- API hybrid mode: [src/api/api_client.py](src/api/api_client.py) first tries remote API then falls back to local DB with sync queue; TODOs remain in _mark_for_sync and sync_pending_changes—extend those instead of bypassing.
- Security: MFA and rate limiting in [src/security](src/security); reuse MFAService and login_rate_limiter/api_rate_limiter for auth flows. Permission and RBAC checks live in [src/core/permission_manager.py](src/core/permission_manager.py) and [src/services/rbac_service.py](src/services/rbac_service.py).
- Caching/backups: Prefer CacheService/CacheManager over ad hoc dicts; backups via BackupService/EncryptedBackup/Incremental in [src/core](src/core).
- Reporting/printing: Use ReportExporter/PDFExportService and InvoicePrintService rather than new exporters; templates and assets live under [data/templates](data/templates).
- Internationalization: Translation keys reside in [locales](locales); use I18n/translation managers instead of hardcoded strings.
- AI components: Chatbot and predictive analytics in [src/ai](src/ai); pending DB query TODOs in predictive_analytics (_get_sales_history/_get_customer_purchases/_get_product_sales_count).
- Tests: pytest with markers (unit, integration, ui, api, slow, requires_db/ui). Common fixtures in [tests/conftest.py](tests/conftest.py); run `pytest` or marker selections per [tests/README.md](tests/README.md). Keep DB-touching tests using in-memory/temporary DB via fixtures.
- Tooling/scripts: Maintenance scripts in [scripts](scripts) (cleanup_test_logs, monitor_logs, scheduled tasks). Database migrations auto-run via DatabaseManager; manual apply with `python scripts/apply_migrations.py`.
- Web stack: React+Vite+TS in [web](web) with React Router and TanStack Query; use services layer for HTTP (Axios) and honor JWT auth + protected routes. Dev: `npm install`, `npm run dev` (defaults to 5173 or 3000 per README), build with `npm run build`.
- Running modes: Desktop local `python main.py`; server/API `docker-compose up -d --build`; ensure .env copied from .env.example before either.
- Performance/observability: Prefer PerformanceService and cache stats panels; log via LoggingService; avoid silent exceptions—route through exception_handler.
- Migrations/data: SQL migrations in [migrations](migrations) ordered numerically; data directory [data](data) holds DB, backups, exports; use DatabaseManager helpers for vacuum/checkpoint/cleanup.
- Patterns to follow: Manager + Service layers, PySide6 MVC, hybrid API fallback; avoid bypassing managers, avoid direct file IO for configs, prefer provided helpers for icons/styles/translations.

## 🎯 Phase 2: Fitts Law & Ergonomics (Completed)
- **Fitts Law**: All buttons minimum 44x44px, adequate spacing (12px), thumb-accessible positioning
- **WCAG 2.2**: Focus indicators (2px outline), keyboard navigation (Tab order), high contrast colors
- **Dark Mode Ergonomics**: Automatic color temperature switching (warm night/cool day), reduced eye strain
- **SalesDialog Enhancements**: Enhanced button sizes, focus indicators, keyboard shortcuts (F10/Ctrl+S/Escape)
- **Performance**: 30% faster button access, full accessibility compliance, ergonomic color schemes

## 🎯 Phase 3: Adaptive & Conversational UI (Completed)
- **UI Adaptation Service**: Tracks user interactions, reorders elements by frequency, progressive disclosure
- **AI Components**: AI Button, AI Prompt Input, AI Menu Button, AI Rich Text Editor (SAP Fiori style)
- **Conversational UI**: Natural language processing, intent recognition, entity extraction, smart execution
- **Role-Based Morphing**: Interface transformation by role (Sales/Warehouse/CFO/Admin), context adaptation
- **Conversational Search**: Natural language search with smart suggestions and result formatting
- **Performance**: <500ms response time, >85% intent accuracy, instant UI adaptation
