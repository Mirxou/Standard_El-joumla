#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Window Manager - مدير النوافذ المركزي (Minimal & Clean Edition)
Centralized Window Management System

نسخة بسيطة واحترافية:
- تسجيل النوافذ
- فتح/إغلاق
- singleton vs multiple
- weakrefs لمنع memory leaks
- QSettings آمن
- hooks system
- لا إعادة كتابة closeEvent
"""

from __future__ import annotations

import weakref
import json
import logging
from typing import Dict, List, Optional, Type, Any, Callable
from collections import defaultdict
from functools import partial

from PySide6.QtCore import QObject, QSettings, Slot
from PySide6.QtWidgets import QWidget

logger = logging.getLogger("window_manager")


class WindowConfig:
    """
    Minimal config holder for a registered window.
    
    window_key: unique id string (e.g. "products")
    window_class: subclass of QWidget
    singleton: True => only one live instance tracked (by key)
    init_kwargs: default kwargs when creating
    """
    def __init__(
        self,
        window_key: str,
        window_class: Type[QWidget],
        title: Optional[str] = None,
        singleton: bool = True,
        init_kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.window_key = window_key
        self.window_class = window_class
        self.title = title or window_key
        self.singleton = singleton
        self.init_kwargs = init_kwargs or {}


class WindowManager(QObject):
    """
    Central Window Manager for a Desktop (PySide6) ERP.
    
    - register_window
    - open_window / close_window / close_all
    - supports singleton and multiple instances
    - tracks via weakrefs to avoid memory leaks
    - saves geometry/state into QSettings
    - provides hooks lists: on_before_open, on_after_open, on_before_close, on_after_close
    """

    def __init__(self, organization: str = "LogicalVersion", appname: str = "ERP", parent: Optional[QObject] = None):
        super().__init__(parent)
        self._configs: Dict[str, WindowConfig] = {}
        # dict of key -> list of weakrefs to QWidget
        self._open_refs: Dict[str, List[weakref.ref]] = defaultdict(list)
        self.settings = QSettings(organization, appname)

        # hooks: lists of callables. each callable receives (window_key, instance) where instance may be None on before_open
        self.on_before_open: List[Callable[[str, Optional[QWidget], Dict[str, Any]], None]] = []
        self.on_after_open: List[Callable[[str, QWidget], None]] = []
        self.on_before_close: List[Callable[[str, QWidget], None]] = []
        self.on_after_close: List[Callable[[str], None]] = []

        # Signals (Qt Signals for better integration)
        # Note: These are optional and can be used by subclasses or wrappers
        # Base WindowManager doesn't inherit QObject signals, but can be extended
        
        # basic logger
        self.logger = logger

    # ----- registration -----
    def register_window(self, *,
                        window_key: str,
                        window_class: Type[QWidget],
                        title: Optional[str] = None,
                        singleton: bool = True,
                        init_kwargs: Optional[Dict[str, Any]] = None) -> None:
        if not isinstance(window_key, str) or not window_key:
            raise ValueError("window_key must be a non-empty string")
        if not isinstance(window_class, type) or not issubclass(window_class, QWidget):
            raise TypeError("window_class must be a QWidget subclass")

        cfg = WindowConfig(window_key=window_key, window_class=window_class, title=title, singleton=singleton, init_kwargs=init_kwargs)
        self._configs[window_key] = cfg
        self.logger.debug(f"Registered window: {window_key} -> {window_class.__name__}")

    # ----- internal helpers -----
    def _clean_dead_refs(self, key: str) -> None:
        refs = self._open_refs.get(key, [])
        alive = [r for r in refs if r() is not None]
        if len(alive) != len(refs):
            self._open_refs[key] = alive

    def _make_on_destroyed(self, window_key: str, wref: weakref.ref):
        # will be called when the QObject emits destroyed
        def _handler(obj=None):
            inst = wref()
            try:
                if inst:
                    # call before_close hooks
                    for h in self.on_before_close:
                        try:
                            h(window_key, inst)
                        except Exception:
                            self.logger.exception("on_before_close hook failed")
                # remove the weakref from tracking
                self._open_refs[window_key] = [r for r in self._open_refs.get(window_key, []) if r is not wref and r() is not None]
                # call after_close hooks
                for h in self.on_after_close:
                    try:
                        h(window_key)
                    except Exception:
                        self.logger.exception("on_after_close hook failed")
            except Exception:
                self.logger.exception("error handling destroyed for %s", window_key)
        return _handler

    # ----- persistence (geometry/state) -----
    def _save_geometry(self, window_key: str, instance: QWidget) -> None:
        try:
            # إذا كانت النافذة maximized، احفظ normalGeometry بدلاً من geometry
            if instance.isMaximized():
                # استعادة مؤقتة للحصول على الحجم الطبيعي
                instance.showNormal()
                # معالجة الأحداث للتأكد من أن التغيير تم
                from PySide6.QtWidgets import QApplication
                QApplication.processEvents()
                geom = instance.geometry()
                instance.showMaximized()  # إعادة maximized
            else:
                geom = instance.geometry()
            
            data = json.dumps({
                "x": geom.x(),
                "y": geom.y(),
                "w": geom.width(),
                "h": geom.height(),
                "maximized": bool(instance.isMaximized())
            })
            self.settings.setValue(f"{window_key}/geometry", data)
            self.settings.sync()
        except Exception:
            self.logger.exception("Failed to save geometry for %s", window_key)

    def _restore_geometry(self, window_key: str, instance: QWidget) -> None:
        try:
            raw = self.settings.value(f"{window_key}/geometry", "")
            if not raw:
                return
            obj = json.loads(raw)
            
            # التحقق من حالة maximized أولاً
            if obj.get("maximized"):
                # إذا كانت maximized، احفظ الحجم الطبيعي أولاً ثم كبّر
                x = max(0, int(obj.get("x", 100)))
                y = max(0, int(obj.get("y", 100)))
                w = max(200, int(obj.get("w", 800)))
                h = max(100, int(obj.get("h", 600)))
                instance.setGeometry(x, y, w, h)
                # معالجة الأحداث للتأكد من التطبيق
                from PySide6.QtWidgets import QApplication
                QApplication.processEvents()
                instance.showMaximized()
            else:
                x = max(0, int(obj.get("x", 100)))
                y = max(0, int(obj.get("y", 100)))
                w = max(200, int(obj.get("w", 800)))
                h = max(100, int(obj.get("h", 600)))
                instance.setGeometry(x, y, w, h)
        except Exception:
            self.logger.warning("Failed to restore geometry for %s (using defaults)", window_key)

    # ----- open/close -----
    def open_window(self, window_key: str, parent: Optional[QWidget] = None, **override_kwargs) -> Optional[QWidget]:
        """
        Open (or show existing) window.
        returns the QWidget instance or None on failure.
        """
        cfg = self._configs.get(window_key)
        if not cfg:
            self.logger.error("Window not registered: %s", window_key)
            return None

        # clean dead refs first
        self._clean_dead_refs(window_key)

        # if singleton and an alive instance exists -> show & raise it
        if cfg.singleton:
            refs = self._open_refs.get(window_key, [])
            for r in refs:
                inst = r()
                if inst is not None:
                    try:
                        inst.show()
                        inst.raise_()
                        inst.activateWindow()
                        self.logger.debug("Reusing existing singleton instance for %s", window_key)
                        return inst
                    except Exception:
                        # continue to try others if any
                        self.logger.exception("Error re-activating instance for %s", window_key)

        # call before-open hooks
        for h in self.on_before_open:
            try:
                h(window_key, None, {**cfg.init_kwargs, **override_kwargs})
            except Exception:
                self.logger.exception("on_before_open hook failed")

        # create new instance
        try:
            kwargs = dict(cfg.init_kwargs)
            kwargs.update(override_kwargs)
            if parent is not None:
                kwargs.setdefault("parent", parent)

            inst = cfg.window_class(**kwargs)  # may raise
            if cfg.title:
                try:
                    inst.setWindowTitle(cfg.title)
                except Exception:
                    pass

            # restore geometry/state if any
            self._restore_geometry(window_key, inst)

            # track via weakref
            wref = weakref.ref(inst)
            self._open_refs[window_key].append(wref)

            # connect destroyed to cleanup handler
            inst.destroyed.connect(self._make_on_destroyed(window_key, wref))

            # connect close/save hook if we can (safe)
            # do NOT override closeEvent; instead connect to destroyed & rely on callers to call deleteLater() on close if needed

            # call after-open hooks
            for h in self.on_after_open:
                try:
                    h(window_key, inst)
                except Exception:
                    self.logger.exception("on_after_open hook failed")

            # استعادة الحالة المتقدمة (تبويبات، فلاتر، جداول)
            # إذا كانت النافذة تدعم WindowStateManager
            try:
                from src.core.window_state_manager import WindowStateManager
                state_manager = WindowStateManager(
                    organization=self.settings.organizationName(),
                    appname=self.settings.applicationName(),
                    parent=self
                )
                
                # استعادة التبويبات
                if hasattr(inst, 'tab_widgets'):
                    for tab_key, tab_widget in inst.tab_widgets.items():
                        state_manager.restore_tab_state(window_key, tab_widget, tab_key)
                
                # استعادة الفلاتر
                if hasattr(inst, 'filter_widgets'):
                    for filter_key, filter_dict in inst.filter_widgets.items():
                        state_manager.restore_filter_state(window_key, filter_dict, filter_key)
                
                # استعادة الجداول
                if hasattr(inst, 'table_widgets'):
                    for table_key, table_widget in inst.table_widgets.items():
                        state_manager.restore_table_state(window_key, table_widget, table_key)
            except Exception:
                # لا مشكلة إذا لم تكن النافذة تدعم الحالة المتقدمة
                pass

            # show it
            try:
                inst.show()
                inst.raise_()
                inst.activateWindow()
                
                # Performance optimization: process events once after showing
                # This ensures the window is rendered before returning
                from PySide6.QtWidgets import QApplication
                QApplication.processEvents()
            except Exception:
                self.logger.exception("opening/showing window failed for %s", window_key)

            return inst

        except Exception as e:
            self.logger.exception("Failed to create window %s: %s", window_key, e)
            return None

    def close_window(self, window_key: str) -> bool:
        """
        Close all instances for key (or the singleton). Returns True if any were closed.
        """
        self._clean_dead_refs(window_key)
        refs = list(self._open_refs.get(window_key, []))
        closed_any = False
        for r in refs:
            inst = r()
            if inst is None:
                continue
            try:
                # try to save geometry and advanced state before closing
                # تأكد من أن النافذة مرئية قبل حفظ الحالة
                if inst.isVisible():
                    try:
                        self._save_geometry(window_key, inst)
                        
                        # حفظ الحالة المتقدمة (تبويبات، فلاتر، جداول)
                        # إذا كانت النافذة تدعم WindowStateManager
                        try:
                            from src.core.window_state_manager import WindowStateManager
                            state_manager = WindowStateManager(
                                organization=self.settings.organizationName(),
                                appname=self.settings.applicationName(),
                                parent=self
                            )
                            
                            # حفظ التبويبات
                            if hasattr(inst, 'tab_widgets'):
                                for tab_key, tab_widget in inst.tab_widgets.items():
                                    state_manager.save_tab_state(window_key, tab_widget, tab_key)
                            
                            # حفظ الفلاتر
                            if hasattr(inst, 'filter_widgets'):
                                for filter_key, filter_dict in inst.filter_widgets.items():
                                    state_manager.save_filter_state(window_key, filter_dict, filter_key)
                            
                            # حفظ الجداول
                            if hasattr(inst, 'table_widgets'):
                                for table_key, table_widget in inst.table_widgets.items():
                                    state_manager.save_table_state(window_key, table_widget, table_key)
                        except Exception:
                            # لا مشكلة إذا لم تكن النافذة تدعم الحالة المتقدمة
                            pass
                    except Exception:
                        self.logger.exception("Failed to save state for %s", window_key)
                
                inst.close()
                # ensure deletion
                try:
                    inst.deleteLater()
                except Exception:
                    pass
                closed_any = True
            except Exception:
                self.logger.exception("Error closing instance for %s", window_key)
        return closed_any

    def close_all(self) -> None:
        for key in list(self._open_refs.keys()):
            self.close_window(key)

    def get_open_instances(self, window_key: str) -> List[QWidget]:
        self._clean_dead_refs(window_key)
        return [r() for r in self._open_refs.get(window_key, []) if r() is not None]

    def is_open(self, window_key: str) -> bool:
        self._clean_dead_refs(window_key)
        return any(r() is not None for r in self._open_refs.get(window_key, []))

    # helper to auto-register windows by scanning modules (optional)
    def auto_register(self, module_objects: List[Any]) -> None:
        """
        Accepts a list of classes/objects from your windows module.
        Each class should expose:
            window_key: str
            window_singleton: bool (optional, defaults True)
        and be QWidget subclass.
        """
        for obj in module_objects:
            try:
                if isinstance(obj, type) and issubclass(obj, QWidget) and hasattr(obj, "window_key"):
                    key = getattr(obj, "window_key")
                    singleton = getattr(obj, "window_singleton", True)
                    title = getattr(obj, "window_title", None)
                    self.register_window(window_key=key, window_class=obj, title=title, singleton=singleton)
            except Exception:
                self.logger.exception("auto_register error for %r", obj)

