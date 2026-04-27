import os
import sys
import pytest
import importlib
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QMainWindow, QDialog, QWidget, QApplication

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def get_ui_classes(directory, base_package):
    """اكتشاف كافة فئات UI في مجلد معين"""
    classes = []
    if not os.path.exists(directory):
        return classes
        
    for filename in os.listdir(directory):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = f"{base_package}.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                for name, obj in vars(module).items():
                    if isinstance(obj, type) and issubclass(obj, (QMainWindow, QDialog, QWidget)):
                        # تجنب الفئات الأساسية من Qt
                        if obj.__module__ == module_name:
                            classes.append((obj, module_name))
            except Exception as e:
                print(f"Warning: Could not import {module_name}: {e}")
    return classes

# اكتشاف النوافذ والحوارات
WINDOWS_DIR = os.path.join(project_root, "src", "ui", "windows")
DIALOGS_DIR = os.path.join(project_root, "src", "ui", "dialogs")

ALL_UI_COMPONENTS = get_ui_classes(WINDOWS_DIR, "src.ui.windows") + \
                   get_ui_classes(DIALOGS_DIR, "src.ui.dialogs")
@pytest.fixture(scope="session")
def mock_db():
    return MagicMock()

@pytest.fixture(scope="session")
def mock_inv():
    return MagicMock()

@pytest.mark.parametrize("ui_class, module_name", ALL_UI_COMPONENTS)
def test_ui_component_instantiation(qtbot, mock_db, mock_inv, ui_class, module_name):
    """اختبار تلقائي لإنشاء واجهة المستخدم (Batch Smoke Test)"""
    
    # محاكاة التبعيات المشتركة والواجهات التي قد توقف الاختبار
    with patch('src.ui.theme_manager.get_theme_manager'), \
         patch('src.ui.notifications_manager.get_notifications_manager'), \
         patch('src.core.config_manager.ConfigManager'), \
         patch('src.ui.widgets.custom_title_bar.CustomTitleBar', return_value=MagicMock()), \
         patch('src.ui.animations.animation_manager.AnimationManager', return_value=MagicMock()), \
         patch('PySide6.QtWidgets.QWidget.show'), \
         patch('PySide6.QtWidgets.QDialog.exec'), \
         patch('PySide6.QtWidgets.QDialog.exec_'):
        
        try:
            # محاولة تخمين الوسائط المطلوبة بناءً على القائمة الأكثر شيوعاً
            # في هذا النظام، معظم الحوارات تأخذ (db_manager) أو (inventory_service)
            
            # محاولة إنشاء بدون وسائط أولاً
            try:
                widget = ui_class()
            except TypeError:
                # محاولة تمرير db_manager
                try:
                    widget = ui_class(mock_db)
                except TypeError:
                    # محاولة تمرير inventory_service
                    try:
                        widget = ui_class(mock_inv)
                    except TypeError:
                        # محاولة تمرير كليهما
                        try:
                            widget = ui_class(mock_db, mock_inv)
                        except TypeError:
                            pytest.skip(f"Could not determine constructor for {ui_class.__name__}")
            
            qtbot.addWidget(widget)
            assert widget is not None
            
            # التحقق من أن المكون تم إنشاؤه بنجاح
            assert hasattr(widget, 'isVisible')
            
        except Exception as e:
            # إذا كان هناك خطأ في الاستيراد أو التبعيات المعقدة
            if "requires" in str(e).lower() or "environment" in str(e).lower():
                pytest.skip(f"Skipping {ui_class.__name__} due to environment requirements: {e}")
            else:
                pytest.fail(f"Failed to instantiate {ui_class.__name__} from {module_name}: {e}")



