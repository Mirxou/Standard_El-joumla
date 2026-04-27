#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EDI Service - خدمة EDI
إدارة مستندات EDI والشركاء والـ Mapping
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal
from dataclasses import dataclass, field
from pathlib import Path
import sys


from src.core.database_manager import DatabaseManager
from src.core.tenant_isolation import TenantIsolationManager
from src.core.edi_parser import EDIParser, EDIParseResult
from src.core.edi_generator import EDIGenerator, EDIGenerateResult

logger = logging.getLogger(__name__)


@dataclass
class EDIPartner:
    """شريك EDI"""
    id: Optional[int] = None
    name: str = ""
    partner_code: str = ""
    partner_type: str = "SUPPLIER"  # SUPPLIER, CUSTOMER, BOTH
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    edi_standard: str = "EDIFACT"  # EDIFACT, X12
    edi_version: str = "D96A"
    interchange_id: Optional[str] = None
    sender_id: Optional[str] = None
    receiver_id: Optional[str] = None
    supports_orders: bool = True
    supports_invoices: bool = True
    supports_acknowledgments: bool = True
    supports_asn: bool = False
    connection_type: str = "FILE"  # FILE, FTP, SFTP, AS2, API
    file_path: Optional[str] = None
    ftp_host: Optional[str] = None
    ftp_port: int = 21
    ftp_username: Optional[str] = None
    ftp_password: Optional[str] = None
    ftp_directory: Optional[str] = None
    encryption_method: Optional[str] = None
    signature_method: Optional[str] = None
    public_key: Optional[str] = None
    is_active: bool = True
    auto_process: bool = False
    company_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "name": self.name,
            "partner_code": self.partner_code,
            "partner_type": self.partner_type,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "edi_standard": self.edi_standard,
            "edi_version": self.edi_version,
            "interchange_id": self.interchange_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "supports_orders": self.supports_orders,
            "supports_invoices": self.supports_invoices,
            "supports_acknowledgments": self.supports_acknowledgments,
            "supports_asn": self.supports_asn,
            "connection_type": self.connection_type,
            "file_path": self.file_path,
            "ftp_host": self.ftp_host,
            "ftp_port": self.ftp_port,
            "ftp_username": self.ftp_username,
            "ftp_password": "***" if self.ftp_password else None,  # إخفاء كلمة المرور
            "ftp_directory": self.ftp_directory,
            "encryption_method": self.encryption_method,
            "signature_method": self.signature_method,
            "public_key": self.public_key,
            "is_active": self.is_active,
            "auto_process": self.auto_process,
            "company_id": self.company_id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EDIPartner':
        """إنشاء من قاموس"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class EDIDocument:
    """مستند EDI"""
    id: Optional[int] = None
    document_type: str = ""  # 850, 810, 855, etc.
    document_number: str = ""
    partner_id: int = 0
    status: str = "PENDING"  # PENDING, PROCESSED, ERROR, ACKNOWLEDGED
    direction: str = ""  # INBOUND, OUTBOUND
    raw_content: str = ""
    parsed_content: Optional[str] = None
    related_po_id: Optional[int] = None
    related_invoice_id: Optional[int] = None
    related_sale_id: Optional[int] = None
    sent_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    error_message: Optional[str] = None
    error_details: Optional[str] = None
    is_valid: bool = True
    validation_errors: Optional[str] = None
    company_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "document_type": self.document_type,
            "document_number": self.document_number,
            "partner_id": self.partner_id,
            "status": self.status,
            "direction": self.direction,
            "raw_content": self.raw_content[:500] if len(self.raw_content) > 500 else self.raw_content,  # تقليل الحجم
            "parsed_content": self.parsed_content,
            "related_po_id": self.related_po_id,
            "related_invoice_id": self.related_invoice_id,
            "related_sale_id": self.related_sale_id,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
            "company_id": self.company_id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EDIService:
    """خدمة EDI"""
    
    def __init__(self, db_manager: DatabaseManager, logger_instance: Optional[logging.Logger] = None):
        """
        تهيئة خدمة EDI
        
        Args:
            db_manager: مدير قاعدة البيانات
            logger_instance: Logger (اختياري)
        """
        self.db_manager = db_manager
        self.logger = logger_instance or logger
        self.tenant_isolation = TenantIsolationManager(db_manager) if db_manager else None
        
        # تهيئة المحلل والمولد
        self.parser = None  # سيتم تهيئته حسب المعيار
        self.generator = None  # سيتم تهيئته حسب المعيار
    
    # ============================================================================
    # إدارة الشركاء (EDI Partners)
    # ============================================================================
    
    def create_partner(self, partner: EDIPartner) -> Optional[int]:
        """إنشاء شريك EDI جديد"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = """
                INSERT INTO edi_partners (
                    name, partner_code, partner_type, contact_name, contact_email, contact_phone,
                    edi_standard, edi_version, interchange_id, sender_id, receiver_id,
                    supports_orders, supports_invoices, supports_acknowledgments, supports_asn,
                    connection_type, file_path, ftp_host, ftp_port, ftp_username, ftp_password, ftp_directory,
                    encryption_method, signature_method, public_key,
                    is_active, auto_process, company_id, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            values = (
                partner.name, partner.partner_code, partner.partner_type,
                partner.contact_name, partner.contact_email, partner.contact_phone,
                partner.edi_standard, partner.edi_version, partner.interchange_id,
                partner.sender_id, partner.receiver_id,
                1 if partner.supports_orders else 0,
                1 if partner.supports_invoices else 0,
                1 if partner.supports_acknowledgments else 0,
                1 if partner.supports_asn else 0,
                partner.connection_type, partner.file_path,
                partner.ftp_host, partner.ftp_port, partner.ftp_username, partner.ftp_password, partner.ftp_directory,
                partner.encryption_method, partner.signature_method, partner.public_key,
                1 if partner.is_active else 0,
                1 if partner.auto_process else 0,
                company_id,
                partner.created_by
            )
            
            result = self.db_manager.execute_query(query, values)
            if result:
                partner_id = result.lastrowid
                self.logger.info(f"✅ تم إنشاء شريك EDI: {partner.name} (ID: {partner_id})")
                return partner_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في إنشاء شريك EDI: {e}", exc_info=True)
            return None
    
    def get_partner(self, partner_id: int) -> Optional[EDIPartner]:
        """الحصول على شريك EDI"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = """
                SELECT * FROM edi_partners
                WHERE id = ? AND company_id = ?
            """
            
            row = self.db_manager.fetch_one(query, (partner_id, company_id))
            if row:
                return self._row_to_partner(row)
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على شريك EDI: {e}", exc_info=True)
            return None
    
    def get_all_partners(self, partner_type: Optional[str] = None) -> List[EDIPartner]:
        """الحصول على جميع الشركاء"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            if partner_type:
                query = """
                    SELECT * FROM edi_partners
                    WHERE company_id = ? AND partner_type = ?
                    ORDER BY name
                """
                rows = self.db_manager.fetch_all(query, (company_id, partner_type))
            else:
                query = """
                    SELECT * FROM edi_partners
                    WHERE company_id = ?
                    ORDER BY name
                """
                rows = self.db_manager.fetch_all(query, (company_id,))
            
            return [self._row_to_partner(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على الشركاء: {e}", exc_info=True)
            return []
    
    def update_partner(self, partner: EDIPartner) -> bool:
        """تحديث شريك EDI"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = """
                UPDATE edi_partners SET
                    name = ?, partner_code = ?, partner_type = ?,
                    contact_name = ?, contact_email = ?, contact_phone = ?,
                    edi_standard = ?, edi_version = ?, interchange_id = ?,
                    sender_id = ?, receiver_id = ?,
                    supports_orders = ?, supports_invoices = ?,
                    supports_acknowledgments = ?, supports_asn = ?,
                    connection_type = ?, file_path = ?,
                    ftp_host = ?, ftp_port = ?, ftp_username = ?, ftp_password = ?, ftp_directory = ?,
                    encryption_method = ?, signature_method = ?, public_key = ?,
                    is_active = ?, auto_process = ?
                WHERE id = ? AND company_id = ?
            """
            
            values = (
                partner.name, partner.partner_code, partner.partner_type,
                partner.contact_name, partner.contact_email, partner.contact_phone,
                partner.edi_standard, partner.edi_version, partner.interchange_id,
                partner.sender_id, partner.receiver_id,
                1 if partner.supports_orders else 0,
                1 if partner.supports_invoices else 0,
                1 if partner.supports_acknowledgments else 0,
                1 if partner.supports_asn else 0,
                partner.connection_type, partner.file_path,
                partner.ftp_host, partner.ftp_port, partner.ftp_username, partner.ftp_password, partner.ftp_directory,
                partner.encryption_method, partner.signature_method, partner.public_key,
                1 if partner.is_active else 0,
                1 if partner.auto_process else 0,
                partner.id, company_id
            )
            
            result = self.db_manager.execute_query(query, values)
            if result and (hasattr(result, 'rowcount') and result.rowcount > 0 or not hasattr(result, 'rowcount')):
                self.logger.info(f"✅ تم تحديث شريك EDI: {partner.name} (ID: {partner.id})")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تحديث شريك EDI: {e}", exc_info=True)
            return False
    
    def delete_partner(self, partner_id: int) -> bool:
        """حذف شريك EDI"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = "DELETE FROM edi_partners WHERE id = ? AND company_id = ?"
            result = self.db_manager.execute_query(query, (partner_id, company_id))
            
            if result and (hasattr(result, 'rowcount') and result.rowcount > 0 or not hasattr(result, 'rowcount')):
                self.logger.info(f"✅ تم حذف شريك EDI: ID={partner_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في حذف شريك EDI: {e}", exc_info=True)
            return False
    
    # ============================================================================
    # إدارة المستندات (EDI Documents)
    # ============================================================================
    
    def create_document(self, document: EDIDocument) -> Optional[int]:
        """إنشاء مستند EDI جديد"""
        try:
            company_id = self.tenant_isolation.get_company_id()
            
            query = """
                INSERT INTO edi_documents (
                    document_type, document_number, partner_id, status, direction,
                    raw_content, parsed_content,
                    related_po_id, related_invoice_id, related_sale_id,
                    sent_at, received_at, processed_at, acknowledged_at,
                    error_message, error_details, is_valid, validation_errors,
                    company_id, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            values = (
                document.document_type, document.document_number, document.partner_id,
                document.status, document.direction,
                document.raw_content, document.parsed_content,
                document.related_po_id, document.related_invoice_id, document.related_sale_id,
                document.sent_at, document.received_at, document.processed_at, document.acknowledged_at,
                document.error_message, document.error_details,
                1 if document.is_valid else 0, document.validation_errors,
                company_id, document.created_by
            )
            
            result = self.db_manager.execute_query(query, values)
            if result:
                doc_id = result.lastrowid
                self.logger.info(f"✅ تم إنشاء مستند EDI: {document.document_type} - {document.document_number} (ID: {doc_id})")
                return doc_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في إنشاء مستند EDI: {e}", exc_info=True)
            return None
    
    def get_document(self, document_id: int) -> Optional[EDIDocument]:
        """الحصول على مستند EDI"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = """
                SELECT * FROM edi_documents
                WHERE id = ? AND company_id = ?
            """
            
            row = self.db_manager.fetch_one(query, (document_id, company_id))
            if row:
                return self._row_to_document(row)
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على مستند EDI: {e}", exc_info=True)
            return None
    
    def get_all_documents(self, partner_id: Optional[int] = None,
                         document_type: Optional[str] = None,
                         status: Optional[str] = None) -> List[EDIDocument]:
        """الحصول على جميع المستندات"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            conditions = ["company_id = ?"]
            params = [company_id]
            
            if partner_id:
                conditions.append("partner_id = ?")
                params.append(partner_id)
            
            if document_type:
                conditions.append("document_type = ?")
                params.append(document_type)
            
            if status:
                conditions.append("status = ?")
                params.append(status)
            
            query = f"""
                SELECT * FROM edi_documents
                WHERE {' AND '.join(conditions)}
                ORDER BY created_at DESC
            """
            
            rows = self.db_manager.fetch_all(query, tuple(params))
            return [self._row_to_document(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على المستندات: {e}", exc_info=True)
            return []
    
    # ============================================================================
    # معالجة EDI (Parsing & Generation)
    # ============================================================================
    
    def parse_document(self, edi_content: str, standard: str = "EDIFACT") -> EDIParseResult:
        """تحليل مستند EDI"""
        try:
            parser = EDIParser(standard=standard)
            result = parser.parse(edi_content)
            
            # تسجيل النتيجة
            if result.success:
                self.logger.info(f"✅ تم تحليل مستند EDI: {result.document_type}")
            else:
                self.logger.warning(f"⚠️ فشل تحليل مستند EDI: {', '.join(result.errors)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تحليل مستند EDI: {e}", exc_info=True)
            return EDIParseResult(
                success=False,
                errors=[f"خطأ في التحليل: {str(e)}"]
            )
    
    def generate_document(self, document_type: str, data: Dict[str, Any],
                         sender_id: str, receiver_id: str,
                         standard: str = "EDIFACT") -> EDIGenerateResult:
        """توليد مستند EDI"""
        try:
            generator = EDIGenerator(standard=standard)
            result = generator.generate(document_type, data, sender_id, receiver_id)
            
            # تسجيل النتيجة
            if result.success:
                self.logger.info(f"✅ تم توليد مستند EDI: {document_type}")
            else:
                self.logger.warning(f"⚠️ فشل توليد مستند EDI: {', '.join(result.errors)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في توليد مستند EDI: {e}", exc_info=True)
            return EDIGenerateResult(
                success=False,
                errors=[f"خطأ في التوليد: {str(e)}"]
            )
    
    def generate_purchase_order_edi(self, po_data: Dict[str, Any],
                                    partner: EDIPartner) -> EDIGenerateResult:
        """توليد EDI من أمر شراء"""
        try:
            generator = EDIGenerator(standard=partner.edi_standard)
            sender_id = partner.receiver_id or "SENDER"
            receiver_id = partner.sender_id or partner.partner_code
            
            result = generator.generate_from_purchase_order(po_data, sender_id, receiver_id)
            
            if result.success:
                # حفظ المستند
                document = EDIDocument(
                    document_type="850",
                    document_number=po_data.get("po_number", ""),
                    partner_id=partner.id,
                    status="PENDING",
                    direction="OUTBOUND",
                    raw_content=result.edi_content,
                    related_po_id=po_data.get("id"),
                    company_id=partner.company_id
                )
                
                self.create_document(document)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في توليد EDI لأمر الشراء: {e}", exc_info=True)
            return EDIGenerateResult(
                success=False,
                errors=[f"خطأ في التوليد: {str(e)}"]
            )
    
    # ============================================================================
    # Helper Methods
    # ============================================================================
    
    def _row_to_partner(self, row: Dict[str, Any]) -> EDIPartner:
        """تحويل صف قاعدة البيانات إلى EDIPartner"""
        return EDIPartner(
            id=row.get("id"),
            name=row.get("name", ""),
            partner_code=row.get("partner_code", ""),
            partner_type=row.get("partner_type", "SUPPLIER"),
            contact_name=row.get("contact_name"),
            contact_email=row.get("contact_email"),
            contact_phone=row.get("contact_phone"),
            edi_standard=row.get("edi_standard", "EDIFACT"),
            edi_version=row.get("edi_version", "D96A"),
            interchange_id=row.get("interchange_id"),
            sender_id=row.get("sender_id"),
            receiver_id=row.get("receiver_id"),
            supports_orders=bool(row.get("supports_orders", 1)),
            supports_invoices=bool(row.get("supports_invoices", 1)),
            supports_acknowledgments=bool(row.get("supports_acknowledgments", 1)),
            supports_asn=bool(row.get("supports_asn", 0)),
            connection_type=row.get("connection_type", "FILE"),
            file_path=row.get("file_path"),
            ftp_host=row.get("ftp_host"),
            ftp_port=row.get("ftp_port", 21),
            ftp_username=row.get("ftp_username"),
            ftp_password=row.get("ftp_password"),
            ftp_directory=row.get("ftp_directory"),
            encryption_method=row.get("encryption_method"),
            signature_method=row.get("signature_method"),
            public_key=row.get("public_key"),
            is_active=bool(row.get("is_active", 1)),
            auto_process=bool(row.get("auto_process", 0)),
            company_id=row.get("company_id"),
            created_by=row.get("created_by"),
            created_at=self._parse_datetime(row.get("created_at")),
            updated_at=self._parse_datetime(row.get("updated_at"))
        )
    
    def _row_to_document(self, row: Dict[str, Any]) -> EDIDocument:
        """تحويل صف قاعدة البيانات إلى EDIDocument"""
        return EDIDocument(
            id=row.get("id"),
            document_type=row.get("document_type", ""),
            document_number=row.get("document_number", ""),
            partner_id=row.get("partner_id", 0),
            status=row.get("status", "PENDING"),
            direction=row.get("direction", ""),
            raw_content=row.get("raw_content", ""),
            parsed_content=row.get("parsed_content"),
            related_po_id=row.get("related_po_id"),
            related_invoice_id=row.get("related_invoice_id"),
            related_sale_id=row.get("related_sale_id"),
            sent_at=self._parse_datetime(row.get("sent_at")),
            received_at=self._parse_datetime(row.get("received_at")),
            processed_at=self._parse_datetime(row.get("processed_at")),
            acknowledged_at=self._parse_datetime(row.get("acknowledged_at")),
            error_message=row.get("error_message"),
            error_details=row.get("error_details"),
            is_valid=bool(row.get("is_valid", 1)),
            validation_errors=row.get("validation_errors"),
            company_id=row.get("company_id"),
            created_by=row.get("created_by"),
            created_at=self._parse_datetime(row.get("created_at")),
            updated_at=self._parse_datetime(row.get("updated_at"))
        )
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """تحليل datetime من قاعدة البيانات"""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                try:
                    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except:
                    return None
        return None
    
    # ============================================================================
    # EDI Mapping
    # ============================================================================
    
    def create_mapping(self, name: str, document_type: str, field_mappings: Dict[str, str],
                      partner_id: Optional[int] = None,
                      transformation_rules: Optional[Dict[str, Any]] = None,
                      validation_rules: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """إنشاء EDI Mapping"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = """
                INSERT INTO edi_mappings (
                    name, document_type, partner_id,
                    field_mappings, transformation_rules, validation_rules,
                    company_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            values = (
                name, document_type, partner_id,
                json.dumps(field_mappings, ensure_ascii=False),
                json.dumps(transformation_rules, ensure_ascii=False) if transformation_rules else None,
                json.dumps(validation_rules, ensure_ascii=False) if validation_rules else None,
                company_id
            )
            
            result = self.db_manager.execute_query(query, values)
            if result:
                mapping_id = result.lastrowid
                self.logger.info(f"✅ تم إنشاء EDI Mapping: {name} (ID: {mapping_id})")
                return mapping_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في إنشاء EDI Mapping: {e}", exc_info=True)
            return None
    
    def get_mapping(self, mapping_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على EDI Mapping"""
        try:
            company_id = self.tenant_isolation.get_current_company_id() if self.tenant_isolation else None
            
            query = """
                SELECT * FROM edi_mappings
                WHERE id = ? AND company_id = ?
            """
            
            row = self.db_manager.fetch_one(query, (mapping_id, company_id))
            if row:
                return {
                    "id": row.get("id"),
                    "name": row.get("name"),
                    "document_type": row.get("document_type"),
                    "partner_id": row.get("partner_id"),
                    "field_mappings": json.loads(row.get("field_mappings", "{}")),
                    "transformation_rules": json.loads(row.get("transformation_rules", "{}")) if row.get("transformation_rules") else {},
                    "validation_rules": json.loads(row.get("validation_rules", "{}")) if row.get("validation_rules") else {},
                    "is_active": bool(row.get("is_active", 1)),
                    "is_default": bool(row.get("is_default", 0))
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحصول على EDI Mapping: {e}", exc_info=True)
            return None
    
    def apply_mapping(self, parsed_data: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        """تطبيق EDI Mapping على البيانات المحللة"""
        try:
            field_mappings = mapping.get("field_mappings", {})
            transformation_rules = mapping.get("transformation_rules", {})
            
            mapped_data = {}
            
            # تطبيق Field Mappings
            for target_field, source_path in field_mappings.items():
                value = self._get_nested_value(parsed_data, source_path)
                mapped_data[target_field] = value
            
            # تطبيق Transformation Rules
            for field, rule in transformation_rules.items():
                if field in mapped_data:
                    mapped_data[field] = self._apply_transformation(mapped_data[field], rule)
            
            return mapped_data
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تطبيق EDI Mapping: {e}", exc_info=True)
            return parsed_data
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """الحصول على قيمة متداخلة من قاموس"""
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value
    
    def _apply_transformation(self, value: Any, rule: Dict[str, Any]) -> Any:
        """تطبيق قاعدة تحويل"""
        rule_type = rule.get("type")
        
        if rule_type == "date_format":
            # تحويل تنسيق التاريخ
            from_format = rule.get("from", "%Y%m%d")
            to_format = rule.get("to", "%Y-%m-%d")
            try:
                from datetime import datetime
                dt = datetime.strptime(str(value), from_format)
                return dt.strftime(to_format)
            except:
                return value
        
        elif rule_type == "decimal":
            # تحويل إلى Decimal
            try:
                return Decimal(str(value))
            except:
                return value
        
        elif rule_type == "uppercase":
            return str(value).upper()
        
        elif rule_type == "lowercase":
            return str(value).lower()
        
        return value
    
    # ============================================================================
    # EDI Validation
    # ============================================================================
    
    def validate_document(self, parsed_data: Dict[str, Any], 
                         validation_rules: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
        """التحقق من صحة مستند EDI محلل"""
        errors = []
        
        if not validation_rules:
            # قواعد افتراضية
            validation_rules = {
                "required_fields": ["document_type", "header"],
                "field_types": {
                    "document_type": str,
                    "header": dict
                }
            }
        
        # التحقق من الحقول المطلوبة
        required_fields = validation_rules.get("required_fields", [])
        for field in required_fields:
            if field not in parsed_data or parsed_data[field] is None:
                errors.append(f"الحقل المطلوب مفقود: {field}")
        
        # التحقق من أنواع الحقول
        field_types = validation_rules.get("field_types", {})
        for field, expected_type in field_types.items():
            if field in parsed_data:
                if not isinstance(parsed_data[field], expected_type):
                    errors.append(f"نوع الحقل غير صحيح: {field} (متوقع: {expected_type.__name__})")
        
        # التحقق من صحة البيانات
        if "items" in parsed_data:
            items = parsed_data["items"]
            if not isinstance(items, list):
                errors.append("items يجب أن يكون قائمة")
            else:
                for idx, item in enumerate(items):
                    if not isinstance(item, dict):
                        errors.append(f"البند {idx + 1} يجب أن يكون قاموس")
                    else:
                        if "quantity" in item:
                            try:
                                qty = float(item["quantity"])
                                if qty <= 0:
                                    errors.append(f"كمية البند {idx + 1} يجب أن تكون أكبر من صفر")
                            except:
                                errors.append(f"كمية البند {idx + 1} غير صحيحة")
        
        return len(errors) == 0, errors

