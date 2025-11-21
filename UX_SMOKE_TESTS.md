# UX Smoke Tests

Quick checks to verify core UX features work after changes.

- Launch App: Start the application via `python main.py`.
- Theme Toggle: Open `عرض → 🎨 تغيير السمة` and switch between Light/Dark. Verify global styles update.
- Shortcuts Help: Open `مساعدة → ⌨️ اختصارات لوحة المفاتيح`. Verify dialog opens and lists shortcuts.
- Notifications Center:
  - Open `عرض → 🔔 مركز الإشعارات` and verify dialog opens.
  - If seed data loaded, ensure notifications list renders.
  - Click `⟳ افحص الآن` to trigger an immediate scan, then verify list updates.
- Quick Actions Toolbar:
  - Confirm toolbar appears with default actions (فاتورة جديدة, نسخ احتياطي, منتج جديد, نقطة بيع, تقرير يومي, لوحة المعلومات, الإشعارات, تحديث).
  - Click ⚙️ تخصيص and toggle actions on/off; verify toolbar updates and persists.
  - Optionally enable “📊 مراقبة الأداء” and confirm it opens the dashboard.
- Performance Tab (New):
  - Switch to `⚡ الأداء` tab.
  - Verify values update every ~2s: current theme, unread notifications count, DB status, and uptime.
  - Click the button “📊 افتح لوحة مراقبة الأداء التفصيلية” and confirm the dashboard opens.
- Performance Dashboard (Window):
  - Open `أدوات → 📊 مراقبة الأداء` and verify live metrics.
- Status Bar: Verify DB status message shows when connected.

Notes:
- On first run without DB, notifications and some metrics may show placeholders.
- Use `tests/data/seed_notifications.sql` to populate representative notification data when applicable.
