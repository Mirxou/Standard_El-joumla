"""
نماذج التكاملات الخارجية (Webhooks & Integrations)
"""
from pydantic import BaseModel
from typing import Optional

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
