#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EDI Parser - محلل مستندات EDI
يدعم EDIFACT و X12
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class EDIParseResult:
    """نتيجة تحليل EDI"""
    success: bool
    document_type: Optional[str] = None  # 850, 810, 855, etc.
    data: Optional[Dict[str, Any]] = None
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class EDIParser:
    """محلل مستندات EDI"""
    
    def __init__(self, standard: str = "EDIFACT"):
        """
        تهيئة المحلل
        
        Args:
            standard: المعيار المستخدم (EDIFACT, X12)
        """
        self.standard = standard.upper()
        self.logger = logger
        
    def parse(self, edi_content: str) -> EDIParseResult:
        """
        تحليل محتوى EDI
        
        Args:
            edi_content: المحتوى الخام لـ EDI
            
        Returns:
            EDIParseResult: نتيجة التحليل
        """
        try:
            if self.standard == "EDIFACT":
                return self._parse_edifact(edi_content)
            elif self.standard == "X12":
                return self._parse_x12(edi_content)
            else:
                return EDIParseResult(
                    success=False,
                    errors=[f"معيار غير مدعوم: {self.standard}"]
                )
        except Exception as e:
            self.logger.error(f"خطأ في تحليل EDI: {e}", exc_info=True)
            return EDIParseResult(
                success=False,
                errors=[f"خطأ في التحليل: {str(e)}"]
            )
    
    def _parse_edifact(self, content: str) -> EDIParseResult:
        """
        تحليل EDIFACT
        
        EDIFACT Format:
        UNA:+.? '
        UNB+UNOA:2+SENDER+RECEIVER+20231208:1200+12345'
        UNH+1+ORDERS:D:96A:UN'
        ...
        UNT+5+1'
        UNZ+1+12345'
        """
        try:
            lines = content.strip().split('\n')
            if not lines:
                return EDIParseResult(
                    success=False,
                    errors=["محتوى EDI فارغ"]
                )
            
            # تحديد نوع المستند من UNH
            document_type = None
            segments = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # UNH = Message Header
                if line.startswith('UNH+'):
                    parts = line.split('+')
                    if len(parts) >= 2:
                        # UNH+1+ORDERS:D:96A:UN
                        msg_type = parts[1].split(':')[0] if ':' in parts[1] else parts[1]
                        document_type = self._map_edifact_document_type(msg_type)
                
                # تجميع المقاطع
                segments.append(line)
            
            if not document_type:
                return EDIParseResult(
                    success=False,
                    errors=["لم يتم العثور على نوع المستند في UNH"]
                )
            
            # تحليل المقاطع
            parsed_data = self._parse_edifact_segments(segments, document_type)
            
            return EDIParseResult(
                success=True,
                document_type=document_type,
                data=parsed_data
            )
            
        except Exception as e:
            return EDIParseResult(
                success=False,
                errors=[f"خطأ في تحليل EDIFACT: {str(e)}"]
            )
    
    def _parse_x12(self, content: str) -> EDIParseResult:
        """
        تحليل X12
        
        X12 Format:
        ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *231208*1200*^*00501*000000001*0*P*:~
        GS*PO*SENDER*RECEIVER*20231208*1200*1*X*005010~
        ST*850*0001~
        ...
        SE*10*0001~
        GE*1*1~
        IEA*1*000000001~
        """
        try:
            lines = content.strip().split('\n')
            if not lines:
                return EDIParseResult(
                    success=False,
                    errors=["محتوى EDI فارغ"]
                )
            
            # تحديد نوع المستند من ST
            document_type = None
            segments = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # ST = Transaction Set Header
                if line.startswith('ST*'):
                    parts = line.split('*')
                    if len(parts) >= 2:
                        document_type = parts[1]  # 850, 810, etc.
                
                segments.append(line)
            
            if not document_type:
                return EDIParseResult(
                    success=False,
                    errors=["لم يتم العثور على نوع المستند في ST"]
                )
            
            # تحليل المقاطع
            parsed_data = self._parse_x12_segments(segments, document_type)
            
            return EDIParseResult(
                success=True,
                document_type=document_type,
                data=parsed_data
            )
            
        except Exception as e:
            return EDIParseResult(
                success=False,
                errors=[f"خطأ في تحليل X12: {str(e)}"]
            )
    
    def _parse_edifact_segments(self, segments: List[str], doc_type: str) -> Dict[str, Any]:
        """تحليل مقاطع EDIFACT"""
        data = {
            "document_type": doc_type,
            "header": {},
            "items": [],
            "summary": {}
        }
        
        for segment in segments:
            if segment.startswith('UNB+'):
                # Interchange Header
                parts = segment.split('+')
                if len(parts) >= 4:
                    data["header"]["sender"] = parts[2] if len(parts) > 2 else ""
                    data["header"]["receiver"] = parts[3] if len(parts) > 3 else ""
            
            elif segment.startswith('UNH+'):
                # Message Header
                parts = segment.split('+')
                if len(parts) >= 2:
                    msg_ref = parts[1].split('+')[0] if '+' in parts[1] else parts[1]
                    data["header"]["message_reference"] = msg_ref
            
            elif segment.startswith('BGM+'):
                # Beginning of Message (Order Number, etc.)
                parts = segment.split('+')
                if len(parts) >= 2:
                    data["header"]["document_number"] = parts[1] if len(parts) > 1 else ""
            
            elif segment.startswith('DTM+'):
                # Date/Time
                parts = segment.split('+')
                if len(parts) >= 3:
                    date_type = parts[1] if len(parts) > 1 else ""
                    date_value = parts[2] if len(parts) > 2 else ""
                    if date_type == "137":  # Order Date
                        data["header"]["order_date"] = self._parse_edifact_date(date_value)
            
            elif segment.startswith('LIN+'):
                # Line Item
                parts = segment.split('+')
                item = {
                    "line_number": parts[1] if len(parts) > 1 else "",
                    "product_code": "",
                    "quantity": 0,
                    "unit_price": 0.0
                }
                data["items"].append(item)
            
            elif segment.startswith('QTY+'):
                # Quantity
                parts = segment.split('+')
                if len(parts) >= 3 and data["items"]:
                    quantity = parts[2] if len(parts) > 2 else "0"
                    try:
                        data["items"][-1]["quantity"] = float(quantity)
                    except:
                        pass
            
            elif segment.startswith('PRI+'):
                # Price
                parts = segment.split('+')
                if len(parts) >= 3 and data["items"]:
                    price = parts[2] if len(parts) > 2 else "0"
                    try:
                        data["items"][-1]["unit_price"] = float(price)
                    except:
                        pass
        
        return data
    
    def _parse_x12_segments(self, segments: List[str], doc_type: str) -> Dict[str, Any]:
        """تحليل مقاطع X12"""
        data = {
            "document_type": doc_type,
            "header": {},
            "items": [],
            "summary": {}
        }
        
        for segment in segments:
            if segment.startswith('ISA*'):
                # Interchange Header
                parts = segment.split('*')
                if len(parts) >= 7:
                    data["header"]["sender"] = parts[6] if len(parts) > 6 else ""
                    data["header"]["receiver"] = parts[8] if len(parts) > 8 else ""
            
            elif segment.startswith('BEG*'):
                # Beginning Segment (Order Number)
                parts = segment.split('*')
                if len(parts) >= 3:
                    data["header"]["document_number"] = parts[3] if len(parts) > 3 else ""
            
            elif segment.startswith('DTM*'):
                # Date/Time
                parts = segment.split('*')
                if len(parts) >= 3:
                    date_type = parts[1] if len(parts) > 1 else ""
                    date_value = parts[2] if len(parts) > 2 else ""
                    if date_type == "001":  # Requested Ship Date
                        data["header"]["order_date"] = self._parse_x12_date(date_value)
            
            elif segment.startswith('PO1*'):
                # Line Item
                parts = segment.split('*')
                item = {
                    "line_number": parts[1] if len(parts) > 1 else "",
                    "product_code": parts[7] if len(parts) > 7 else "",
                    "quantity": float(parts[2]) if len(parts) > 2 and parts[2] else 0,
                    "unit_price": float(parts[4]) if len(parts) > 4 and parts[4] else 0.0
                }
                data["items"].append(item)
        
        return data
    
    def _map_edifact_document_type(self, msg_type: str) -> str:
        """تحويل نوع رسالة EDIFACT إلى كود قياسي"""
        mapping = {
            "ORDERS": "850",      # Purchase Order
            "INVOIC": "810",      # Invoice
            "ORDERS": "855",      # Purchase Order Acknowledgment
            "DESADV": "856",      # Advanced Shipping Notice
            "APERAK": "997",      # Functional Acknowledgment
        }
        return mapping.get(msg_type.upper(), msg_type)
    
    def _parse_edifact_date(self, date_str: str) -> Optional[str]:
        """تحليل تاريخ EDIFACT (YYYYMMDD)"""
        try:
            if len(date_str) >= 8:
                year = date_str[:4]
                month = date_str[4:6]
                day = date_str[6:8]
                return f"{year}-{month}-{day}"
        except:
            pass
        return None
    
    def _parse_x12_date(self, date_str: str) -> Optional[str]:
        """تحليل تاريخ X12 (YYYYMMDD)"""
        try:
            if len(date_str) >= 8:
                year = date_str[:4]
                month = date_str[4:6]
                day = date_str[6:8]
                return f"{year}-{month}-{day}"
        except:
            pass
        return None
    
    def validate(self, edi_content: str) -> Tuple[bool, List[str]]:
        """
        التحقق من صحة محتوى EDI
        
        Returns:
            Tuple[bool, List[str]]: (صحيح/غير صحيح, قائمة الأخطاء)
        """
        errors = []
        
        if not edi_content or not edi_content.strip():
            errors.append("محتوى EDI فارغ")
            return False, errors
        
        if self.standard == "EDIFACT":
            if "UNB+" not in edi_content:
                errors.append("مفقود: UNB (Interchange Header)")
            if "UNH+" not in edi_content:
                errors.append("مفقود: UNH (Message Header)")
            if "UNT+" not in edi_content:
                errors.append("مفقود: UNT (Message Trailer)")
            if "UNZ+" not in edi_content:
                errors.append("مفقود: UNZ (Interchange Trailer)")
        
        elif self.standard == "X12":
            if "ISA*" not in edi_content:
                errors.append("مفقود: ISA (Interchange Header)")
            if "GS*" not in edi_content:
                errors.append("مفقود: GS (Functional Group Header)")
            if "ST*" not in edi_content:
                errors.append("مفقود: ST (Transaction Set Header)")
            if "SE*" not in edi_content:
                errors.append("مفقود: SE (Transaction Set Trailer)")
            if "GE*" not in edi_content:
                errors.append("مفقود: GE (Functional Group Trailer)")
            if "IEA*" not in edi_content:
                errors.append("مفقود: IEA (Interchange Trailer)")
        
        return len(errors) == 0, errors

