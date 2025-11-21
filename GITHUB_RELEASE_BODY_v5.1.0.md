# v5.1.0 — UX Polish

This minor release focuses on everyday usability and visibility: a new Performance tab, live status indicators, and a more capable Notification Center with configurable intervals.

## Highlights
- Performance tab in the main window (live metrics + open full Dashboard).
- Status bar indicators for theme and unread notifications with last-check tooltip.
- Unified Notification Center with “Check Now” and a quick link to Notification Settings.
- Configurable notifications interval (1/2/5/10/15/30 minutes), persisted via QSettings.
- Menu cleanup and keyboard shortcuts: Ctrl+Shift+P (Performance), Ctrl+Shift+N (Notifications), Ctrl+T (Theme).
- Optional Quick Action to launch Performance Dashboard from the toolbar.

## Upgrade Notes
- New QSettings keys: `theme`, `notifications/interval_seconds`, `notifications`, `quick_actions/enabled`.
- No database migrations.

## Verification
- Follow `UX_SMOKE_TESTS.md` for manual checks.
- Targeted unit tests included for theme and notifications persistence.

## Thanks
- UX polish driven by v5.x roadmap priorities.
