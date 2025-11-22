# ✅ Release Checklist v5.2.0

Release Date: 2025-11-22
Branch: v5.2.0-dev
Type: Major Security & Performance Enhancement

---
## 1. Pre-Release Validation
- [ ] Pull latest branch: `git pull origin v5.2.0-dev`
- [ ] Confirm version bump to `5.2.0` in `src/__init__.py`
- [ ] Review CHANGELOG section `[5.2.0]`
- [ ] Ensure README v5.2.0 section present
- [ ] Run full test suite: `pytest -q` (all pass)
- [ ] Validate new integration tests:
  - 2FA flow
  - RBAC schema detection
  - Backup restore checksum

## 2. Security & RBAC
- [ ] TOTP activation and verification tested in UI
- [ ] Brute-force lockout triggers after threshold
- [ ] Password strength feedback shown (manual QA)
- [ ] Roles Manager panel loads with expected roles
- [ ] Audit Viewer panel displays entries (simulate actions)

## 3. Backup & Restore
- [ ] Set encryption password (if required)
- [ ] Create encrypted backup (UI or service)
- [ ] Run `verify_backup` on latest backup (match = true)
- [ ] Restore backup; confirm checksum verified
- [ ] Auto-backup scheduling enabled & executes at least once (log check)
- [ ] Old backups cleanup behavior validated (reduce count)

## 4. Performance & Caching
- [ ] Performance panel auto-refresh every 5s
- [ ] Cache stats panel lists caches & top items
- [ ] Hit/Miss counters increment under simulated load
- [ ] Slow query table populates (trigger artificial slow query)

## 5. Documentation & Metadata
- [ ] CHANGELOG finalized
- [ ] GitHub release body drafted (`GITHUB_RELEASE_BODY_v5.2.0.md`)
- [ ] Release checklist complete, all boxes checked
- [ ] Screenshots captured (optional) for new panels

## 6. Packaging & CI/CD
- [ ] Docker build: `docker build -t logical-version:5.2.0 .` succeeds
- [ ] Optional push to registry
- [ ] Verify runtime health endpoint (if API active)

## 7. Post-Release
- [ ] Tag created: `git tag v5.2.0 && git push origin v5.2.0`
- [ ] Publish release on GitHub with body
- [ ] Announce internal & user channels
- [ ] Plan v5.2.1 items created (issues or roadmap)

---
## Quick Commands
```bash
pytest -q
python main.py  # launch UI
python - <<'PY'
from src.services.backup_service import BackupService; from src.core.database_manager import DatabaseManager; db=DatabaseManager('data/app.db'); db.initialize(); bs=BackupService(db); bs.set_encryption_password('Strong#Pass99'); print(bs.create_backup(encrypt=True, compress=True));
PY
```

## Rollback Strategy
- Use latest unencrypted backup or previous tag `v5.1.0`
- Restore database file and restart application

---
Prepared by: Release Automation / GitHub Copilot
Status: Draft
