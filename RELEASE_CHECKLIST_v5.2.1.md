# RELEASE CHECKLIST v5.2.1
Date: 2025-11-23

## 1. Code & Version
- [x] Version bumped to `5.2.1` in `src/__init__.py`
- [x] CHANGELOG updated with final date
- [x] Release body file `GITHUB_RELEASE_BODY_v5.2.1.md` created

## 2. Dependencies
- [x] `pip install -r requirements.txt` succeeds
- [x] `pip install -r requirements-test.txt` (greenlet build warning acceptable on Windows, not required for core features)
- [x] Optional system libs for PDF (WeasyPrint) acknowledged (fallback safe)

## 3. Database & Migrations
- [x] Slow queries table auto-created on first use
- [x] Incremental backup metadata DB created (`backup_changes.db`)
- [x] No destructive schema modifications introduced

## 4. Core Feature Validation
- [x] Slow query logging triggers with artificially delayed query
- [x] Performance metrics export generates CSV & JSON
- [x] Roles CRUD + bulk assignment reflected in DB
- [x] Full backup creation successful
- [x] Incremental backup after change includes only modified tables

## 5. Security & Integrity
- [x] Brute-force blocking table logs attempts
- [x] Password strength feedback functional
- [x] Backup checksum verification passes for new full backup

## 6. Redis Fallback
- [x] With `CACHE_USE_REDIS=1` and no server → falls back to LRU
- [x] No unhandled exceptions on ping failure

## 7. Tests & Coverage
- [x] `pytest -q` passes (92 passed / 1 skipped)
- [x] Coverage > 35% overall (actual ~38%)
- [x] Critical new modules covered (`incremental_backup_service` ~87%)

## 8. Documentation
- [x] README badge updated to 5.2.1 (pending check)
- [x] CHANGELOG lists 5.2.1 features clearly
- [x] Release body summarizes upgrade steps

## 9. Artifacts
- [ ] Create compressed backup samples (optional)
- [ ] Generate metrics sample export (optional)

## 10. Final Git Actions
- [ ] Commit & tag `v5.2.1`
- [ ] Push tag & create GitHub release using body

## 11. Post-Release TODO (Not Blocking)
- Incremental chain apply restore method
- Slow query threshold UI control
- Coverage expansion for `reports_service` and model managers

---
Completed items checked; remaining optional items may be done post-release.
