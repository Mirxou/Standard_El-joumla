import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Printing Service
Handles communication with receipt printers (ESC/POS).
"""

try:
    import usb.core
    import usb.util
    from escpos.printer import Usb

    _USB_AVAILABLE = True
except ImportError:
    _USB_AVAILABLE = False


class PrintingService:
    def __init__(self, logger=None):
        self.logger = logger
        self.can_discover_usb = _USB_AVAILABLE
        self._usb_failure_reason = None
        if not _USB_AVAILABLE and logger:
            logger.warning("USB printing libraries not available (usb, escpos). USB printer features disabled.")

    def discover_usb_printers(self):
        """
        Discovers connected USB ESC/POS printers.
        Returns a list of dictionaries, each containing vendor and product IDs.
        """
        if not _USB_AVAILABLE or not self.can_discover_usb:
            if self.logger:
                self.logger.info("USB printer discovery disabled on this system.")
            return []

        printers = []
        try:
            # Find all devices that could be printers
            devices = usb.core.find(find_all=True)
            for dev in devices:
                # A common heuristic for receipt printers is to check for a specific interface class
                if dev.bDeviceClass == 7:  # 7 is the class for Printers
                    printers.append(
                        {
                            "vendor_id": dev.idVendor,
                            "product_id": dev.idProduct,
                            "name": usb.util.get_string(dev, dev.iProduct),
                        }
                    )
                else:
                    # Look for specific endpoint configurations as another heuristic
                    for cfg in dev:
                        for intf in cfg:
                            if intf.bInterfaceClass == 7:
                                printers.append(
                                    {
                                        "vendor_id": dev.idVendor,
                                        "product_id": dev.idProduct,
                                        "name": usb.util.get_string(dev, dev.iProduct),
                                    }
                                )
                                break
        except Exception as e:
            self._usb_failure_reason = str(e)
            self.can_discover_usb = False
            if self.logger:
                if "No backend available" in self._usb_failure_reason:
                    self.logger.warning("USB backend not available; disabling printer discovery.")
                else:
                    self.logger.error(f"Error discovering USB printers: {self._usb_failure_reason}")
            return []

        # Deduplicate
        unique_printers = []
        seen = set()
        for p in printers:
            identifier = (p["vendor_id"], p["product_id"])
            if identifier not in seen:
                unique_printers.append(p)
                seen.add(identifier)

        return unique_printers

    def print_receipt(self, printer_config: dict, sale_data: dict):
        """
        Prints a formatted receipt to the specified printer.

        :param printer_config: A dict with 'vendor_id' and 'product_id'.
        :param sale_data: A dict containing receipt information.
        """
        if not _USB_AVAILABLE:
            if self.logger:
                self.logger.error("Cannot print: USB libraries not installed.")
            return False, "USB libraries not available"

        try:
            p = Usb(printer_config["vendor_id"], printer_config["product_id"], 0)

            p.set(align="center", text_type="B")
            p.text("Your Store Name\n")
            p.text("---------------\n")
            p.set(align="left")

            for item in sale_data.get("items", []):
                name = item.get("name", "N/A")
                qty = item.get("quantity", 0)
                price = item.get("price", 0.0)
                line = f"{name:<20} {qty} x {price:.2f}\n"
                p.text(line)

            p.text("---------------\n")
            p.set(align="right")
            p.text(f"Total: {sale_data.get('total', 0.0):.2f}\n")

            p.cut()
            p.close()

            if self.logger:
                self.logger.info(f"Receipt printed successfully to {printer_config}.")
            return True, "Success"
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to print receipt: {e}")
            return False, str(e)

    def open_cash_drawer(self, printer_config: dict):
        """
        Sends a command to open the cash drawer connected to the printer.
        """
        if not _USB_AVAILABLE:
            if self.logger:
                self.logger.error("Cannot open cash drawer: USB libraries not installed.")
            return False, "USB libraries not available"

        try:
            p = Usb(printer_config["vendor_id"], printer_config["product_id"], 0)
            p.cashdraw(2)  # Sends pulse to pin 2
            p.close()
            if self.logger:
                self.logger.info(f"Cash drawer pulse sent to {printer_config}.")
            return True, "Success"
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to open cash drawer: {e}")
            return False, str(e)


if __name__ == "__main__":
    # For testing purposes
    service = PrintingService()
    print("Discovering printers...")
    found_printers = service.discover_usb_printers()
    if found_printers:
        print("Found printers:")
        for pr in found_printers:
            print(f"  - Name: {pr['name']}, VID: {hex(pr['vendor_id'])}, PID: {hex(pr['product_id'])}")
    else:
        print("No USB printers found.")
