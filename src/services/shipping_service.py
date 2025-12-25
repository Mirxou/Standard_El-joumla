#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shipping Service - خدمة الشحن
تكامل مع FedEx, DHL, وغيرها
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal
from dataclasses import dataclass
from pathlib import Path
import sys

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.database_manager import DatabaseManager
from src.core.tenant_isolation import TenantIsolationManager

logger = logging.getLogger(__name__)


@dataclass
class ShippingShipment:
    """شحنة"""
    id: Optional[int] = None
    integration_id: int = 0
    shipment_id: str = ""
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    sale_id: Optional[int] = None
    customer_id: Optional[int] = None
    origin_address: Optional[str] = None
    destination_address: Optional[str] = None
    weight: Optional[Decimal] = None
    dimensions: Optional[str] = None
    status: str = "PENDING"  # PENDING, IN_TRANSIT, DELIVERED, CANCELLED
    shipping_status: Optional[str] = None
    shipping_cost: Optional[Decimal] = None
    currency: str = "DZD"
    provider_response: Optional[str] = None
    estimated_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ShippingService:
    """خدمة الشحن"""
    
    def __init__(self, db_manager: DatabaseManager, logger_instance: Optional[logging.Logger] = None):
        """
        تهيئة خدمة الشحن
        
        Args:
            db_manager: مدير قاعدة البيانات
            logger_instance: Logger (اختياري)
        """
        self.db_manager = db_manager
        self.logger = logger_instance or logger
        self.tenant_isolation = TenantIsolationManager(db_manager) if db_manager else None
    
    def create_shipment(self, integration_id: int, sale_id: int,
                       origin_address: str, destination_address: str,
                       weight: Decimal, dimensions: Optional[Dict[str, float]] = None,
                       customer_id: Optional[int] = None) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        إنشاء شحنة
        
        Args:
            integration_id: معرف التكامل
            sale_id: معرف فاتورة المبيعات
            origin_address: عنوان المنشأ
            destination_address: عنوان الوجهة
            weight: الوزن (كجم)
            dimensions: الأبعاد (اختياري)
            customer_id: معرف العميل (اختياري)
            
        Returns:
            Tuple[bool, Optional[str], Optional[Dict[str, Any]]]: (نجح/فشل, shipment_id, response)
        """
        try:
            # الحصول على معلومات التكامل
            integration = self._get_integration(integration_id)
            if not integration:
                return False, None, {"error": "التكامل غير موجود"}
            
            if not integration.get("is_active"):
                return False, None, {"error": "التكامل غير نشط"}
            
            provider = integration.get("provider", "").upper()
            
            # إنشاء الشحنة حسب المزود
            if provider == "FEDEX":
                return self._create_fedex_shipment(integration, sale_id, origin_address, destination_address, weight, dimensions, customer_id)
            elif provider == "DHL":
                return self._create_dhl_shipment(integration, sale_id, origin_address, destination_address, weight, dimensions, customer_id)
            else:
                return False, None, {"error": f"المزود غير مدعوم: {provider}"}
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في إنشاء الشحنة: {e}", exc_info=True)
            return False, None, {"error": str(e)}
    
    def _create_fedex_shipment(self, integration: Dict[str, Any], sale_id: int,
                               origin_address: str, destination_address: str,
                               weight: Decimal, dimensions: Optional[Dict[str, float]],
                               customer_id: Optional[int]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """إنشاء شحنة عبر FedEx"""
        try:
            import requests
            
            api_key = integration.get("api_key")
            api_secret = integration.get("api_secret")
            api_url = integration.get("api_url", "https://apis-sandbox.fedex.com")
            
            if not api_key or not api_secret:
                return False, None, {"error": "API Credentials غير موجودة"}
            
            # الحصول على Access Token
            token_response = requests.post(
                f"{api_url}/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": api_key,
                    "client_secret": api_secret
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if token_response.status_code != 200:
                return False, None, {"error": "فشل الحصول على Access Token"}
            
            access_token = token_response.json()["access_token"]
            
            # إنشاء Shipment
            shipment_data = {
                "labelResponseOptions": "URL_ONLY",
                "requestedShipment": {
                    "shipper": {
                        "contact": {
                            "personName": "Shipper Name",
                            "emailAddress": "shipper@example.com",
                            "phoneNumber": "1234567890"
                        },
                        "address": {
                            "streetLines": [origin_address],
                            "city": "City",
                            "stateOrProvinceCode": "ST",
                            "postalCode": "12345",
                            "countryCode": "DZ"
                        }
                    },
                    "recipients": [{
                        "contact": {
                            "personName": "Recipient Name",
                            "emailAddress": "recipient@example.com",
                            "phoneNumber": "1234567890"
                        },
                        "address": {
                            "streetLines": [destination_address],
                            "city": "City",
                            "stateOrProvinceCode": "ST",
                            "postalCode": "12345",
                            "countryCode": "DZ"
                        }
                    }],
                    "shipDatestamp": datetime.now().strftime("%Y-%m-%d"),
                    "serviceType": "STANDARD_OVERNIGHT",
                    "packagingType": "YOUR_PACKAGING",
                    "pickupType": "USE_SCHEDULED_PICKUP",
                    "blockInsightVisibility": False,
                    "shippingChargesPayment": {
                        "paymentType": "SENDER"
                    },
                    "labelSpecification": {
                        "imageType": "PDF",
                        "labelStockType": "PAPER_4X6"
                    },
                    "requestedPackageLineItems": [{
                        "weight": {
                            "units": "KG",
                            "value": float(weight)
                        }
                    }]
                }
            }
            
            if dimensions:
                shipment_data["requestedShipment"]["requestedPackageLineItems"][0]["dimensions"] = {
                    "length": dimensions.get("length", 10),
                    "width": dimensions.get("width", 10),
                    "height": dimensions.get("height", 10),
                    "units": "CM"
                }
            
            shipment_response = requests.post(
                f"{api_url}/ship/v1/shipments",
                json=shipment_data,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "X-locale": "en_US"
                }
            )
            
            if shipment_response.status_code not in [200, 201]:
                return False, None, {"error": f"فشل إنشاء الشحنة: {shipment_response.text}"}
            
            response_data = shipment_response.json()
            shipment_id = response_data.get("output", {}).get("transactionShipments", [{}])[0].get("masterTrackingNumber", "")
            
            if not shipment_id:
                shipment_id = f"FEDEX_{sale_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # حفظ الشحنة
            self._save_shipment(
                integration_id=integration["id"],
                shipment_id=shipment_id,
                tracking_number=shipment_id,
                carrier="FedEx",
                sale_id=sale_id,
                customer_id=customer_id,
                origin_address=origin_address,
                destination_address=destination_address,
                weight=weight,
                dimensions=json.dumps(dimensions, ensure_ascii=False) if dimensions else None,
                status="PENDING",
                shipping_status=response_data.get("output", {}).get("transactionShipments", [{}])[0].get("shipmentDocuments", [{}])[0].get("contentType", ""),
                provider_response=json.dumps(response_data, ensure_ascii=False)
            )
            
            return True, shipment_id, response_data
            
        except ImportError:
            return False, None, {"error": "مكتبة requests غير مثبتة"}
        except Exception as e:
            self.logger.error(f"❌ خطأ في FedEx: {e}", exc_info=True)
            return False, None, {"error": str(e)}
    
    def _create_dhl_shipment(self, integration: Dict[str, Any], sale_id: int,
                            origin_address: str, destination_address: str,
                            weight: Decimal, dimensions: Optional[Dict[str, float]],
                            customer_id: Optional[int]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """إنشاء شحنة عبر DHL"""
        try:
            import requests
            
            api_key = integration.get("api_key")
            api_url = integration.get("api_url", "https://api-sandbox.dhl.com")
            
            if not api_key:
                return False, None, {"error": "API Key غير موجود"}
            
            # DHL API implementation
            # Note: DHL API structure may vary
            shipment_data = {
                "plannedShippingDateAndTime": {
                    "shippingDate": datetime.now().strftime("%Y-%m-%d")
                },
                "pickup": {
                    "isRequested": False
                },
                "productCode": "P",
                "accounts": [{
                    "number": api_key
                }],
                "content": {
                    "packages": [{
                        "weight": float(weight),
                        "dimensions": {
                            "length": dimensions.get("length", 10) if dimensions else 10,
                            "width": dimensions.get("width", 10) if dimensions else 10,
                            "height": dimensions.get("height", 10) if dimensions else 10
                        }
                    }]
                },
                "outputImageProperties": {
                    "allImagesInOnePdf": True,
                    "encodingFormat": "pdf",
                    "imageOptions": [{
                        "typeCode": "label"
                    }]
                }
            }
            
            shipment_response = requests.post(
                f"{api_url}/shipment",
                json=shipment_data,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if shipment_response.status_code not in [200, 201]:
                return False, None, {"error": f"فشل إنشاء الشحنة: {shipment_response.text}"}
            
            response_data = shipment_response.json()
            shipment_id = response_data.get("shipmentTrackingNumber", f"DHL_{sale_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}")
            
            # حفظ الشحنة
            self._save_shipment(
                integration_id=integration["id"],
                shipment_id=shipment_id,
                tracking_number=shipment_id,
                carrier="DHL",
                sale_id=sale_id,
                customer_id=customer_id,
                origin_address=origin_address,
                destination_address=destination_address,
                weight=weight,
                dimensions=json.dumps(dimensions, ensure_ascii=False) if dimensions else None,
                status="PENDING",
                shipping_status=response_data.get("status", {}).get("statusCode", ""),
                provider_response=json.dumps(response_data, ensure_ascii=False)
            )
            
            return True, shipment_id, response_data
            
        except ImportError:
            return False, None, {"error": "مكتبة requests غير مثبتة"}
        except Exception as e:
            self.logger.error(f"❌ خطأ في DHL: {e}", exc_info=True)
            return False, None, {"error": str(e)}
    
    def track_shipment(self, tracking_number: str, integration_id: int) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        تتبع شحنة
        
        Args:
            tracking_number: رقم التتبع
            integration_id: معرف التكامل
            
        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: (نجح/فشل, tracking_info)
        """
        try:
            integration = self._get_integration(integration_id)
            if not integration:
                return False, {"error": "التكامل غير موجود"}
            
            provider = integration.get("provider", "").upper()
            
            if provider == "FEDEX":
                return self._track_fedex(tracking_number, integration)
            elif provider == "DHL":
                return self._track_dhl(tracking_number, integration)
            else:
                return False, {"error": f"المزود غير مدعوم: {provider}"}
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في تتبع الشحنة: {e}", exc_info=True)
            return False, {"error": str(e)}
    
    def _track_fedex(self, tracking_number: str, integration: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """تتبع شحنة FedEx"""
        # FedEx Tracking implementation
        return False, {"error": "FedEx Tracking غير مدعوم حالياً"}
    
    def _track_dhl(self, tracking_number: str, integration: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """تتبع شحنة DHL"""
        # DHL Tracking implementation
        return False, {"error": "DHL Tracking غير مدعوم حالياً"}
    
    def _get_integration(self, integration_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على معلومات التكامل"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = """
                SELECT * FROM integrations
                WHERE id = ? AND integration_type = 'SHIPPING'
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
    
    def _save_shipment(self, integration_id: int, shipment_id: str,
                      tracking_number: Optional[str] = None,
                      carrier: Optional[str] = None,
                      sale_id: Optional[int] = None,
                      customer_id: Optional[int] = None,
                      origin_address: Optional[str] = None,
                      destination_address: Optional[str] = None,
                      weight: Optional[Decimal] = None,
                      dimensions: Optional[str] = None,
                      status: str = "PENDING",
                      shipping_status: Optional[str] = None,
                      shipping_cost: Optional[Decimal] = None,
                      currency: str = "DZD",
                      provider_response: Optional[str] = None):
        """حفظ شحنة"""
        try:
            query = """
                INSERT INTO shipping_shipments (
                    integration_id, shipment_id, tracking_number, carrier,
                    sale_id, customer_id, origin_address, destination_address,
                    weight, dimensions, status, shipping_status,
                    shipping_cost, currency, provider_response
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            values = (
                integration_id, shipment_id, tracking_number, carrier,
                sale_id, customer_id, origin_address, destination_address,
                float(weight) if weight else None, dimensions, status, shipping_status,
                float(shipping_cost) if shipping_cost else None, currency, provider_response
            )
            
            self.db_manager.execute_query(query, values)
            self.logger.info(f"✅ تم حفظ شحنة: {shipment_id}")
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في حفظ الشحنة: {e}", exc_info=True)

