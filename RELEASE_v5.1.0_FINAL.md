# RELEASE v5.1.0 — UX Polish

Date: 2025-11-21

## Highlights
- Performance tab in main window with live metrics and quick access to full dashboard.
- Status bar indicators for theme and unread notifications with last-check tooltip.
- Unified Notifications Center with "Check Now" and quick link to notification settings.
- Configurable notifications interval (1–30 minutes) stored via QSettings.
- Keyboard shortcut for Performance Dashboard (Ctrl+Shift+P) and menu cleanup.
- Optional Quick Action for Performance Dashboard in the customizable toolbar.
- Basic unit tests for theme persistence and notifications settings.

## Details
- Main Window
  - Added lightweight Performance tab: theme status, unread count, DB/uptime indicators, and a button to open the full Performance Dashboard.
  - Status bar live metrics auto-refresh every few seconds; hover shows last notifications check time.
  - Menus cleaned and unified; added shortcuts: theme toggle (Ctrl+T), notifications (Ctrl+Shift+N), performance dashboard (Ctrl+Shift+P).
- Notifications
  - Background checker emits a post-scan signal; manager tracks last check timestamp and exposes string accessor.
  - Settings exposes notifications interval (QComboBox 1/2/5/10/15/30 minutes). Changes persist to QSettings and restart the checker.
  - Notifications Center adds: "⚙️ إعدادات الإشعارات" to jump to Settings and "⟳ افحص الآن" to trigger an immediate scan.
- Quick Actions Toolbar
  - Added optional Performance action to launch the Performance Dashboard (disabled by default; can be enabled in Customize).
- Tests & Docs
  - Unit tests: theme toggle persistence and notifications interval persistence via QSettings.
  - UX smoke tests guide updated for new flows.

## Upgrade Notes
- New QSettings keys:
  - `theme` — current theme (light/dark)
  - `notifications/interval_seconds` — background checker interval
  - `notifications` — persisted notifications list (JSON)
  - `quick_actions/enabled` — enabled quick actions list
- No database migrations in this release.

## How to Use
- Performance tab appears in the main window; use the button to open the full dashboard.
- Open Notification Center from the menu or shortcut (Ctrl+Shift+N); use "Check Now" for immediate scan or click settings link to adjust interval.
- Enable the Performance quick action from the toolbar customization dialog if desired.

## Verification
- See `UX_SMOKE_TESTS.md` for manual verification steps.
- Run unit tests:
  - `pytest -q`

## Credits
- UX improvements prioritized and implemented per v5.x roadmap.
