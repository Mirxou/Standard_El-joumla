# Release v5.2.1 – Performance Instrumentation & Incremental Backups

Date: 2025-11-23
Tag: v5.2.1

## 🚀 Summary
This release finalizes the performance observability layer, advanced role management UI, and introduces incremental/delta backup capability with chain awareness. It also stabilizes slow query logging, exportable metrics, and secure fallback behaviors.

## ✨ New Features
- Slow query logging with threshold (default 100ms) persisted in `slow_queries`.
- Dual-source slow queries view (in-memory vs persisted) in Performance Panel.
- IncrementalBackupService for full + delta snapshots (table-level checksum diffing).
- Metrics export (CSV/JSON) for historical performance records.
- Extended Roles Manager (CRUD, bulk assignment, permissions editing, user counts).
- Safe WeasyPrint optional import (PDF export guarded when system libs missing).
- Dynamic Redis availability re-check (ping) with graceful fallback to LRU cache.

## 🛡 Security & Reliability
- Brute-force login blocking and password strength evaluation retained from 5.2.0.
- Backup integrity (checksums + chain metadata) stabilized for incremental path.
- Optional Redis disabled automatically if module/connection unavailable.

## 🧪 Test Coverage
- 92 passed / 1 skipped.
- High coverage modules: `incremental_backup_service.py` (87%), `vendor_rating_service.py` (84%), `theme_manager.py` (98%).
- Overall coverage: 38% (focus remains on critical new paths rather than legacy models).

## 📁 Key Files Changed
- `src/core/database_manager.py` (slow query timing + table definition)
- `src/services/performance_service.py` (metrics export, DB slow query retrieval)
- `src/ui/admin/performance_panel.py` (dual tables, extended columns)
- `src/ui/admin/roles_manager.py` (CRUD + bulk assignment dialogs)
- `src/core/incremental_backup_service.py` (new service)
- `src/services/cache_service.py` (dynamic Redis fallback)
- `src/services/reports_service.py` (optional PDF gracefully handled)

## 🔄 Upgrade Steps
1. Pull tag `v5.2.1`.
2. Install/upgrade dependencies:
   ```bash
   pip install -r requirements.txt -r requirements-test.txt
   ```
3. Run sanity tests:
   ```bash
   pytest -q tests/test_slow_query_logging.py tests/test_incremental_backup.py
   ```
4. (Optional) Configure `SLOW_QUERY_THRESHOLD_MS` via code (`db_manager.slow_query_threshold_ms`).
5. Initialize incremental backups: first call `create_full_backup()`, then `create_incremental_backup()` after data changes.

## 🔧 Configuration Notes
- Redis: set `CACHE_USE_REDIS=1` and `REDIS_URL=redis://host:6379/0`; fallback occurs automatically if unreachable.
- Backups: ensure writable `data/backups/` directory and sufficient disk space.
- PDF Export: install system GTK/Pango stack if PDF reports are required.

## 🔮 Future Directions (Post 5.2.1)
- Incremental chain automated restore application.
- UI control to adjust slow query threshold.
- Coverage expansion for legacy service/model layers.
- Historical metrics visualization (charts + trend anomalies).

## ✅ Verification Checklist
- [ ] Slow queries appear after inducing heavy/inefficient query.
- [ ] Metrics export files generated (CSV & JSON) contain expected headers.
- [ ] Full backup + incremental backup directory structure serialized with metadata.
- [ ] Roles creation/edit/delete reflects immediately in UI and DB.
- [ ] Redis fallback logs no errors if server unreachable.

## 📜 License & Contact
Licensed under MIT. For support open an issue or email support@inventory-system.com.

---
Enjoy the enhanced observability and smarter backup workflow in v5.2.1!
