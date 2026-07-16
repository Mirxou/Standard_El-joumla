import logging

import serial


class HardwareService:
    """
    Manages interactions with physical hardware:
    1. Employee: Customer Displays (VFD 2x20) - Standard EPSON Protocol
    2. Ticket Printers (ESC/POS) - Future extension
    3. Cash Drawers - Future extension
    """

    def __init__(self, port="COM3", baudrate=9600):
        self.logger = logging.getLogger(__name__)
        self.port = port
        self.baudrate = baudrate
        self.serial = None

        # Try to connect on init (optional)
        self.connect()

    def connect(self):
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=1,
            )
            self.logger.info(f"✅ Hardware: Connected to Customer Display on {self.port}")
            self.clear_display()
            self.welcome_message()
            return True
        except Exception as e:
            self.logger.warning(f"⚠️ Hardware: Failed to connect to display on {self.port}: {e}")
            self.serial = None
            return False

    def send_command(self, cmd):
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(cmd)
            except Exception as e:
                self.logger.error(f"Hardware Error: {e}")

    def clear_display(self):
        # Standard EPSON Clear Command: CLR
        self.send_command(b"\x0c")

    def welcome_message(self):
        self.clear_display()
        # Line 1
        self.send_command(b"Welcome to store!")
        # Move to Line 2
        self.send_command(b"\x0d\x0a")
        self.send_command(b"    EL-joumLa ERP    ")

    def show_price(self, item_name, price):
        """
        Show item and price on 2 lines
        Line 1: Item Name (truncated 20 chars)
        Line 2: Price (Aligned Right)
        """
        self.clear_display()

        # Line 1: Item
        name_bytes = item_name[:20].encode("ascii", "replace")
        self.send_command(name_bytes)

        # Line 2: Price
        self.send_command(b"\x0d\x0a")  # New Line
        price_str = f"Total: {price:,.2f} DA"
        # Pad left to align right on 20 chars display
        padding = 20 - len(price_str)
        if padding > 0:
            self.send_command(b" " * padding)
        self.send_command(price_str.encode("ascii", "replace"))

    def close(self):
        if self.serial:
            self.serial.close()
