#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialog modules
حوارات التطبيق
"""

# Main dialogs
from .sales_dialog import SalesDialog
from .product_dialog import ProductDialog
from .login_dialog import LoginDialog, ForgotPasswordDialog
from .payment_dialog import PaymentDialog
from .installment_payment_dialog import InstallmentPaymentDialog, PaymentPlanDetailsDialog

# Stock management dialogs
from .adjust_stock_dialog import AdjustStockDialog
from .transfer_stock_dialog import TransferStockDialog

# Form dialogs
from .customer_form_dialog import CustomerFormDialog
from .supplier_form_dialog import SupplierFormDialog
from .category_form_dialog import CategoryFormDialog

# Management dialogs
from .customer_management_dialog import CustomerManagementDialog
from .supplier_management_dialog import SupplierManagementDialog
from .category_dialog import CategoryDialog

# Other dialogs
from .purchase_order_dialog import PurchaseOrderDialog
from .receiving_dialog import ReceivingDialog
from .batch_dialog import BatchDialog
from .safety_stock_dialog import SafetyStockDialog
from .contacts_report_dialog import ContactsReportDialog
from .payment_plan_dialog import PaymentPlanDialog
from .theme_selector_dialog import ThemeSelectorDialog
from .encryption_dialog import EncryptionDialog
from .count_details_dialog import CountDetailsDialog

__all__ = [
    # Main dialogs
    'SalesDialog',
    'ProductDialog',
    'LoginDialog',
    'ForgotPasswordDialog',
    'PaymentDialog',
    'InstallmentPaymentDialog',
    'PaymentPlanDetailsDialog',
    
    # Stock management
    'AdjustStockDialog',
    'TransferStockDialog',
    
    # Form dialogs
    'CustomerFormDialog',
    'SupplierFormDialog',
    'CategoryFormDialog',
    
    # Management dialogs
    'CustomerManagementDialog',
    'SupplierManagementDialog',
    'CategoryDialog',
    
    # Other dialogs
    'PurchaseOrderDialog',
    'ReceivingDialog',
    'BatchDialog',
    'SafetyStockDialog',
    'ContactsReportDialog',
    'PaymentPlanDialog',
    'ThemeSelectorDialog',
    'EncryptionDialog',
    'CountDetailsDialog',
]
