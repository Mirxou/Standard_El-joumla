import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EDI Generator - مولد مستندات EDI
يدعم EDIFACT و X12
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class EDIGenerateResult:
    """نتيجة توليد EDI"""

    success: bool
    edi_content: Optional[str] = None
    errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class EDIGenerator:
    """مولد مستندات EDI"""

    def __init__(self, standard: str = "EDIFACT"):
        """
        تهيئة المولد

        Args:
            standard: المعيار المستخدم (EDIFACT, X12)
        """
        self.standard = standard.upper()
        self.logger = logger

    def generate(
        self,
        document_type: str,
        data: Dict[str, Any],
        sender_id: str = "",
        receiver_id: str = "",
    ) -> EDIGenerateResult:
        """
        توليد محتوى EDI

        Args:
            document_type: نوع المستند (850, 810, 855, etc.)
            data: البيانات المراد تحويلها
            sender_id: معرف المرسل
            receiver_id: معرف المستقبل

        Returns:
            EDIGenerateResult: نتيجة التوليد
        """
        try:
            if self.standard == "EDIFACT":
                return self._generate_edifact(document_type, data, sender_id, receiver_id)
            elif self.standard == "X12":
                return self._generate_x12(document_type, data, sender_id, receiver_id)
            else:
                return EDIGenerateResult(success=False, errors=[f"معيار غير مدعوم: {self.standard}"])
        except Exception as e:
            self.logger.error(f"خطأ في توليد EDI: {e}", exc_info=True)
            return EDIGenerateResult(success=False, errors=[f"خطأ في التوليد: {str(e)}"])

    def _generate_edifact(
        self, doc_type: str, data: Dict[str, Any], sender_id: str, receiver_id: str
    ) -> EDIGenerateResult:
        """توليد EDIFACT"""
        try:
            lines = []

            # UNA: Service String Advice (اختياري)
            lines.append("UNA:+.? '")

            # UNB: Interchange Header
            interchange_ref = datetime.now().strftime("%Y%m%d%H%M%S")
            lines.append(
                f"UNB+UNOA:2+{sender_id}+{receiver_id}+{datetime.now().strftime('%Y%m%d:%H%M')}+{interchange_ref}'"
            )

            # UNH: Message Header
            msg_type = self._map_document_type_to_edifact(doc_type)
            msg_ref = "1"
            lines.append(f"UNH+{msg_ref}+{msg_type}:D:96A:UN'")

            # BGM: Beginning of Message
            doc_number = data.get("header", {}).get("document_number", "")
            lines.append(f"BGM+220+{doc_number}+9'")

            # DTM: Date/Time
            order_date = data.get("header", {}).get("order_date", datetime.now().strftime("%Y%m%d"))
            if isinstance(order_date, date):
                order_date = order_date.strftime("%Y%m%d")
            elif isinstance(order_date, str) and len(order_date) >= 10:
                order_date = order_date.replace("-", "")[:8]
            lines.append(f"DTM+137:{order_date}:102'")

            # Items
            items = data.get("items", [])
            for idx, item in enumerate(items, 1):
                # LIN: Line Item
                product_code = item.get("product_code", "")
                lines.append(f"LIN+{idx}++{product_code}:EN'")

                # QTY: Quantity
                quantity = item.get("quantity", 0)
                unit = item.get("unit", "PCE")  # Piece
                lines.append(f"QTY+21:{quantity}:{unit}'")

                # PRI: Price
                unit_price = item.get("unit_price", 0.0)
                lines.append(f"PRI+AAA:{unit_price}:CT'")

            # UNS: Section Control
            lines.append("UNS+S'")

            # CNT: Control Total
            data.get("summary", {}).get("total_amount", 0.0)
            lines.append(f"CNT+2:{len(items)}'")

            # UNT: Message Trailer
            segment_count = len(lines) - 1  # بدون UNB
            lines.append(f"UNT+{segment_count}+{msg_ref}'")

            # UNZ: Interchange Trailer
            lines.append(f"UNZ+1+{interchange_ref}'")

            edi_content = "\n".join(lines)

            return EDIGenerateResult(success=True, edi_content=edi_content)

        except Exception as e:
            return EDIGenerateResult(success=False, errors=[f"خطأ في توليد EDIFACT: {str(e)}"])

    def _generate_x12(self, doc_type: str, data: Dict[str, Any], sender_id: str, receiver_id: str) -> EDIGenerateResult:
        """توليد X12"""
        try:
            lines = []

            # ISA: Interchange Header
            isa_date = datetime.now().strftime("%y%m%d")
            isa_time = datetime.now().strftime("%H%M")
            isa_ref = "000000001"
            lines.append(
                f"ISA*00*          *00*          *ZZ*{sender_id:<15}*ZZ*{receiver_id:<15}*{isa_date}*{isa_time}*^*00501*{isa_ref}*0*P*:~"  # noqa: E501
            )

            # GS: Functional Group Header
            gs_date = datetime.now().strftime("%Y%m%d")
            gs_time = datetime.now().strftime("%H%M")
            gs_ref = "1"
            lines.append(f"GS*PO*{sender_id}*{receiver_id}*{gs_date}*{gs_time}*{gs_ref}*X*005010~")

            # ST: Transaction Set Header
            st_ref = "0001"
            lines.append(f"ST*{doc_type}*{st_ref}~")

            # BEG: Beginning Segment
            po_type = "00"  # Original
            po_number = data.get("header", {}).get("document_number", "")
            po_date = data.get("header", {}).get("order_date", datetime.now().strftime("%Y%m%d"))
            if isinstance(po_date, date):
                po_date = po_date.strftime("%Y%m%d")
            elif isinstance(po_date, str) and len(po_date) >= 10:
                po_date = po_date.replace("-", "")[:8]
            lines.append(f"BEG*{po_type}*SA*{po_number}**{po_date}~")

            # Items
            items = data.get("items", [])
            for idx, item in enumerate(items, 1):
                # PO1: Line Item
                product_code = item.get("product_code", "")
                quantity = item.get("quantity", 0)
                unit_price = item.get("unit_price", 0.0)
                unit = item.get("unit", "EA")  # Each
                lines.append(f"PO1*{idx}*{quantity}*{unit}*{unit_price}**VC*{product_code}~")

            # CTT: Transaction Totals
            lines.append(f"CTT*{len(items)}~")

            # SE: Transaction Set Trailer
            segment_count = len([l for l in lines if l.startswith(("ST", "BEG", "PO1", "CTT", "SE"))])  # noqa: E741
            lines.append(f"SE*{segment_count}*{st_ref}~")

            # GE: Functional Group Trailer
            lines.append(f"GE*1*{gs_ref}~")

            # IEA: Interchange Trailer
            lines.append(f"IEA*1*{isa_ref}~")

            edi_content = "\n".join(lines)

            return EDIGenerateResult(success=True, edi_content=edi_content)

        except Exception as e:
            return EDIGenerateResult(success=False, errors=[f"خطأ في توليد X12: {str(e)}"])

    def _map_document_type_to_edifact(self, doc_type: str) -> str:
        """تحويل نوع المستند إلى رسالة EDIFACT"""
        mapping = {
            "850": "ORDERS",  # Purchase Order
            "810": "INVOIC",  # Invoice
            "855": "ORDRSP",  # Purchase Order Acknowledgment
            "856": "DESADV",  # Advanced Shipping Notice
            "997": "APERAK",  # Functional Acknowledgment
        }
        return mapping.get(doc_type, f"DOC{doc_type}")

    def generate_from_purchase_order(
        self, po_data: Dict[str, Any], sender_id: str, receiver_id: str
    ) -> EDIGenerateResult:
        """توليد EDI من أمر شراء"""
        # تحويل بيانات أمر الشراء إلى تنسيق EDI
        edi_data = {
            "header": {
                "document_number": po_data.get("po_number", ""),
                "order_date": po_data.get("order_date", datetime.now().strftime("%Y-%m-%d")),
            },
            "items": [],
            "summary": {"total_amount": float(po_data.get("total_amount", 0))},
        }

        # تحويل البنود
        items = po_data.get("items", [])
        for item in items:
            edi_data["items"].append(
                {
                    "product_code": item.get("product_code", ""),
                    "quantity": float(item.get("quantity_ordered", 0)),
                    "unit_price": float(item.get("unit_price", 0)),
                    "unit": item.get("unit_of_measure", "PCE"),
                }
            )

        return self.generate("850", edi_data, sender_id, receiver_id)

    def generate_from_invoice(
        self, invoice_data: Dict[str, Any], sender_id: str, receiver_id: str
    ) -> EDIGenerateResult:
        """توليد EDI من فاتورة"""
        # تحويل بيانات الفاتورة إلى تنسيق EDI
        edi_data = {
            "header": {
                "document_number": invoice_data.get("invoice_number", ""),
                "invoice_date": invoice_data.get("purchase_date", datetime.now().strftime("%Y-%m-%d")),
            },
            "items": [],
            "summary": {"total_amount": float(invoice_data.get("total_amount", 0))},
        }

        # تحويل البنود
        items = invoice_data.get("items", [])
        for item in items:
            edi_data["items"].append(
                {
                    "product_code": item.get("product_code", ""),
                    "quantity": float(item.get("quantity", 0)),
                    "unit_price": float(item.get("unit_price", 0)),
                    "unit": "PCE",
                }
            )

        return self.generate("810", edi_data, sender_id, receiver_id)
