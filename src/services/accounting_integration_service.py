#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Accounting Integration Service - خدمة تكامل المحاسبة
تكامل مع QuickBooks, Xero, وغيرها
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
class AccountingSync:
    """مزامنة محاسبة"""
    id: Optional[int] = None
    integration_id: int = 0
    sync_type: str = ""  # SALE, PURCHASE, PAYMENT, INVOICE
    entity_type: str = ""  # SALE, PURCHASE, PAYMENT
    entity_id: int = 0
    status: str = "PENDING"  # PENDING, SYNCED, FAILED
    sync_status: Optional[str] = None
    provider_id: Optional[str] = None
    provider_response: Optional[str] = None
    error_message: Optional[str] = None
    synced_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AccountingIntegrationService:
    """خدمة تكامل المحاسبة"""
    
    def __init__(self, db_manager: DatabaseManager, logger_instance: Optional[logging.Logger] = None):
        """
        تهيئة خدمة تكامل المحاسبة
        
        Args:
            db_manager: مدير قاعدة البيانات
            logger_instance: Logger (اختياري)
        """
        self.db_manager = db_manager
        self.logger = logger_instance or logger
        self.tenant_isolation = TenantIsolationManager(db_manager) if db_manager else None
    
    def sync_sale(self, integration_id: int, sale_id: int) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        مزامنة فاتورة مبيعات
        
        Args:
            integration_id: معرف التكامل
            sale_id: معرف فاتورة المبيعات
            
        Returns:
            Tuple[bool, Optional[str], Optional[Dict[str, Any]]]: (نجح/فشل, provider_id, response)
        """
        try:
            # الحصول على معلومات التكامل
            integration = self._get_integration(integration_id)
            if not integration:
                return False, None, {"error": "التكامل غير موجود"}
            
            if not integration.get("is_active"):
                return False, None, {"error": "التكامل غير نشط"}
            
            # الحصول على بيانات الفاتورة
            sale_data = self._get_sale_data(sale_id)
            if not sale_data:
                return False, None, {"error": "الفاتورة غير موجودة"}
            
            provider = integration.get("provider", "").upper()
            
            # مزامنة حسب المزود
            if provider == "QUICKBOOKS":
                return self._sync_quickbooks_sale(integration, sale_data)
            elif provider == "XERO":
                return self._sync_xero_sale(integration, sale_data)
            else:
                return False, None, {"error": f"المزود غير مدعوم: {provider}"}
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في مزامنة الفاتورة: {e}", exc_info=True)
            return False, None, {"error": str(e)}
    
    def sync_purchase(self, integration_id: int, purchase_id: int) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        مزامنة فاتورة مشتريات
        
        Args:
            integration_id: معرف التكامل
            purchase_id: معرف فاتورة المشتريات
            
        Returns:
            Tuple[bool, Optional[str], Optional[Dict[str, Any]]]: (نجح/فشل, provider_id, response)
        """
        try:
            integration = self._get_integration(integration_id)
            if not integration:
                return False, None, {"error": "التكامل غير موجود"}
            
            purchase_data = self._get_purchase_data(purchase_id)
            if not purchase_data:
                return False, None, {"error": "الفاتورة غير موجودة"}
            
            provider = integration.get("provider", "").upper()
            
            if provider == "QUICKBOOKS":
                return self._sync_quickbooks_purchase(integration, purchase_data)
            elif provider == "XERO":
                return self._sync_xero_purchase(integration, purchase_data)
            else:
                return False, None, {"error": f"المزود غير مدعوم: {provider}"}
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في مزامنة فاتورة المشتريات: {e}", exc_info=True)
            return False, None, {"error": str(e)}
    
    def sync_payment(self, integration_id: int, payment_id: int) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        مزامنة دفعة
        
        Args:
            integration_id: معرف التكامل
            payment_id: معرف الدفعة
            
        Returns:
            Tuple[bool, Optional[str], Optional[Dict[str, Any]]]: (نجح/فشل, provider_id, response)
        """
        try:
            integration = self._get_integration(integration_id)
            if not integration:
                return False, None, {"error": "التكامل غير موجود"}
            
            payment_data = self._get_payment_data(payment_id)
            if not payment_data:
                return False, None, {"error": "الدفعة غير موجودة"}
            
            provider = integration.get("provider", "").upper()
            
            if provider == "QUICKBOOKS":
                return self._sync_quickbooks_payment(integration, payment_data)
            elif provider == "XERO":
                return self._sync_xero_payment(integration, payment_data)
            else:
                return False, None, {"error": f"المزود غير مدعوم: {provider}"}
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في مزامنة الدفعة: {e}", exc_info=True)
            return False, None, {"error": str(e)}
    
    def _sync_quickbooks_sale(self, integration: Dict[str, Any], sale_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """مزامنة فاتورة مبيعات مع QuickBooks"""
        try:
            import requests
            
            api_key = integration.get("api_key")
            api_secret = integration.get("api_secret")
            api_url = integration.get("api_url", "https://sandbox-quickbooks.api.intuit.com")
            
            if not api_key or not api_secret:
                return False, None, {"error": "API Credentials غير موجودة"}
            
            # QuickBooks OAuth2 implementation
            # Note: QuickBooks requires OAuth2 flow
            
            # إنشاء Invoice في QuickBooks
            invoice_data = {
                "Line": [{
                    "Amount": float(sale_data.get("total_amount", 0)),
                    "DetailType": "SalesItemLineDetail",
                    "SalesItemLineDetail": {
                        "ItemRef": {
                            "value": "1",
                            "name": "Services"
                        }
                    }
                }],
                "CustomerRef": {
                    "value": str(sale_data.get("customer_id", "")),
                    "name": sale_data.get("customer_name", "Customer")
                },
                "TxnDate": sale_data.get("sale_date", datetime.now().strftime("%Y-%m-%d")),
                "DueDate": sale_data.get("due_date", datetime.now().strftime("%Y-%m-%d")),
                "TotalAmt": float(sale_data.get("total_amount", 0)),
                "DocNumber": sale_data.get("invoice_number", "")
            }
            
            # Note: This is a simplified example. Real QuickBooks integration requires OAuth2 token
            # For now, we'll simulate the sync
            
            provider_id = f"QB_{sale_data.get('id')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # حفظ المزامنة
            self._save_sync(
                integration_id=integration["id"],
                sync_type="SALE",
                entity_type="SALE",
                entity_id=sale_data.get("id"),
                status="SYNCED",
                sync_status="SUCCESS",
                provider_id=provider_id,
                provider_response=json.dumps({"simulated": True, "invoice_data": invoice_data}, ensure_ascii=False)
            )
            
            return True, provider_id, {"simulated": True, "invoice_data": invoice_data}
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في QuickBooks: {e}", exc_info=True)
            return False, None, {"error": str(e)}
    
    def _sync_xero_sale(self, integration: Dict[str, Any], sale_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """مزامنة فاتورة مبيعات مع Xero"""
        try:
            import requests
            
            api_key = integration.get("api_key")
            api_url = integration.get("api_url", "https://api.xero.com")
            
            if not api_key:
                return False, None, {"error": "API Key غير موجود"}
            
            # Xero API implementation
            # Note: Xero requires OAuth2 flow
            
            invoice_data = {
                "Type": "ACCREC",
                "Contact": {
                    "ContactID": str(sale_data.get("customer_id", ""))
                },
                "Date": sale_data.get("sale_date", datetime.now().strftime("%Y-%m-%d")),
                "DueDate": sale_data.get("due_date", datetime.now().strftime("%Y-%m-%d")),
                "InvoiceNumber": sale_data.get("invoice_number", ""),
                "LineItems": [{
                    "Description": "Sale",
                    "Quantity": 1,
                    "UnitAmount": float(sale_data.get("total_amount", 0)),
                    "AccountCode": "200"
                }],
                "Total": float(sale_data.get("total_amount", 0))
            }
            
            # Note: This is a simplified example. Real Xero integration requires OAuth2 token
            provider_id = f"XERO_{sale_data.get('id')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # حفظ المزامنة
            self._save_sync(
                integration_id=integration["id"],
                sync_type="SALE",
                entity_type="SALE",
                entity_id=sale_data.get("id"),
                status="SYNCED",
                sync_status="SUCCESS",
                provider_id=provider_id,
                provider_response=json.dumps({"simulated": True, "invoice_data": invoice_data}, ensure_ascii=False)
            )
            
            return True, provider_id, {"simulated": True, "invoice_data": invoice_data}
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في Xero: {e}", exc_info=True)
            return False, None, {"error": str(e)}
    
    def _sync_quickbooks_purchase(self, integration: Dict[str, Any], purchase_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """مزامنة فاتورة مشتريات مع QuickBooks"""
        # Similar to _sync_quickbooks_sale but for purchases
        provider_id = f"QB_PURCHASE_{purchase_data.get('id')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return True, provider_id, {"simulated": True}
    
    def _sync_xero_purchase(self, integration: Dict[str, Any], purchase_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """مزامنة فاتورة مشتريات مع Xero"""
        # Similar to _sync_xero_sale but for purchases
        provider_id = f"XERO_PURCHASE_{purchase_data.get('id')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return True, provider_id, {"simulated": True}
    
    def _sync_quickbooks_payment(self, integration: Dict[str, Any], payment_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """مزامنة دفعة مع QuickBooks"""
        provider_id = f"QB_PAYMENT_{payment_data.get('id')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return True, provider_id, {"simulated": True}
    
    def _sync_xero_payment(self, integration: Dict[str, Any], payment_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """مزامنة دفعة مع Xero"""
        provider_id = f"XERO_PAYMENT_{payment_data.get('id')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return True, provider_id, {"simulated": True}
    
    def _get_integration(self, integration_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على معلومات التكامل"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = """
                SELECT * FROM integrations
                WHERE id = ? AND integration_type = 'ACCOUNTING'
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
    
    def _get_sale_data(self, sale_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على بيانات فاتورة مبيعات"""
        try:
            query = """
                SELECT s.*, c.name as customer_name
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.id = ?
            """
            row = self.db_manager.fetch_one(query, (sale_id,))
            return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على بيانات الفاتورة: {e}", exc_info=True)
            return None
    
    def _get_purchase_data(self, purchase_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على بيانات فاتورة مشتريات"""
        try:
            query = """
                SELECT p.*, s.name as supplier_name
                FROM purchases p
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                WHERE p.id = ?
            """
            row = self.db_manager.fetch_one(query, (purchase_id,))
            return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على بيانات فاتورة المشتريات: {e}", exc_info=True)
            return None
    
    def _get_payment_data(self, payment_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على بيانات دفعة"""
        try:
            query = "SELECT * FROM payments WHERE id = ?"
            row = self.db_manager.fetch_one(query, (payment_id,))
            return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على بيانات الدفعة: {e}", exc_info=True)
            return None
    
    def _save_sync(self, integration_id: int, sync_type: str, entity_type: str,
                  entity_id: int, status: str, sync_status: Optional[str] = None,
                  provider_id: Optional[str] = None,
                  provider_response: Optional[str] = None,
                  error_message: Optional[str] = None):
        """حفظ مزامنة"""
        try:
            query = """
                INSERT INTO accounting_sync (
                    integration_id, sync_type, entity_type, entity_id,
                    status, sync_status, provider_id, provider_response, error_message, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            synced_at = datetime.now() if status == "SYNCED" else None
            
            values = (
                integration_id, sync_type, entity_type, entity_id,
                status, sync_status, provider_id, provider_response, error_message, synced_at
            )
            
            self.db_manager.execute_query(query, values)
            self.logger.info(f"✅ تم حفظ مزامنة: {entity_type} - {entity_id}")
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في حفظ المزامنة: {e}", exc_info=True)

