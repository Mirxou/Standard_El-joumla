# 🚀 RELEASE v4.8.0 – Advanced Printing, Email, Notes & Reminders

Date: 2025-11-21  
Status: Production-Ready ✅  
Tests: 49/49 passing ✅

## Highlights
- 🖨️ Advanced Printing System with customizable HTML/CSS templates (Jinja2)
- 📄 PDF export with full Arabic support (WeasyPrint)
- ✉️ Email delivery (SMTP) with invoice PDF attachments
- 🗒️ Invoice Notes (internal/pinned/customer-visible)
- ⏰ Automatic Payment Reminders (with PDF), plus background scheduler

## What’s New

### Printing System
- `src/core/print_manager.py` (800+ lines)
  - TemplateType: INVOICE, QUOTE, RECEIPT, PURCHASE, REPORT
  - PaperSize: A4, A5, LETTER, THERMAL_80MM, THERMAL_58MM
  - Default templates: A4 Invoice, 80mm Thermal Receipt, A4 Quote
  - Jinja2 rendering, logging print jobs, DB tables + indexes

### PDF Export
- `src/services/pdf_export_service.py`
  - WeasyPrint-first; wkhtmltopdf fallback
  - Custom margins, headers/footers, multi-size support

### Integrated Printing Service
- `src/services/print_service.py`
  - print_invoice/print_quote/print_thermal_receipt
  - batch_print_invoices
  - Auto data fetch + job logging

### Email Service (SMTP)
- `src/services/email_service.py`
  - send_email: HTML/text, CC/BCC, attachments
  - send_invoice_email: generate and attach invoice PDF automatically
  - send_alert / send_report (optional PDF)

### Notes & Reminders
- DB tables: `invoice_notes`, `reminders` + indexes
- `src/services/notes_service.py` (add/list/pin/delete)
- `src/services/reminder_service.py` (schedule/list/send/cancel)
  - Payment reminder templates (HTML/Text) with PDF attachments
- `src/services/scheduler_service.py` (threaded background)
  - Controlled by env: `SCHEDULER_ENABLED`, `SCHEDULER_INTERVAL_SECONDS`
- App integration (optional): `main.py` initializes Email/Reminders/Scheduler if enabled

## Environment
```bash
# SMTP
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=no-reply@example.com
SMTP_PASSWORD=APP_PASSWORD
SMTP_TLS=true
SMTP_FROM=no-reply@example.com

# Reminders Scheduler
SCHEDULER_ENABLED=true
SCHEDULER_INTERVAL_SECONDS=300
```

## Dependencies
- requirements.txt updated:
  - `jinja2>=3.1.0`
  - `weasyprint>=60.0`

## Database
- New tables created automatically by DatabaseManager:
  - `print_templates`, `print_jobs`
  - `invoice_notes`, `reminders`
  - Proper indexes for performance

## Docs
- `PRINTING_v4.8.0_REPORT.md` – Full printing guide
- `NOTES_REMINDERS_v4.8.0_REPORT.md` – Notes/reminders guide

## App Integration
- `main.py`: optional initialization of EmailService, ReminderService, ReminderScheduler
  - Scheduler starts only if `SCHEDULER_ENABLED=true`

## Testing
- All existing suites pass: 49/49 ✅
- No regressions or API changes affecting tests

## Upgrade Notes
- Install new dependencies:
```powershell
pip install -r requirements.txt
```
- Configure SMTP variables for email and set scheduler envs as needed.

## Summary
v4.8.0 delivers professional-grade printing and automated communications, rounding out the ERP with end-to-end invoice lifecycle: create → print → email → remind. Production-ready with comprehensive tests and docs.
