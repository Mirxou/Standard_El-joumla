# Release Checklist — v5.1.0 (UX Polish)

Date: 2025-11-21

## 1) Preflight
- [ ] All UX tasks merged: performance tab, status bar, notifications controls, quick action
- [ ] `CHANGELOG.md` updated with 5.1.0 entry
- [ ] `RELEASE_v5.1.0_FINAL.md` reviewed (highlights, upgrade notes, verification)
- [ ] Tag exists locally: `v5.1.0`

## 2) Tests
- [ ] Targeted tests pass:
  - Run: `pytest -q tests\test_theme_and_notifications.py`
- Note: Broader API tests may be unrelated; keep scope to v5.1.0 UX.

## 3) Push
- [ ] Remote set: `git remote -v` (add origin if missing)
- [ ] Push branch + tag (choose one):
  - Manual:
    ```powershell
    git push -u origin master
    git push origin v5.1.0
    ```
  - Script:
    ```powershell
    .\scripts\push_release.bat
    ```

## 4) GitHub Release
- [ ] Create a new Release: `v5.1.0`
- [ ] Title: `v5.1.0 — UX Polish`
- [ ] Body: paste from `RELEASE_v5.1.0_FINAL.md`
- [ ] Attach artifacts (optional): screenshots, demo gif

## 5) Post-Release
- [ ] Update roadmap/status docs if needed
- [ ] Notify team/stakeholders
- [ ] Monitor user feedback

## Notes
- New QSettings keys: `theme`, `notifications/interval_seconds`, `notifications`, `quick_actions/enabled`
- No database migrations in 5.1.0
