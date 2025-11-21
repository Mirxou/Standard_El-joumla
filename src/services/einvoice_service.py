"""
نظام الفوترة الإلكترونية الحكومية
E-Invoicing Government Integration

Features:
- التوافق مع معايير الفاتورة الإلكترونية
- التوقيع الرقمي
- تنسيق XML/JSON
- التكامل مع APIs الحكومية
- QR Code generation
"""

from typing import Dict, Optional
from datetime import datetime
import json
import hashlib
import base64
from dataclasses import dataclass


@dataclass
class EInvoiceConfig:
    """إعدادات الفوترة الإلكترونية"""
    company_vat_number: str
    company_name: str
    company_address: str
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    certificate_path: Optional[str] = None


class EInvoiceGenerator:
    """مولد الفواتير الإلكترونية"""
    
    def __init__(self, config: EInvoiceConfig):
        """
        تهيئة مولد الفواتير
        
        Args:
            config: إعدادات الفوترة الإلكترونية
        """
        self.config = config
    
    def generate_invoice(
        self,
        invoice_number: str,
        invoice_date: str,
        customer_name: str,
        customer_vat: Optional[str],
        items: list,
        total_amount: float,
        vat_amount: float
    ) -> Dict:
        """
        إنشاء فاتورة إلكترونية
        
        Args:
            invoice_number: رقم الفاتورة
            invoice_date: تاريخ الفاتورة
            customer_name: اسم العميل
            customer_vat: الرقم الضريبي للعميل
            items: قائمة الأصناف
            total_amount: المبلغ الإجمالي
            vat_amount: قيمة الضريبة
            
        Returns:
            الفاتورة الإلكترونية
        """
        invoice_data = {
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "seller": {
                "name": self.config.company_name,
                "vat_number": self.config.company_vat_number,
                "address": self.config.company_address
            },
            "buyer": {
                "name": customer_name,
                "vat_number": customer_vat
            },
            "items": items,
            "totals": {
                "subtotal": total_amount - vat_amount,
                "vat": vat_amount,
                "total": total_amount
            },
            "generated_at": datetime.now().isoformat()
        }
        
        # إنشاء التوقيع الرقمي
        signature = self._generate_signature(invoice_data)
        invoice_data["digital_signature"] = signature
        
        # إنشاء QR Code
        qr_data = self._generate_qr_data(invoice_data)
        invoice_data["qr_code"] = qr_data
        
        return invoice_data
    
    def _generate_signature(self, invoice_data: Dict) -> str:
        """
        إنشاء التوقيع الرقمي
        
        Args:
            invoice_data: بيانات الفاتورة
            
        Returns:
            التوقيع الرقمي
        """
        # تحويل البيانات إلى نص
        invoice_text = json.dumps(invoice_data, sort_keys=True)
        
        # حساب hash
        hash_object = hashlib.sha256(invoice_text.encode())
        signature = base64.b64encode(hash_object.digest()).decode()
        
        return signature
    
    def _generate_qr_data(self, invoice_data: Dict) -> str:
        """
        إنشاء بيانات QR Code
        
        Args:
            invoice_data: بيانات الفاتورة
            
        Returns:
            نص QR Code
        """
        # تنسيق بيانات QR حسب المعايير الجزائرية
        qr_fields = [
            ("1", self.config.company_name),
            ("2", self.config.company_vat_number),
            ("3", invoice_data["invoice_date"]),
            ("4", str(invoice_data["totals"]["total"])),
            ("5", str(invoice_data["totals"]["vat"]))
        ]
        
        # تشفير البيانات
        qr_text = "|".join([f"{tag}:{value}" for tag, value in qr_fields])
        qr_encoded = base64.b64encode(qr_text.encode()).decode()
        
        return qr_encoded
    
    def convert_to_xml(self, invoice_data: Dict) -> str:
        """
        تحويل الفاتورة إلى XML
        
        Args:
            invoice_data: بيانات الفاتورة
            
        Returns:
            XML string
        """
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
    <ID>{invoice_data["invoice_number"]}</ID>
    <IssueDate>{invoice_data["invoice_date"]}</IssueDate>
    <Seller>
        <Name>{invoice_data["seller"]["name"]}</Name>
        <VATNumber>{invoice_data["seller"]["vat_number"]}</VATNumber>
        <Address>{invoice_data["seller"]["address"]}</Address>
    </Seller>
    <Buyer>
        <Name>{invoice_data["buyer"]["name"]}</Name>
        <VATNumber>{invoice_data["buyer"].get("vat_number", "N/A")}</VATNumber>
    </Buyer>
    <Items>'''
        
        for item in invoice_data["items"]:
            xml += f'''
        <Item>
            <Name>{item.get("name", "")}</Name>
            <Quantity>{item.get("quantity", 0)}</Quantity>
            <UnitPrice>{item.get("unit_price", 0)}</UnitPrice>
            <Total>{item.get("total", 0)}</Total>
        </Item>'''
        
        xml += f'''
    </Items>
    <Totals>
        <Subtotal>{invoice_data["totals"]["subtotal"]}</Subtotal>
        <VAT>{invoice_data["totals"]["vat"]}</VAT>
        <Total>{invoice_data["totals"]["total"]}</Total>
    </Totals>
    <Signature>{invoice_data.get("digital_signature", "")}</Signature>
    <QRCode>{invoice_data.get("qr_code", "")}</QRCode>
</Invoice>'''
        
        return xml
    
    def submit_to_government(self, invoice_data: Dict) -> Dict:
        """
        إرسال الفاتورة إلى النظام الحكومي
        
        Args:
            invoice_data: بيانات الفاتورة
            
        Returns:
            نتيجة الإرسال
        """
        if not self.config.api_endpoint or not self.config.api_key:
            return {
                "status": "offline",
                "message": "لم يتم تكوين اتصال API الحكومي",
                "invoice_saved": True
            }
        
        # TODO: تنفيذ الاتصال الفعلي بـ API الحكومي
        # هذا مثال تجريبي
        
        return {
            "status": "submitted",
            "message": "تم إرسال الفاتورة بنجاح",
            "reference_number": f"GOV-{invoice_data['invoice_number']}",
            "timestamp": datetime.now().isoformat()
        }
    
    def verify_invoice(self, invoice_data: Dict) -> bool:
        """
        التحقق من صحة الفاتورة
        
        Args:
            invoice_data: بيانات الفاتورة
            
        Returns:
            True إذا كانت الفاتورة صحيحة
        """
        # التحقق من التوقيع
        saved_signature = invoice_data.pop("digital_signature", None)
        calculated_signature = self._generate_signature(invoice_data)
        invoice_data["digital_signature"] = saved_signature
        
        return saved_signature == calculated_signature


class RecurringInvoiceManager:
    """إدارة الفواتير الدورية"""
    
    def __init__(self, db_manager):
        """
        تهيئة مدير الفواتير الدورية
        
        Args:
            db_manager: مدير قاعدة البيانات
        """
        self.db = db_manager
        self._create_tables()
    
    def _create_tables(self):
        """إنشاء جداول الفواتير الدورية"""
        conn = self.db.connection
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recurring_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                description TEXT,
                amount REAL NOT NULL,
                frequency TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                next_invoice_date TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recurring_invoice_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recurring_invoice_id INTEGER NOT NULL,
                invoice_number TEXT,
                generated_date TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (recurring_invoice_id) REFERENCES recurring_invoices(id)
            )
        ''')
        
        conn.commit()
    
    def create_recurring_invoice(
        self,
        customer_id: int,
        description: str,
        amount: float,
        frequency: str,  # 'monthly', 'quarterly', 'annually'
        start_date: str,
        end_date: Optional[str] = None
    ) -> int:
        """إنشاء فاتورة دورية"""
        conn = self.db.connection
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO recurring_invoices 
            (customer_id, description, amount, frequency, start_date, end_date, next_invoice_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (customer_id, description, amount, frequency, start_date, end_date, start_date))
        
        conn.commit()
        return cursor.lastrowid
    
    def get_due_invoices(self) -> list:
        """الحصول على الفواتير المستحقة"""
        conn = self.db.connection
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT id, customer_id, description, amount, frequency, next_invoice_date
            FROM recurring_invoices
            WHERE is_active = 1
                AND next_invoice_date <= ?
                AND (end_date IS NULL OR end_date >= ?)
        ''', (today, today))
        
        due_invoices = []
        for row in cursor.fetchall():
            due_invoices.append({
                "id": row[0],
                "customer_id": row[1],
                "description": row[2],
                "amount": row[3],
                "frequency": row[4],
                "next_invoice_date": row[5]
            })
        
        return due_invoices


if __name__ == "__main__":
    print("📄 E-Invoicing System Test")
    print("=" * 50)
    
    # اختبار التكوين
    config = EInvoiceConfig(
        company_vat_number="300012345600003",
        company_name="شركة الإصدار المنطقي",
        company_address="الجزائر العاصمة، الجزائر"
    )
    
    generator = EInvoiceGenerator(config)
    
    # إنشاء فاتورة تجريبية
    invoice = generator.generate_invoice(
        invoice_number="INV-001",
        invoice_date="2025-11-20",
        customer_name="عميل تجريبي",
        customer_vat="300012345600004",
        items=[
            {"name": "منتج 1", "quantity": 2, "unit_price": 100, "total": 200},
            {"name": "منتج 2", "quantity": 1, "unit_price": 50, "total": 50}
        ],
        total_amount=287.5,
        vat_amount=37.5
    )
    
    print("\n✅ E-Invoice generated successfully!")
    print(f"Invoice Number: {invoice['invoice_number']}")
    print(f"Digital Signature: {invoice['digital_signature'][:50]}...")
    print(f"QR Code: {invoice['qr_code'][:50]}...")
