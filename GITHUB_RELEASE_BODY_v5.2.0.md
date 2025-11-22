# v5.2.0 – Security, Performance & Reliability Upgrade

> Date: 2025-11-22  
> Branch: `v5.2.0-dev`  
> Type: Major Enhancement Release

## 🚀 Highlights
- Multi-layer caching (LRU + TTL + optional Redis) with live stats & top hot keys panel.
- Real-time performance dashboard: CPU, RAM, DB size, query count, avg latency, slow queries list.
- Encrypted backup system (password-derived AES-256 / PBKDF2HMAC + Fernet) + checksum validation.
- Scheduled auto-backups + cleanup + non-invasive integrity check (`verify_backup`).
- Adaptive RBAC & audit schema handling (no destructive migrations needed).
- Integrated TOTP 2FA login second step + brute-force lockout + password strength feedback.
- New admin panels: Roles, Audit Viewer (lite), Sessions, Performance, Cache Stats.
- Added integration tests for 2FA flow, RBAC schema variants, backup checksum integrity.

## 🔐 Security
- Dynamic column detection for roles/audit tables – fixes prior "no such column" errors.
- Login dialog now performs conditional TOTP challenge after password success.
- Brute-force mitigation: tracks failed attempts with configurable thresholds.
- Password strength scoring (length, character classes, repetition, common words) returned via API/service.

## 💾 Backup & Restore
- Metadata now embeds `database_checksum_sha256` & encrypted payload checksum.
- Restore aborts if checksum mismatch – ensures integrity.
- `verify_backup(name)` method allows integrity check without altering current DB.
- Auto-backup interval scheduler with cleanup of older backups beyond retention count.

## ⚡ Performance & Caching
- Performance panel auto-refresh (5s) + slow queries table.
- Cache statistics panel: per-cache size, hit/miss, evictions, expirations, usage %, overall hit rate.
- Aggregated cache hit rate merged into core performance metrics.

## 🧪 Testing
New integration tests:
- `test_security_2fa_flow.py` – real TOTP generation & verification.
- `test_rbac_schema_detection.py` – supports both `id/name` and `role_id/role_name` schemas.
- `test_backup_restore_checksum.py` – encrypted backup creation, verify + restore with checksum.

## 📝 Docs
- README updated with full v5.2.0 feature list & security/backup expansions.
- Changelog section `[5.2.0]` added (upgrade notes + next roadmap).
- Release checklist (`RELEASE_CHECKLIST_v5.2.0.md`) prepared.

## ✅ Upgrade Notes
1. Pull latest: `git pull origin v5.2.0-dev`.
2. Optional: set `CACHE_USE_REDIS=1` & `REDIS_URL` for Redis usage.
3. Set backup encryption password before encrypted backups.
4. Run tests: `pytest -q`.
5. Verify at least one encrypted backup & integrity check.

## 🔮 Roadmap (v5.2.1)
- DB-level slow query instrumentation.
- Exportable performance metrics (CSV/JSON).
- Extended RBAC UI (expiry, bulk actions).
- Incremental/delta backup strategy.

## 🐛 Fixes & Internal
- Resolved schema mismatch errors in role/audit services via adaptive mapping.
- Enhanced reliability of restore with checksum verification path.

## ⏪ Rollback
Use most recent pre-5.2.0 backup or tag `v5.1.0`; restore DB file and restart.

---
**Tag**: `v5.2.0`  
**Author**: GitHub Copilot / AI Toolkit  
**Status**: Ready for tagging & publication
