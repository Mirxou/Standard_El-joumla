#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialog modules
حوارات التطبيق
"""

# Stock management dialogs
from .adjust_stock_dialog import AdjustStockDialog
from .batch_dialog import BatchDialog
from .category_dialog import CategoryDialog
from .category_form_dialog import CategoryFormDialog
from .contacts_report_dialog import ContactsReportDialog
from .count_details_dialog import CountDetailsDialog

# Form dialogs
from .customer_form_dialog import CustomerFormDialog

# Management dialogs
from .customer_management_dialog import CustomerManagementDialog
from .encryption_dialog import EncryptionDialog
from .installment_payment_dialog import (
    InstallmentPaymentDialog,
    PaymentPlanDetailsDialog,
)
from .login_dialog import ForgotPasswordDialog, LoginDialog
from .payment_dialog import PaymentDialog
from .payment_plan_dialog import PaymentPlanDialog
from .product_dialog import ProductDialog

# Other dialogs
from .purchase_order_dialog import PurchaseOrderDialog
from .receiving_dialog import ReceivingDialog
from .safety_stock_dialog import SafetyStockDialog

# Main dialogs
from .sales_dialog import SalesDialog
from .supplier_form_dialog import SupplierFormDialog
from .supplier_management_dialog import SupplierManagementDialog
from .transfer_stock_dialog import TransferStockDialog

__all__ = [
    # Main dialogs
    "SalesDialog",
    "ProductDialog",
    "LoginDialog",
    "ForgotPasswordDialog",
    "PaymentDialog",
    "InstallmentPaymentDialog",
    "PaymentPlanDetailsDialog",
    # Stock management
    "AdjustStockDialog",
    "TransferStockDialog",
    # Form dialogs
    "CustomerFormDialog",
    "SupplierFormDialog",
    "CategoryFormDialog",
    # Management dialogs
    "CustomerManagementDialog",
    "SupplierManagementDialog",
    "CategoryDialog",
    # Other dialogs
    "PurchaseOrderDialog",
    "ReceivingDialog",
    "BatchDialog",
    "SafetyStockDialog",
    "ContactsReportDialog",
    "PaymentPlanDialog",
    "EncryptionDialog",
    "CountDetailsDialog",
]
