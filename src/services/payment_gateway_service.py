#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Payment Gateway Service - خدمة بوابات الدفع
تكامل مع Stripe, PayPal, وغيرها
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass
from pathlib import Path
import sys


from src.core.database_manager import DatabaseManager
from src.core.tenant_isolation import TenantIsolationManager

logger = logging.getLogger(__name__)


@dataclass
class PaymentGatewayTransaction:
    """معاملة Payment Gateway"""
    id: Optional[int] = None
    integration_id: int = 0
    transaction_id: str = ""
    transaction_type: str = "CHARGE"  # CHARGE, REFUND, VOID
    amount: Decimal = Decimal('0.00')
    currency: str = "DZD"
    status: str = "PENDING"  # PENDING, SUCCESS, FAILED, CANCELLED
    gateway_status: Optional[str] = None
    payment_id: Optional[int] = None
    sale_id: Optional[int] = None
    customer_id: Optional[int] = None
    gateway_response: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaymentGatewayService:
    """خدمة بوابات الدفع"""
    
    def __init__(self, db_manager: DatabaseManager, logger_instance: Optional[logging.Logger] = None):
        """
        تهيئة خدمة Payment Gateway
        
        Args:
            db_manager: مدير قاعدة البيانات
            logger_instance: Logger (اختياري)
        """
        self.db_manager = db_manager
        self.logger = logger_instance or logger
        self.tenant_isolation = TenantIsolationManager(db_manager) if db_manager else None
    
    def charge(self, integration_id: int, amount: Decimal, currency: str,
              payment_id: Optional[int] = None, sale_id: Optional[int] = None,
              customer_id: Optional[int] = None,
              metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        تنفيذ عملية دفع
        
        Args:
            integration_id: معرف التكامل
            amount: المبلغ
            currency: العملة
            payment_id: معرف الدفعة (اختياري)
            sale_id: معرف فاتورة المبيعات (اختياري)
            customer_id: معرف العميل (اختياري)
            metadata: بيانات إضافية (اختياري)
            
        Returns:
            Tuple[bool, Optional[str], Optional[Dict[str, Any]]]: (نجح/فشل, transaction_id, response)
        """
        try:
            # الحصول على معلومات التكامل
            integration = self._get_integration(integration_id)
            if not integration:
                return False, None, {"error": "التكامل غير موجود"}
            
            if not integration.get("is_active"):
                return False, None, {"error": "التكامل غير نشط"}
            
            provider = integration.get("provider", "").upper()
            
            # تنفيذ الدفع حسب المزود
            if provider == "STRIPE":
                return self._charge_stripe(integration, amount, currency, payment_id, sale_id, customer_id, metadata)
            elif provider == "PAYPAL":
                return self._charge_paypal(integration, amount, currency, payment_id, sale_id, customer_id, metadata)
            else:
                return False, None, {"error": f"المزود غير مدعوم: {provider}"}
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في تنفيذ الدفع: {e}", exc_info=True)
            return False, None, {"error": str(e)}
    
    def _charge_stripe(self, integration: Dict[str, Any], amount: Decimal,
                      currency: str, payment_id: Optional[int],
                      sale_id: Optional[int], customer_id: Optional[int],
                      metadata: Optional[Dict[str, Any]]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """تنفيذ دفع عبر Stripe"""
        try:
            import stripe
            
            api_key = integration.get("api_key")
            if not api_key:
                return False, None, {"error": "API Key غير موجود"}
            
            # تهيئة Stripe
            stripe.api_key = api_key
            
            # إنشاء Payment Intent
            intent_data = {
                "amount": int(amount * 100),  # Stripe يستخدم السنتات
                "currency": currency.lower(),
            }
            
            if metadata:
                intent_data["metadata"] = metadata
            
            if customer_id:
                intent_data["metadata"] = intent_data.get("metadata", {})
                intent_data["metadata"]["customer_id"] = str(customer_id)
            
            payment_intent = stripe.PaymentIntent.create(**intent_data)
            
            transaction_id = payment_intent.id
            status = "SUCCESS" if payment_intent.status == "succeeded" else "PENDING"
            
            # حفظ المعاملة
            self._save_transaction(
                integration_id=integration["id"],
                transaction_id=transaction_id,
                transaction_type="CHARGE",
                amount=amount,
                currency=currency,
                status=status,
                gateway_status=payment_intent.status,
                payment_id=payment_id,
                sale_id=sale_id,
                customer_id=customer_id,
                gateway_response=json.dumps(payment_intent.to_dict(), ensure_ascii=False)
            )
            
            return True, transaction_id, payment_intent.to_dict()
            
        except ImportError:
            return False, None, {"error": "مكتبة Stripe غير مثبتة"}
        except Exception as e:
            self.logger.error(f"❌ خطأ في Stripe: {e}", exc_info=True)
            return False, None, {"error": str(e)}
    
    def _charge_paypal(self, integration: Dict[str, Any], amount: Decimal,
                      currency: str, payment_id: Optional[int],
                      sale_id: Optional[int], customer_id: Optional[int],
                      metadata: Optional[Dict[str, Any]]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """تنفيذ دفع عبر PayPal"""
        try:
            # استخدام PayPal REST API
            import requests
            
            api_key = integration.get("api_key")
            api_secret = integration.get("api_secret")
            api_url = integration.get("api_url", "https://api.sandbox.paypal.com")
            
            if not api_key or not api_secret:
                return False, None, {"error": "API Credentials غير موجودة"}
            
            # الحصول على Access Token
            token_response = requests.post(
                f"{api_url}/v1/oauth2/token",
                auth=(api_key, api_secret),
                data={"grant_type": "client_credentials"},
                headers={"Accept": "application/json", "Accept-Language": "en_US"}
            )
            
            if token_response.status_code != 200:
                return False, None, {"error": "فشل الحصول على Access Token"}
            
            access_token = token_response.json()["access_token"]
            
            # إنشاء Order
            order_data = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {
                        "currency_code": currency,
                        "value": str(amount)
                    }
                }]
            }
            
            order_response = requests.post(
                f"{api_url}/v2/checkout/orders",
                json=order_data,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
            )
            
            if order_response.status_code != 201:
                return False, None, {"error": "فشل إنشاء Order"}
            
            order = order_response.json()
            transaction_id = order["id"]
            
            # حفظ المعاملة
            self._save_transaction(
                integration_id=integration["id"],
                transaction_id=transaction_id,
                transaction_type="CHARGE",
                amount=amount,
                currency=currency,
                status="PENDING",
                gateway_status=order.get("status"),
                payment_id=payment_id,
                sale_id=sale_id,
                customer_id=customer_id,
                gateway_response=json.dumps(order, ensure_ascii=False)
            )
            
            return True, transaction_id, order
            
        except ImportError:
            return False, None, {"error": "مكتبة requests غير مثبتة"}
        except Exception as e:
            self.logger.error(f"❌ خطأ في PayPal: {e}", exc_info=True)
            return False, None, {"error": str(e)}
    
    def refund(self, transaction_id: str, amount: Optional[Decimal] = None) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        استرداد مبلغ
        
        Args:
            transaction_id: معرف المعاملة الأصلية
            amount: المبلغ المراد استرداده (None = استرداد كامل)
            
        Returns:
            Tuple[bool, Optional[str], Optional[Dict[str, Any]]]: (نجح/فشل, refund_id, response)
        """
        try:
            # الحصول على المعاملة الأصلية
            transaction = self._get_transaction_by_id(transaction_id)
            if not transaction:
                return False, None, {"error": "المعاملة غير موجودة"}
            
            integration = self._get_integration(transaction["integration_id"])
            if not integration:
                return False, None, {"error": "التكامل غير موجود"}
            
            provider = integration.get("provider", "").upper()
            
            if provider == "STRIPE":
                return self._refund_stripe(integration, transaction_id, amount)
            elif provider == "PAYPAL":
                return self._refund_paypal(integration, transaction_id, amount)
            else:
                return False, None, {"error": f"المزود غير مدعوم: {provider}"}
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في الاسترداد: {e}", exc_info=True)
            return False, None, {"error": str(e)}
    
    def _refund_stripe(self, integration: Dict[str, Any], transaction_id: str,
                      amount: Optional[Decimal]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """استرداد عبر Stripe"""
        try:
            import stripe
            
            stripe.api_key = integration.get("api_key")
            
            refund_data = {"payment_intent": transaction_id}
            if amount:
                refund_data["amount"] = int(amount * 100)
            
            refund = stripe.Refund.create(**refund_data)
            
            return True, refund.id, refund.to_dict()
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في Stripe Refund: {e}", exc_info=True)
            return False, None, {"error": str(e)}
    
    def _refund_paypal(self, integration: Dict[str, Any], transaction_id: str,
                      amount: Optional[Decimal]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """استرداد عبر PayPal"""
        # PayPal Refund implementation
        return False, None, {"error": "PayPal Refund غير مدعوم حالياً"}
    
    def _get_integration(self, integration_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على معلومات التكامل"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = """
                SELECT * FROM integrations
                WHERE id = ? AND integration_type = 'PAYMENT_GATEWAY'
            """
            params = [integration_id]
            
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)
            
            row = self.db_manager.fetch_one(query, tuple(params))
            return dict(row) if row else None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على التكامل: {e}", exc_info=True)
            return None
    
    def _get_transaction_by_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على معاملة بواسطة transaction_id"""
        try:
            query = """
                SELECT * FROM payment_gateway_transactions
                WHERE transaction_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """
            
            row = self.db_manager.fetch_one(query, (transaction_id,))
            return dict(row) if row else None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على المعاملة: {e}", exc_info=True)
            return None
    
    def _save_transaction(self, integration_id: int, transaction_id: str,
                         transaction_type: str, amount: Decimal, currency: str,
                         status: str, gateway_status: Optional[str] = None,
                         payment_id: Optional[int] = None,
                         sale_id: Optional[int] = None,
                         customer_id: Optional[int] = None,
                         gateway_response: Optional[str] = None,
                         error_message: Optional[str] = None):
        """حفظ معاملة"""
        try:
            query = """
                INSERT INTO payment_gateway_transactions (
                    integration_id, transaction_id, transaction_type,
                    amount, currency, status, gateway_status,
                    payment_id, sale_id, customer_id,
                    gateway_response, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            values = (
                integration_id, transaction_id, transaction_type,
                float(amount), currency, status, gateway_status,
                payment_id, sale_id, customer_id,
                gateway_response, error_message
            )
            
            self.db_manager.execute_query(query, values)
            self.logger.info(f"✅ تم حفظ معاملة: {transaction_id}")
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في حفظ المعاملة: {e}", exc_info=True)

