# ✅ Comprehensive Test Plan — v5.0.0 (User Experience Revolution)

- Version: v5.0.0
- Date: 2025-11-21
- Owner: QA/Dev Team
- Application: Desktop ERP (PySide6, SQLite)

---

## 1. Scope & Objectives
- Validate new UX features in v5.0.0:
  - Dark/Light Theme system (ThemeManager)
  - Keyboard Shortcuts system (Shortcuts Manager)
  - Smart Notifications system (NotificationChecker + Center + Tray)
- Ensure no regressions in core modules: Inventory, Sales, Purchases, Reports, Accounts, Printing, Backup/Restore, Search/Filters.
- Confirm Arabic RTL usability, accessibility, and persistence (QSettings).

Out of scope:
- New server-side APIs (none added in this version)
- Mobile client

Assumptions:
- Python and PySide6 environment installed; app runs locally on Windows.
- SQLite DB is available and initialized with seed data.

---

## 2. Test Strategy
- Pyramid approach:
  - Unit tests for managers/helpers where feasible.
  - Integration/UI manual verification for UX-heavy features.
  - Light performance and accessibility passes.
- Types:
  - Unit, Component, Integration (UI), E2E smoke, Regression
  - Non-functional: Performance, Usability, Accessibility (RTL), i18n/l10n, Security, Backup/Restore

Tools/Artifacts:
- Runner: `run_tests.bat` / `pytest.ini`
- Manual scripts and checklists in this plan
- Defects tracked in repository issues

---

## 3. Environments
- OS: Windows 10/11 (x64)
- Python: 3.10+ (align with `requirements.txt`)
- UI Framework: PySide6
- DB: SQLite (local file)
- Display: 100%, 125%, 150% scale

---

## 4. Entry/Exit Criteria
- Entry:
  - App builds/starts without errors
  - Test data prepared (products, invoices, reminders)
- Exit:
  - 100% pass on P0/P1 test cases
  - No open Critical/High defects
  - Known Low defects documented with workaround

Severity/Priority:
- Sev 1 Critical: crash/data loss/security
- Sev 2 High: core flow blocked
- Sev 3 Medium: degraded UX or secondary flow
- Sev 4 Low: cosmetic/minor

---

## 5. Test Data
- Products: include items with `current_stock <= minimum_stock`
- Invoices: `status='pending'`, due within 7 days
- Reminders: `status='active'`, `reminder_time <= now()`

Minimal SQL seeds (SQLite):
```sql
-- Low stock product
INSERT INTO products(id,name,current_stock,minimum_stock,active) VALUES(1001,'منتج منخفض',2,5,1);

-- Pending invoice due in 3 days
INSERT INTO invoices(id,invoice_number,customer_name,total_amount,status,due_date)
VALUES(2001,'INV-2001','عميل تجريبي',1500.00,'pending',date('now','+3 day'));

-- Active reminder
INSERT INTO reminders(id,title,description,reminder_time,status)
VALUES(3001,'متابعة','اتصل بالعميل','now','active');
```

---

## 6. Detailed Test Cases

### 6.1 Theme System (ThemeManager)
- THEME-001 Apply saved theme on startup
  - Steps: Ensure settings `theme=dark`; start app
  - Expected: Dark stylesheet applied globally; no flicker/errors
- THEME-002 Toggle via Ctrl+T and View menu
  - Steps: Press `Ctrl+T` or menu "تغيير السمة"
  - Expected: Theme switches instantly; persists to QSettings
- THEME-003 Theme Selector dialog behavior
  - Steps: Open dialog; switch Light/Dark; Preview; Apply; Cancel
  - Expected: Preview is live; Apply persists; Cancel restores original
- THEME-004 Widgets coverage
  - Verify menus, tabs, tables, inputs, buttons, scrollbars, tooltips styled
- THEME-005 RTL & Arabic rendering
  - Expected: Proper alignment, no clipping; readable contrast
- THEME-006 Persistence across restarts
  - Restart app; last selected theme loads
- THEME-007 Performance
  - Theme switch completes < 200 ms perceptually; no UI freeze
- THEME-008 No functional regression
  - Buttons/menus remain clickable and legible after theme switching

### 6.2 Keyboard Shortcuts (Shortcuts Manager)
- KBD-001 Register core shortcuts
  - `Ctrl+B`,`Ctrl+T`,`Ctrl+K`,`F5`,`F11` register without conflicts
- KBD-002 Trigger handlers
  - Backup, Theme Selector, Shortcuts dialog, Refresh, Fullscreen fire handlers
- KBD-003 Help dialog content
  - Opens via `Ctrl+K`; shows all shortcuts (key, description, category)
- KBD-004 Persistence
  - Customization persists in QSettings (if UI provided/when updated programmatically)
- KBD-005 Disabled state
  - When an action is unavailable, shortcut should not raise errors
- KBD-006 RTL navigation
  - Focus movement with keyboard (Tab/Shift+Tab) remains correct
- KBD-007 No crash on rapid inputs
  - Hammer random valid shortcuts quickly; app remains stable

### 6.3 Smart Notifications
- NOTIF-001 Checker starts/stops
  - Manager starts background thread; can stop gracefully
- NOTIF-002 Low stock detection
  - With seed data: Low stock notifications appear; correct count/title/message
- NOTIF-003 Payment due detection
  - Pending due within 7 days surfaces as notifications
- NOTIF-004 Reminders detection
  - Active reminders at/older than now appear
- NOTIF-005 System Tray integration
  - Tray icon visible; double-click opens Notification Center; showMessage popups
- NOTIF-006 Notification Center
  - Shows list sorted by priority/time; supports mark read/dismiss; refresh
- NOTIF-007 Unread counter & persistence
  - Unread count updates; notifications saved (<=100) and restored after restart
- NOTIF-008 Error handling
  - Simulate DB unavailability: checker logs error but UI remains responsive
- NOTIF-009 Performance
  - Single check finishes < 500 ms with typical dataset; no UI blocking

### 6.4 Regression (Critical Flows)
- REG-001 App startup shows main window without errors
- REG-002 Inventory tab loads; search/filter works
- REG-003 Create sale/quote/return windows open
- REG-004 Reports window opens and renders
- REG-005 Backup/Restore dialogs open; no unintended interaction with themes
- REG-006 Printing dialog opens (smoke)
- REG-007 Advanced search window opens (if present)

### 6.5 Non-Functional
- PERF-001 Startup time acceptable (< 3s on reference PC)
- PERF-002 Memory delta after theme toggle < +10MB sustained
- A11Y-001 Keyboard-only navigation possible in main views
- A11Y-002 Contrast meets WCAG AA in both themes for primary text
- I18N-001 Arabic RTL layout consistent; truncation-free in common dialogs
- SEC-001 QSettings do not store sensitive data; no PII in tray popups
- BKUP-001 Backup process unaffected by stylesheet/shortcuts

---

## 7. Traceability Matrix (excerpt)
| Requirement | Area | Test IDs |
|---|---|---|
| Theme persistence and toggle | ThemeManager | THEME-001/002/006 |
| Widgets styled and RTL | ThemeManager | THEME-004/005 |
| Shortcuts registration & help | Shortcuts | KBD-001/003 |
| Notifications auto-checks | Notifications | NOTIF-002/003/004 |
| Tray + Center + persistence | Notifications | NOTIF-005/006/007 |
| App critical startup | Core | REG-001 |

---

## 8. Execution & Commands
- Prepare venv and run tests:
```powershell
# Activate venv (example)
& .\.venv\Scripts\Activate.ps1

# Install test deps if needed
pip install -r requirements-test.txt

# Run pytest (if tests exist)
pytest -q
```

- Manual run checklist per section above (6.x). Record Pass/Fail, notes, screenshots if needed.

---

## 9. Reporting & Metrics
- Daily test progress: executed/blocked/passed/failed
- Defect metrics: count by severity, open vs closed, mean time to fix
- Exit report: summary of outstanding risks & mitigations

---

## 10. Risks & Mitigations
- Risk: Background thread exceptions → Mitigation: try/except, log safely
- Risk: Styling gaps in niche widgets → Mitigation: exploratory UI pass and quick patches
- Risk: Shortcut conflicts in OS/IME → Mitigation: allow customization and document alternatives

---

## 11. Sign-off
- QA Lead:
- Dev Lead:
- Date:
