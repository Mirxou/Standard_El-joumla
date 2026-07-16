"""
نماذج التكاملات الخارجية (Webhooks & Integrations)
"""

try:
    from pydantic import BaseModel
except ImportError:
    # Fallback إذا لم يكن pydantic متاحاً
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)


class AccountingWebhookPayload(BaseModel):
    invoice_id: int
    amount: float
    customer: str
    date: str


class PaymentWebhookPayload(BaseModel):
    order_id: int
    status: str
    amount: float
    payment_method: str


class SMSNotificationPayload(BaseModel):
    to: str
    message: str
