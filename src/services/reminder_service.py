"""
خدمة التذكيرات
Reminder Service

تذكيرات الدفع والمتابعة وإرسالها عبر البريد تلقائياً.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from src.core.database_manager import DatabaseManager
from src.services.email_service import EmailService
from src.services.print_service import PrintService

logger = logging.getLogger(__name__)

PAYMENT_REMINDER_HTML = """
<html dir='rtl'>
  <body style='font-family: Arial; line-height:1.6'>
    <h3>تذكير بالدفع للفاتورة رقم {{ invoice_number }}</h3>
    <p>العميل: {{ customer_name }}</p>
    <p>الإجمالي: {{ total }} دج | المدفوع: {{ paid }} دج | المتبقي: <strong>{{ remaining }}</strong> دج</p>
    <p>يرجى تسديد المبلغ المتبقي قبل: {{ due_date }}.</p>
    <p style='color:#666;font-size:12px'>هذا تذكير آلي - لا ترد على هذه الرسالة.</p>
  </body>
</html>
"""

PAYMENT_REMINDER_TEXT = (
    "تذكير دفع للفاتورة رقم {{ invoice_number }}\n" \
    "الإجمالي: {{ total }} دج | المدفوع: {{ paid }} دج | المتبقي: {{ remaining }} دج\n" \
    "يرجى التسديد قبل: {{ due_date }}"
)

class ReminderService:
    def __init__(self, db_manager: DatabaseManager, email_service: EmailService):
        self.db = db_manager
        self.email = email_service
        self.print_service = PrintService()

    def schedule_payment_reminder(
        self,
        sale_id: int,
        due_at: datetime,
        recipient_email: Optional[str],
        created_by: Optional[int] = None,
        subject: Optional[str] = None,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """جدولة تذكير دفع لفاتورة معينة"""
        try:
            invoice = self.print_service._get_invoice_data(sale_id)
            if not invoice:
                return {"success": False, "error": "Invoice not found"}
            if not recipient_email:
                recipient_email = invoice.get('customer_email') or ''
            if not recipient_email:
                return {"success": False, "error": "Recipient email missing"}
            if subject is None:
                subject = f"تذكير دفع - فاتورة {invoice.get('invoice_number', sale_id)}"
            if message is None:
                message = f"المتبقي: {invoice.get('remaining')} دج - الرجاء السداد قبل {due_at.date()}"

            self.db.execute_query(
                """
                INSERT INTO reminders (sale_id, customer_id, reminder_type, subject, message, due_at, recipient_email, created_by)
                VALUES (?, ?, 'payment', ?, ?, ?, ?, ?)
                """,
                (
                    sale_id,
                    invoice.get('customer_id'),
                    subject,
                    message,
                    due_at.isoformat(timespec='seconds'),
                    recipient_email,
                    created_by
                )
            )
            reminder_id = self.db.get_last_insert_id()
            return {"success": True, "id": reminder_id}
        except Exception as e:
            logger.error(f"Failed to schedule payment reminder: {e}")
            return {"success": False, "error": str(e)}

    def list_pending(self, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            rows = self.db.execute_query(
                """
                SELECT * FROM reminders
                WHERE status = 'pending' AND due_at <= ?
                ORDER BY due_at ASC
                LIMIT ?
                """,
                (datetime.utcnow().isoformat(timespec='seconds'), limit)
            )
            return rows
        except Exception as e:
            logger.error(f"Failed to list pending reminders: {e}")
            return []

    def send_due_reminders(self, attach_invoice_pdf: bool = True) -> Dict[str, Any]:
        """إرسال جميع التذكيرات المستحقة حالياً"""
        pending = self.list_pending()
        sent, failed = 0, 0
        for r in pending:
            try:
                sale_id = r.get('sale_id')
                invoice = self.print_service._get_invoice_data(sale_id) if sale_id else None
                if not invoice:
                    raise RuntimeError('Invoice data missing')
                data = {
                    **invoice,
                    'due_date': r.get('due_at')[:10]
                }
                html_body = self.email.render_template(PAYMENT_REMINDER_HTML, data)
                text_body = self.email.render_template(PAYMENT_REMINDER_TEXT, data)
                attachments = []
                if attach_invoice_pdf:
                    pdf_res = self.print_service.print_invoice(sale_id=sale_id, save_pdf=True)
                    if pdf_res.get('success') and pdf_res.get('pdf_path'):
                        from pathlib import Path
                        p = Path(pdf_res['pdf_path'])
                        try:
                            content = p.read_bytes()
                            attachments.append({'filename': p.name, 'content': content, 'mime': 'application/pdf'})
                        except Exception:
                            pass
                send_res = self.email.send_email(
                    to=r.get('recipient_email'),
                    subject=r.get('subject'),
                    body_html=html_body,
                    body_text=text_body,
                    attachments=attachments
                )
                if send_res.get('success'):
                    self.db.execute_query(
                        "UPDATE reminders SET status='sent', attempts=attempts+1, last_attempt_at=CURRENT_TIMESTAMP WHERE id=?",
                        (r.get('id'),)
                    )
                    sent += 1
                else:
                    raise RuntimeError('Email send failed')
            except Exception as e:
                failed += 1
                logger.error(f"Reminder send failed: {e}")
                try:
                    self.db.execute_query(
                        "UPDATE reminders SET attempts=attempts+1, last_attempt_at=CURRENT_TIMESTAMP WHERE id=?",
                        (r.get('id'),)
                    )
                except Exception:
                    pass
        return {"success": True, "sent": sent, "failed": failed, "total": len(pending)}

    def cancel_reminder(self, reminder_id: int) -> bool:
        try:
            self.db.execute_query(
                "UPDATE reminders SET status='cancelled', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (reminder_id,)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to cancel reminder: {e}")
            return False

# Global accessor
_reminder_service_global: Optional[ReminderService] = None

def init_reminder_service(db: DatabaseManager, email: EmailService) -> ReminderService:
    global _reminder_service_global
    _reminder_service_global = ReminderService(db, email)
    return _reminder_service_global

def get_reminder_service() -> Optional[ReminderService]:
    return _reminder_service_global
