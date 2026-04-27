#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct Print Service
خدمة الطباعة المباشرة للطابعات الحرارية (ESC/POS) بدون حوار Windows
"""

import time
from typing import Optional, Dict, Any, List
from enum import Enum
from src.utils.logger import setup_logger

try:
    import usb.core
    import usb.util
    from escpos.printer import Usb
    _USB_AVAILABLE = True
except ImportError:
    _USB_AVAILABLE = False
    Usb = None

try:
    import socket
    _NETWORK_AVAILABLE = True
except ImportError:
    _NETWORK_AVAILABLE = False


class PrinterType(Enum):
    """نوع الطابعة"""
    USB = "usb"
    NETWORK = "network"
    SERIAL = "serial"


class DirectPrintService:
    """خدمة الطباعة المباشرة (ESC/POS)"""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.usb_available = _USB_AVAILABLE
        self.network_available = _NETWORK_AVAILABLE
    
    def discover_printers(self) -> List[Dict[str, Any]]:
        """
        اكتشاف الطابعات المتاحة
        
        Returns:
            قائمة بالطابعات المتاحة
        """
        printers = []
        
        # اكتشاف USB printers
        if self.usb_available:
            printers.extend(self._discover_usb_printers())
        
        # اكتشاف Network printers (يمكن إضافتها يدوياً)
        # printers.extend(self._discover_network_printers())
        
        return printers
    
    def _discover_usb_printers(self) -> List[Dict[str, Any]]:
        """اكتشاف الطابعات USB"""
        printers = []
        
        try:
            devices = usb.core.find(find_all=True)
            for dev in devices:
                if dev.bDeviceClass == 7:  # Printer class
                    try:
                        name = usb.util.get_string(dev, dev.iProduct) or f"Printer {dev.idVendor:04x}:{dev.idProduct:04x}"
                        printers.append({
                            'type': PrinterType.USB.value,
                            'vendor_id': dev.idVendor,
                            'product_id': dev.idProduct,
                            'name': name,
                            'identifier': f"{dev.idVendor:04x}:{dev.idProduct:04x}"
                        })
                    except Exception:
                        pass
        except Exception as e:
            self.logger.warning(f"⚠️ فشل اكتشاف USB printers: {str(e)}")
        
        return printers
    
    def print_receipt(
        self,
        printer_config: Dict[str, Any],
        receipt_data: Dict[str, Any],
        use_emulator: bool = False
    ) -> tuple[bool, str]:
        """
        طباعة فاتورة مباشرة (ESC/POS)
        
        Args:
            printer_config: إعدادات الطابعة
            receipt_data: بيانات الفاتورة
            use_emulator: استخدام المحاكي (للمعاينة)
            
        Returns:
            (نجح, رسالة)
        """
        if use_emulator:
            from src.services.printer_emulator import PrinterEmulator
            emulator = PrinterEmulator()
            self._format_receipt(emulator, receipt_data)
            output = emulator.get_output()
            self.logger.info(f"📄 معاينة الفاتورة:\n{output}")
            return True, "تمت المعاينة بنجاح"
        
        printer_type = printer_config.get('type', PrinterType.USB.value)
        
        if printer_type == PrinterType.USB.value:
            return self._print_via_usb(printer_config, receipt_data)
        elif printer_type == PrinterType.NETWORK.value:
            return self._print_via_network(printer_config, receipt_data)
        else:
            return False, f"نوع طابعة غير مدعوم: {printer_type}"
    
    def _print_via_usb(self, printer_config: Dict[str, Any], receipt_data: Dict[str, Any]) -> tuple[bool, str]:
        """الطباعة عبر USB"""
        if not self.usb_available:
            return False, "مكتبات USB غير متوفرة"
        
        try:
            vendor_id = printer_config['vendor_id']
            product_id = printer_config['product_id']
            
            printer = Usb(vendor_id, product_id, 0, timeout=0, in_ep=0x82, out_ep=0x01)
            
            # تنسيق وطباعة الفاتورة
            self._format_receipt(printer, receipt_data)
            
            # قطع الورق
            printer.cut()
            
            self.logger.info("✅ تمت طباعة الفاتورة بنجاح")
            return True, "تمت الطباعة بنجاح"
            
        except Exception as e:
            error_msg = f"فشل الطباعة: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def _print_via_network(self, printer_config: Dict[str, Any], receipt_data: Dict[str, Any]) -> tuple[bool, str]:
        """الطباعة عبر الشبكة"""
        if not self.network_available:
            return False, "مكتبات الشبكة غير متوفرة"
        
        try:
            host = printer_config.get('host')
            port = printer_config.get('port', 9100)
            
            # إنشاء اتصال TCP
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            
            # تنسيق الفاتورة كـ ESC/POS commands
            commands = self._format_receipt_commands(receipt_data)
            
            # إرسال الأوامر
            sock.sendall(commands)
            sock.close()
            
            self.logger.info("✅ تمت طباعة الفاتورة عبر الشبكة")
            return True, "تمت الطباعة بنجاح"
            
        except Exception as e:
            error_msg = f"فشل الطباعة عبر الشبكة: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def _format_receipt(self, printer, receipt_data: Dict[str, Any]):
        """
        تنسيق الفاتورة (ESC/POS)
        
        Args:
            printer: كائن الطابعة (Usb أو Emulator)
            receipt_data: بيانات الفاتورة
        """
        # Initialize
        printer.set(align='center', text_type='B', width=2, height=2)
        printer.text(f"{receipt_data.get('store_name', 'المتجر')}\n")
        printer.set(align='center', text_type='normal', width=1, height=1)
        printer.text(f"{receipt_data.get('store_address', '')}\n")
        printer.text(f"Tel: {receipt_data.get('store_phone', '')}\n")
        printer.text("=" * 32 + "\n")
        
        # Invoice info
        printer.set(align='left')
        printer.text(f"فاتورة رقم: {receipt_data.get('invoice_number', '')}\n")
        printer.text(f"التاريخ: {receipt_data.get('date', '')}\n")
        printer.text(f"العميل: {receipt_data.get('customer_name', '')}\n")
        printer.text("-" * 32 + "\n")
        
        # Items
        items = receipt_data.get('items', [])
        for item in items:
            name = item.get('name', '')[:20]  # تقصير الاسم
            qty = item.get('quantity', 0)
            price = item.get('unit_price', 0)
            total = item.get('total_price', 0)
            
            printer.text(f"{name}\n")
            printer.text(f"  {qty} x {price:.2f} = {total:.2f}\n")
        
        printer.text("-" * 32 + "\n")
        
        # Totals
        printer.set(align='right')
        printer.text(f"المجموع: {receipt_data.get('total_amount', 0):.2f}\n")
        printer.text(f"الخصم: {receipt_data.get('discount_amount', 0):.2f}\n")
        printer.set(text_type='B')
        printer.text(f"الإجمالي: {receipt_data.get('final_amount', 0):.2f}\n")
        printer.set(text_type='normal')
        
        # Footer
        printer.set(align='center')
        printer.text("=" * 32 + "\n")
        printer.text("شكراً لزيارتك\n")
        printer.text("\n\n")
    
    def _format_receipt_commands(self, receipt_data: Dict[str, Any]) -> bytes:
        """
        تنسيق الفاتورة كأوامر ESC/POS (bytes)
        
        Args:
            receipt_data: بيانات الفاتورة
            
        Returns:
            أوامر ESC/POS كـ bytes
        """
        commands = []
        
        # ESC @ - Initialize
        commands.append(b'\x1B\x40')
        
        # ESC a 1 - Center align
        commands.append(b'\x1B\x61\x01')
        
        # Store name (Bold, Double size)
        commands.append(b'\x1B\x21\x30')  # ESC ! 0x30 = Bold + Double width + Double height
        store_name = receipt_data.get('store_name', 'المتجر').encode('utf-8')
        commands.append(store_name)
        commands.append(b'\n')
        
        # Reset formatting
        commands.append(b'\x1B\x21\x00')
        
        # Add other receipt content...
        # (يمكن إضافة المزيد من التنسيق هنا)
        
        return b''.join(commands)
    
    def open_cash_drawer(self, printer_config: Dict[str, Any]) -> bool:
        """
        فتح الدرج النقدي
        
        Args:
            printer_config: إعدادات الطابعة
            
        Returns:
            True إذا نجح
        """
        try:
            if printer_config.get('type') == PrinterType.USB.value:
                vendor_id = printer_config['vendor_id']
                product_id = printer_config['product_id']
                printer = Usb(vendor_id, product_id, 0)
                # ESC p - Pulse (open drawer)
                printer.control('ESC', 'p', m=0, t=1)
                return True
        except Exception as e:
            self.logger.error(f"❌ فشل فتح الدرج النقدي: {str(e)}")
            return False
        
        return False
