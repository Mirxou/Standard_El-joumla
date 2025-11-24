import pytest
from unittest.mock import patch, MagicMock

# Mock the PySide6 QSettings before it's used
from PySide6.QtCore import QSettings
class MockQSettings:
    def __init__(self, *args):
        self._data = {}
    def value(self, key, defaultValue=None, type=None):
        return self._data.get(key, defaultValue)
    def setValue(self, key, value):
        self._data[key] = value
QSettings = MockQSettings

from src.services.printing_service import PrintingService

@pytest.fixture
def printing_service():
    """Pytest fixture for the PrintingService."""
    logger = MagicMock()
    service = PrintingService(logger)
    return service

@patch('usb.core.find')
def test_discover_usb_printers(mock_usb_find, printing_service):
    """Test discovery of USB printers."""
    print("\nTesting USB printer discovery...")
    # Create a mock device that looks like a printer
    mock_dev = MagicMock()
    mock_dev.bDeviceClass = 7 # Printer class
    mock_dev.idVendor = 0x04b8
    mock_dev.idProduct = 0x0202
    mock_dev.iProduct = 5 # Index of product string descriptor
    
    with patch('usb.util.get_string', return_value="TM-T20II") as mock_get_string:
        mock_usb_find.return_value = [mock_dev]
        
        printers = printing_service.discover_usb_printers()
        
        assert len(printers) == 1
        assert printers[0]['name'] == "TM-T20II"
        assert printers[0]['vendor_id'] == 0x04b8
        assert printers[0]['product_id'] == 0x0202
        print("  ✅ Printer discovery successful.")

@patch('src.services.printing_service._USB_AVAILABLE', True)
@patch('src.services.printing_service.Usb')
def test_print_receipt(mock_usb_printer, printing_service):
    """Test the receipt printing logic."""
    print("\nTesting receipt printing...")
    mock_instance = mock_usb_printer.return_value
    
    printer_config = {'vendor_id': 0x04b8, 'product_id': 0x0202}
    sale_data = {
        'total': 50.50,
        'items': [
            {'name': 'Item A', 'quantity': 2, 'price': 10.00},
            {'name': 'Item B', 'quantity': 1, 'price': 30.50},
        ]
    }
    
    result = printing_service.print_receipt(printer_config, sale_data)
    
    # الدالة تعيد tuple (success, message)
    assert isinstance(result, tuple), "Expected tuple return value"
    success, msg = result
    assert success is True
    assert msg == "Success"
    mock_usb_printer.assert_called_with(printer_config['vendor_id'], printer_config['product_id'], 0)
    mock_instance.set.assert_any_call(align='center', text_type='B')
    mock_instance.text.assert_any_call("Your Store Name\n")
    mock_instance.text.assert_any_call(f"Total: {sale_data['total']:.2f}\n")
    mock_instance.cut.assert_called_once()
    mock_instance.close.assert_called_once()
    print("  ✅ Receipt printing logic verified.")

@patch('src.services.printing_service._USB_AVAILABLE', True)
@patch('src.services.printing_service.Usb')
def test_open_cash_drawer(mock_usb_printer, printing_service):
    """Test the cash drawer opening logic."""
    print("\nTesting cash drawer opening...")
    mock_instance = mock_usb_printer.return_value
    
    printer_config = {'vendor_id': 0x04b8, 'product_id': 0x0202}
    
    result = printing_service.open_cash_drawer(printer_config)
    
    # الدالة تعيد tuple (success, message)
    assert isinstance(result, tuple), "Expected tuple return value"
    success, msg = result
    assert success is True
    assert msg == "Success"
    mock_usb_printer.assert_called_with(printer_config['vendor_id'], printer_config['product_id'], 0)
    mock_instance.cashdraw.assert_called_with(2)
    mock_instance.close.assert_called_once()
    print("  ✅ Cash drawer logic verified.")

