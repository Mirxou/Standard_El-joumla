#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Printer Emulator
محاكي الطابعة الحرارية (ESC/POS) لاختبار المخرجات قبل الإرسال
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from io import StringIO
from src.utils.logger import setup_logger


class PrinterEmulator:
    """محاكي طابعة حرارية (ESC/POS)"""
    
    def __init__(self):
        self.output: List[str] = []
        self.current_alignment = "left"
        self.current_text_type = "normal"
        self.logger = setup_logger(__name__)
        self.line_width = 48  # عرض السطر الافتراضي (58mm printer)
    
    def initialize(self):
        """تهيئة الطابعة (ESC @)"""
        self.output.append("---INITIALIZE---")
    
    def set_alignment(self, align: str = "left"):
        """
        تعيين المحاذاة (ESC a)
        
        Args:
            align: left, center, right
        """
        self.current_alignment = align
        self.output.append(f"[ALIGN: {align}]")
    
    def set_text_type(self, text_type: str = "normal"):
        """
        تعيين نوع النص (ESC !)
        
        Args:
            text_type: normal, bold, large, bold_large
        """
        self.current_text_type = text_type
        self.output.append(f"[TEXT_TYPE: {text_type}]")
    
    def text(self, text: str):
        """
        طباعة نص
        
        Args:
            text: النص المراد طباعته
        """
        # تطبيق المحاذاة
        if self.current_alignment == "center":
            padding = (self.line_width - len(text.strip())) // 2
            text = " " * padding + text.strip()
        elif self.current_alignment == "right":
            padding = self.line_width - len(text.strip())
            text = " " * padding + text.strip()
        
        # تطبيق نوع النص
        if self.current_text_type == "bold":
            text = f"**{text}**"
        elif self.current_text_type == "large":
            text = f"# {text} #"
        elif self.current_text_type == "bold_large":
            text = f"## {text} ##"
        
        self.output.append(text)
    
    def feed_lines(self, lines: int = 1):
        """
        تغذية عدد من الأسطر (ESC d)
        
        Args:
            lines: عدد الأسطر
        """
        for _ in range(lines):
            self.output.append("")
    
    def separator(self, char: str = "-"):
        """طباعة فاصل"""
        separator_line = char * self.line_width
        self.output.append(separator_line)
    
    def cut_paper(self):
        """قطع الورق (GS v 0)"""
        self.output.append("---CUT---")
    
    def open_cash_drawer(self):
        """فتح الدرج النقدي (ESC p)"""
        self.output.append("---CASH_DRAWER_OPEN---")
    
    def set_line_width(self, width: int):
        """
        تعيين عرض السطر
        
        Args:
            width: عرض السطر (بعدد الأحرف)
        """
        self.line_width = width
    
    def get_output(self) -> str:
        """
        الحصول على المخرجات كسلسلة نصية
        
        Returns:
            المخرجات كسلسلة نصية
        """
        return "\n".join(self.output)
    
    def get_output_lines(self) -> List[str]:
        """
        الحصول على المخرجات كقائمة من الأسطر
        
        Returns:
            قائمة من الأسطر
        """
        return self.output.copy()
    
    def clear(self):
        """مسح المخرجات"""
        self.output.clear()
    
    def preview_receipt(self, receipt_data: Dict[str, Any]) -> str:
        """
        معاينة الإيصال
        
        Args:
            receipt_data: بيانات الإيصال {
                'store_name': str,
                'store_address': str,
                'invoice_number': str,
                'date': str,
                'items': List[Dict],
                'subtotal': float,
                'tax': float,
                'total': float,
                'payment_method': str,
                'cash_received': float,
                'change': float
            }
        
        Returns:
            المخرجات كسلسلة نصية
        """
        self.clear()
        self.initialize()
        
        # العنوان
        self.set_alignment("center")
        self.set_text_type("bold_large")
        self.text(receipt_data.get('store_name', 'Store Name'))
        self.feed_lines(1)
        
        # العنوان الفرعي
        self.set_text_type("normal")
        if receipt_data.get('store_address'):
            self.text(receipt_data['store_address'])
            self.feed_lines(1)
        
        # الفاصل
        self.separator()
        self.feed_lines(1)
        
        # معلومات الفاتورة
        self.set_alignment("left")
        if receipt_data.get('invoice_number'):
            self.text(f"Invoice: {receipt_data['invoice_number']}")
        if receipt_data.get('date'):
            self.text(f"Date: {receipt_data['date']}")
        self.feed_lines(1)
        
        # الفاصل
        self.separator()
        self.feed_lines(1)
        
        # العناصر
        items = receipt_data.get('items', [])
        for item in items:
            name = item.get('name', '')
            qty = item.get('quantity', 0)
            price = item.get('price', 0.0)
            total = qty * price
            
            # اسم المنتج
            self.text(name[:self.line_width - 20])
            
            # الكمية والسعر
            item_line = f"{qty} x {price:.2f} = {total:.2f}"
            self.text(item_line)
            self.feed_lines(1)
        
        # الفاصل
        self.separator()
        self.feed_lines(1)
        
        # الملخص
        self.set_alignment("right")
        if receipt_data.get('subtotal'):
            self.text(f"Subtotal: {receipt_data['subtotal']:.2f}")
        if receipt_data.get('tax'):
            self.text(f"Tax: {receipt_data['tax']:.2f}")
        
        self.set_text_type("bold")
        if receipt_data.get('total'):
            self.text(f"TOTAL: {receipt_data['total']:.2f}")
        self.set_text_type("normal")
        self.feed_lines(1)
        
        # طريقة الدفع
        if receipt_data.get('payment_method'):
            self.text(f"Payment: {receipt_data['payment_method']}")
        if receipt_data.get('cash_received'):
            self.text(f"Cash: {receipt_data['cash_received']:.2f}")
        if receipt_data.get('change'):
            self.text(f"Change: {receipt_data['change']:.2f}")
        
        self.feed_lines(2)
        
        # شكر
        self.set_alignment("center")
        self.text("Thank you!")
        self.feed_lines(2)
        
        # قطع الورق
        self.cut_paper()
        
        return self.get_output()
    
    def save_to_file(self, file_path: str):
        """
        حفظ المخرجات في ملف
        
        Args:
            file_path: مسار الملف
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.get_output())
            self.logger.info(f"✅ تم حفظ معاينة الطابعة في: {file_path}")
        except Exception as e:
            self.logger.error(f"❌ فشل حفظ معاينة الطابعة: {str(e)}")


# دالة مساعدة لمعاينة الإيصال
def preview_receipt(receipt_data: Dict[str, Any]) -> str:
    """
    معاينة الإيصال باستخدام Printer Emulator
    
    Args:
        receipt_data: بيانات الإيصال
    
    Returns:
        المخرجات كسلسلة نصية
    """
    emulator = PrinterEmulator()
    return emulator.preview_receipt(receipt_data)


if __name__ == "__main__":
    # اختبار Printer Emulator
    test_receipt = {
        'store_name': 'Test Store',
        'store_address': '123 Main St',
        'invoice_number': 'INV-001',
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'items': [
            {'name': 'Product 1', 'quantity': 2, 'price': 10.0},
            {'name': 'Product 2', 'quantity': 1, 'price': 25.5},
        ],
        'subtotal': 45.5,
        'tax': 2.28,
        'total': 47.78,
        'payment_method': 'Cash',
        'cash_received': 50.0,
        'change': 2.22
    }
    
    emulator = PrinterEmulator()
    output = emulator.preview_receipt(test_receipt)
    print(output)
    print("\n" + "="*50)
    print("Preview saved to receipt_preview.txt")
    emulator.save_to_file("receipt_preview.txt")
