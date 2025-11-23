from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QTextEdit,
    QMessageBox, QListWidget, QLabel, QCheckBox
)
from PySide6.QtCore import Qt
from datetime import datetime, timedelta
import json

from ...services.rbac_service import RBACService
from ...core.database_manager import DatabaseManager


class RolesManagerWidget(QWidget):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.rbac = RBACService(db)
        self.setWindowTitle("إدارة الأدوار والصلاحيات")
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # جدول الأدوار
        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["الدور", "الصلاحيات", "المستخدمين", "الإجراءات"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        
        # أزرار التحكم
        btn_layout = QHBoxLayout()
        
        self.btn_refresh = QPushButton("تحديث", self)
        self.btn_refresh.clicked.connect(self.refresh)
        btn_layout.addWidget(self.btn_refresh)
        
        self.btn_add_role = QPushButton("إضافة دور جديد", self)
        self.btn_add_role.clicked.connect(self.add_role_dialog)
        btn_layout.addWidget(self.btn_add_role)
        
        self.btn_bulk_assign = QPushButton("تعيين جماعي", self)
        self.btn_bulk_assign.clicked.connect(self.bulk_assign_dialog)
        btn_layout.addWidget(self.btn_bulk_assign)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def refresh(self):
        try:
            roles = self.rbac.list_roles()
            self.table.setRowCount(len(roles))
            for i, r in enumerate(roles):
                role_name = str(r.get('name') or r.get('role_name', ''))
                self.table.setItem(i, 0, QTableWidgetItem(role_name))
                
                perms = ", ".join(r.get('permissions', [])) if isinstance(r.get('permissions'), list) else str(r.get('permissions', ''))
                self.table.setItem(i, 1, QTableWidgetItem(perms))
                
                # عدد المستخدمين بهذا الدور
                user_count = self._get_users_count_for_role(r.get('id') or r.get('role_id'))
                self.table.setItem(i, 2, QTableWidgetItem(str(user_count)))
                
                # أزرار الإجراءات
                actions_btn = QPushButton("تعديل")
                actions_btn.clicked.connect(lambda checked, role=r: self.edit_role_dialog(role))
                self.table.setCellWidget(i, 3, actions_btn)
        except Exception as e:
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("خطأ"))
            self.table.setItem(0, 1, QTableWidgetItem(str(e)))
    
    def _get_users_count_for_role(self, role_id) -> int:
        """الحصول على عدد المستخدمين بدور معين"""
        try:
            result = self.db.execute_query(
                "SELECT COUNT(*) as count FROM user_roles WHERE role_id = ?",
                (role_id,)
            )
            return result[0]['count'] if result else 0
        except Exception:
            return 0
    
    def add_role_dialog(self):
        """حوار إضافة دور جديد"""
        dialog = QDialog(self)
        dialog.setWindowTitle("إضافة دور جديد")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        name_edit = QLineEdit()
        layout.addRow("اسم الدور:", name_edit)
        
        perms_edit = QTextEdit()
        perms_edit.setPlaceholderText("أدخل الصلاحيات، واحدة في كل سطر")
        layout.addRow("الصلاحيات:", perms_edit)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("حفظ")
        btn_cancel = QPushButton("إلغاء")
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addRow(btn_layout)
        
        def save_role():
            name = name_edit.text().strip()
            perms_text = perms_edit.toPlainText().strip()
            permissions = [p.strip() for p in perms_text.split('\n') if p.strip()]
            
            if not name:
                QMessageBox.warning(dialog, "خطأ", "الرجاء إدخال اسم الدور")
                return
            
            try:
                self.rbac.create_role(name, permissions)
                QMessageBox.information(dialog, "نجاح", "تم إضافة الدور بنجاح")
                dialog.accept()
                self.refresh()
            except Exception as e:
                QMessageBox.critical(dialog, "خطأ", f"فشل إضافة الدور: {str(e)}")
        
        btn_save.clicked.connect(save_role)
        btn_cancel.clicked.connect(dialog.reject)
        
        dialog.exec()
    
    def edit_role_dialog(self, role):
        """حوار تعديل دور موجود"""
        dialog = QDialog(self)
        dialog.setWindowTitle("تعديل دور")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        name_edit = QLineEdit(str(role.get('name') or role.get('role_name', '')))
        name_edit.setReadOnly(True)
        layout.addRow("اسم الدور:", name_edit)
        
        current_perms = role.get('permissions', [])
        if isinstance(current_perms, str):
            try:
                current_perms = json.loads(current_perms)
            except:
                current_perms = []
        
        perms_edit = QTextEdit()
        perms_edit.setPlainText('\n'.join(current_perms))
        layout.addRow("الصلاحيات:", perms_edit)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("حفظ")
        btn_delete = QPushButton("حذف الدور")
        btn_cancel = QPushButton("إلغاء")
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_delete)
        btn_layout.addWidget(btn_cancel)
        layout.addRow(btn_layout)
        
        def save_changes():
            perms_text = perms_edit.toPlainText().strip()
            permissions = [p.strip() for p in perms_text.split('\n') if p.strip()]
            
            try:
                role_id = role.get('id') or role.get('role_id')
                self.rbac.update_role(role_id, permissions=permissions)
                QMessageBox.information(dialog, "نجاح", "تم تحديث الدور بنجاح")
                dialog.accept()
                self.refresh()
            except Exception as e:
                QMessageBox.critical(dialog, "خطأ", f"فشل تحديث الدور: {str(e)}")
        
        def delete_role():
            reply = QMessageBox.question(
                dialog, "تأكيد الحذف",
                "هل أنت متأكد من حذف هذا الدور؟",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    role_id = role.get('id') or role.get('role_id')
                    self.rbac.delete_role(role_id)
                    QMessageBox.information(dialog, "نجاح", "تم حذف الدور بنجاح")
                    dialog.accept()
                    self.refresh()
                except Exception as e:
                    QMessageBox.critical(dialog, "خطأ", f"فشل حذف الدور: {str(e)}")
        
        btn_save.clicked.connect(save_changes)
        btn_delete.clicked.connect(delete_role)
        btn_cancel.clicked.connect(dialog.reject)
        
        dialog.exec()
    
    def bulk_assign_dialog(self):
        """حوار التعيين الجماعي للأدوار"""
        dialog = QDialog(self)
        dialog.setWindowTitle("تعيين جماعي للأدوار")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        # اختيار الدور
        layout.addWidget(QLabel("اختر الدور:"))
        role_list = QListWidget()
        try:
            roles = self.rbac.list_roles()
            for r in roles:
                role_name = str(r.get('name') or r.get('role_name', ''))
                role_list.addItem(role_name)
                role_list.item(role_list.count() - 1).setData(Qt.UserRole, r)
        except Exception:
            pass
        layout.addWidget(role_list)
        
        # اختيار المستخدمين
        layout.addWidget(QLabel("اختر المستخدمين:"))
        user_list = QListWidget()
        user_list.setSelectionMode(QListWidget.MultiSelection)
        try:
            users = self.db.execute_query("SELECT id, username, full_name FROM users WHERE is_active = 1")
            for u in users:
                display_name = f"{u.get('username')} - {u.get('full_name', '')}"
                user_list.addItem(display_name)
                user_list.item(user_list.count() - 1).setData(Qt.UserRole, u['id'])
        except Exception:
            pass
        layout.addWidget(user_list)
        
        # أزرار التحكم
        btn_layout = QHBoxLayout()
        btn_assign = QPushButton("تعيين")
        btn_cancel = QPushButton("إلغاء")
        btn_layout.addWidget(btn_assign)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        def assign_roles():
            selected_role = role_list.currentItem()
            if not selected_role:
                QMessageBox.warning(dialog, "خطأ", "الرجاء اختيار دور")
                return
            
            selected_users = user_list.selectedItems()
            if not selected_users:
                QMessageBox.warning(dialog, "خطأ", "الرجاء اختيار مستخدم واحد على الأقل")
                return
            
            role = selected_role.data(Qt.UserRole)
            role_id = role.get('id') or role.get('role_id')
            
            success_count = 0
            for user_item in selected_users:
                user_id = user_item.data(Qt.UserRole)
                try:
                    self.rbac.assign_role(user_id, role_id)
                    success_count += 1
                except Exception:
                    pass
            
            QMessageBox.information(
                dialog, "نجاح",
                f"تم تعيين الدور لـ {success_count} من {len(selected_users)} مستخدم"
            )
            dialog.accept()
        
        btn_assign.clicked.connect(assign_roles)
        btn_cancel.clicked.connect(dialog.reject)
        
        dialog.exec()
