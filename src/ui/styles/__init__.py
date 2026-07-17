#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI Styles Module — Standard El-Joumla ERP
أنماط الواجهة الحديثة - Royal Dark v2.0
"""

from .icon_loader import IconLoader, get_icon_loader
from .design_tokens import (
    Colors,
    Spacing,
    Radius,
    Typography,
    Shadows,
    Transitions,
    C, S, R, T, SH, TR,
    qss,
)

__all__ = [
    # Icon loader
    "IconLoader",
    "get_icon_loader",
    # Design token classes
    "Colors",
    "Spacing",
    "Radius",
    "Typography",
    "Shadows",
    "Transitions",
    # Design token singletons
    "C",
    "S",
    "R",
    "T",
    "SH",
    "TR",
    # QSS helper
    "qss",
]