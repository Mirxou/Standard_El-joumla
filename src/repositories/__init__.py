#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repositories Package
طبقة Repository Pattern للوصول إلى قاعدة البيانات المحلية
"""

from .base_repository import BaseRepository
from .customer_repository import CustomerRepository
from .product_repository import ProductRepository
from .sale_repository import SaleRepository

__all__ = [
    "BaseRepository",
    "ProductRepository",
    "SaleRepository",
    "CustomerRepository",
]
