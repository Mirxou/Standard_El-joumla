#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة إدارة المستخدمين
User Management Dialog — يتيح عرض وإضافة وتعديل وحذف المستخدمين وإدارة كلمات المرور
"""

import secrets
import string
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from src.models.user import User, UserRole, UserManager


# ──────────────────────────────────────────────────────────
#  Form dialog for creating / editing a user
# ──────────────────────────────────────────────────────────
class UserFormDialog(QDialog):
    """نموذج إضافة / تعديل مستخدم"""

    def __init__(self, db_manager, user: User = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.editing_user = user  # None ⇒ add mode, User ⇒ edit mode

        self.setWindowTitle("تعديل مستخدم" if user else "إضافة مستخدم جديد")
        self.setMinimumWidth(460)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self._build_ui()

        if user:
            self._populate(user)

    # ── UI construction ────────────────────────────────────
    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        form_group = QGroupBox("بيانات المستخدم")
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(12, 18, 12, 12)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("مثال: ahmed")
        form_layout.addRow("اسم المستخدم *:", self.username_input)

        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("مثال: أحمد محمد")
        form_layout.addRow("الاسم الكامل:", self.full_name_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("example@mail.com")
        form_layout.addRow("البريد الإلكتروني:", self.email_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("05xxxxxxxx")
        form_layout.addRow("الهاتف:", self.phone_input)

        self.role_combo = QComboBox()
        for role in UserRole:
            self.role_combo.addItem(role.value, role.value)
        form_layout.addRow("الدور:", self.role_combo)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("كلمة المرور")
        form_layout.addRow("كلمة المرور *:", self.password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("تأكيد كلمة المرور")
        form_layout.addRow("تأكيد كلمة المرور *:", self.confirm_password_input)

        form_group.setLayout(form_layout)
        main_layout.addWidget(form_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.save_btn = QPushButton("حفظ")
        self.save_btn.setMinimumWidth(100)
        self.save_btn.setMinimumHeight(32)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setMinimumHeight(32)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        main_layout.addLayout(btn_layout)

    def _populate(self, user: User):
        """Pre-fill form fields when editing."""
        self.username_input.setText(user.username)
        self.username_input.setEnabled(False)  # don't allow changing username
        self.full_name_input.setText(user.full_name)
        self.email_input.setText(user.email or "")
        self.phone_input.setText(user.phone or "")

        # select the matching role
        idx = self.role_combo.findData(user.role)
        if idx >= 0:
            self.role_combo.setCurrentIndex(idx)

        # In edit mode password is optional
        self.password_input.setPlaceholderText("(اتركه فارغاً للإبقاء على الحالي)")
        self.confirm_password_input.setPlaceholderText("(اتركه فارغاً للإبقاء على الحالي)")

    # ── Validation ─────────────────────────────────────────
    def _validate(self) -> bool:
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال اسم المستخدم.")
            self.username_input.setFocus()
            return False

        if self.editing_user is None:
            # Add mode — password required
            pwd = self.password_input.text()
            confirm = self.confirm_password_input.text()
            if not pwd:
                QMessageBox.warning(self, "تنبيه", "يرجى إدخال كلمة المرور.")
                self.password_input.setFocus()
                return False
            if pwd != confirm:
                QMessageBox.warning(self, "تنبيه", "كلمة المرور وتأكيدها غير متطابقتين.")
                self.confirm_password_input.setFocus()
                return False
            if len(pwd) < 4:
                QMessageBox.warning(self, "تنبيه", "كلمة المرور يجب أن تكون 4 أحرف على الأقل.")
                self.password_input.setFocus()
                return False
        else:
            # Edit mode — if password provided it must match confirmation
            pwd = self.password_input.text()
            if pwd:
                confirm = self.confirm_password_input.text()
                if pwd != confirm:
                    QMessageBox.warning(self, "تنبيه", "كلمة المرور وتأكيدها غير متطابقتين.")
                    self.confirm_password_input.setFocus()
                    return False
                if len(pwd) < 4:
                    QMessageBox.warning(self, "تنبيه", "كلمة المرور يجب أن تكون 4 أحرف على الأقل.")
                    self.password_input.setFocus()
                    return False

        return True

    # ── Save ───────────────────────────────────────────────
    def _on_save(self):
        if not self._validate():
            return

        try:
            manager = UserManager(self.db_manager)

            username = self.username_input.text().strip()
            full_name = self.full_name_input.text().strip()
            email = self.email_input.text().strip() or None
            phone = self.phone_input.text().strip() or None
            role = self.role_combo.currentData()

            if self.editing_user is None:
                # ── Create ──
                pwd = self.password_input.text()
                new_user = User(
                    username=username,
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    role=role,
                    is_active=True,
                )
                user_id = manager.create_user(new_user, pwd)
                if user_id:
                    QMessageBox.information(self, "نجاح", f"تم إنشاء المستخدم بنجاح (#{user_id}).")
                    self.accept()
                else:
                    QMessageBox.critical(self, "خطأ", "فشل في إنشاء المستخدم. ربما اسم المستخدم موجود مسبقاً.")
            else:
                # ── Update ──
                self.editing_user.full_name = full_name
                self.editing_user.email = email
                self.editing_user.phone = phone
                self.editing_user.role = role

                pwd = self.password_input.text()
                if pwd:
                    manager.change_password(self.editing_user.id, pwd, pwd)  # admin bypass

                ok = manager.update_user(self.editing_user)
                if ok:
                    QMessageBox.information(self, "نجاح", "تم تحديث بيانات المستخدم بنجاح.")
                    self.accept()
                else:
                    QMessageBox.critical(self, "خطأ", "فشل في تحديث بيانات المستخدم.")

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحفظ:\n{str(e)}")


# ──────────────────────────────────────────────────────────
#  Main user-management dialog
# ──────────────────────────────────────────────────────────
class UserManagementDialog(QDialog):
    """نافذة إدارة المستخدمين — عرض، إضافة، تعديل، حذف، إعادة تعيين كلمة المرور، فتح القفل"""

    COLUMNS = [
        "الاسم الكامل",
        "اسم المستخدم",
        "الدور",
        "البريد",
        "الحالة",
        "مقفل",
        "آخر دخول",
    ]
    COL_FULL_NAME = 0
    COL_USERNAME = 1
    COL_ROLE = 2
    COL_EMAIL = 3
    COL_ACTIVE = 4
    COL_LOCKED = 5
    COL_LAST_LOGIN = 6

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.users: list[User] = []

        self.setWindowTitle("إدارة المستخدمين")
        self.resize(860, 520)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self._build_ui()
        self._load_users()

    # ── UI ─────────────────────────────────────────────────
    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(14, 14, 14, 14)

        # ── Toolbar ──
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.add_btn = QPushButton("➕ إضافة مستخدم")
        self.add_btn.setMinimumHeight(34)
        self.add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self.add_btn)

        self.edit_btn = QPushButton("✏️ تعديل")
        self.edit_btn.setMinimumHeight(34)
        self.edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self.edit_btn)

        self.toggle_btn = QPushButton("🔄 تفعيل/تعطيل")
        self.toggle_btn.setMinimumHeight(34)
        self.toggle_btn.clicked.connect(self._on_toggle_active)
        toolbar.addWidget(self.toggle_btn)

        self.reset_pwd_btn = QPushButton("🔑 إعادة تعيين كلمة المرور")
        self.reset_pwd_btn.setMinimumHeight(34)
        self.reset_pwd_btn.clicked.connect(self._on_reset_password)
        toolbar.addWidget(self.reset_pwd_btn)

        self.unlock_btn = QPushButton("🔓 فتح القفل")
        self.unlock_btn.setMinimumHeight(34)
        self.unlock_btn.clicked.connect(self._on_unlock)
        toolbar.addWidget(self.unlock_btn)

        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.setMinimumHeight(34)
        self.delete_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self.delete_btn)

        toolbar.addStretch()

        self.refresh_btn = QPushButton("🔄 تحديث")
        self.refresh_btn.setMinimumHeight(34)
        self.refresh_btn.clicked.connect(self._load_users)
        toolbar.addWidget(self.refresh_btn)

        main_layout.addLayout(toolbar)

        # ── Search ──
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث بالاسم أو اسم المستخدم أو البريد...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # ── Table ──
        self.table = QTableView()
        self.table.setModel(QStandardItemModel())
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_context_menu)
        self.table.verticalHeader().setVisible(False)

        # Column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(self.COL_FULL_NAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_USERNAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_ROLE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_EMAIL, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_ACTIVE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_LOCKED, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_LAST_LOGIN, QHeaderView.ResizeMode.ResizeToContents)

        main_layout.addWidget(self.table)

        # ── Status bar ──
        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

    # ── Data loading ───────────────────────────────────────
    def _load_users(self):
        """Load all users (including inactive) into the table."""
        try:
            manager = UserManager(self.db_manager)
            self.users = manager.get_all_users(active_only=False)
            self._populate_table(self.users)
            self.status_label.setText(f"عدد المستخدمين: {len(self.users)}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل المستخدمين:\n{str(e)}")

    def _populate_table(self, users: list[User]):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(self.COLUMNS)

        for user in users:
            row_items = []

            # الاسم الكامل
            row_items.append(QStandardItem(user.full_name or ""))

            # اسم المستخدم
            row_items.append(QStandardItem(user.username or ""))

            # الدور
            row_items.append(QStandardItem(user.role or ""))

            # البريد
            row_items.append(QStandardItem(user.email or ""))

            # الحالة (نشط / معطّل)
            active_item = QStandardItem("نشط" if user.is_active else "معطّل")
            active_item.setForeground(
                Qt.GlobalColor.darkGreen if user.is_active else Qt.GlobalColor.red
            )
            row_items.append(active_item)

            # مقفل
            locked_item = QStandardItem("نعم" if user.is_locked else "لا")
            locked_item.setForeground(
                Qt.GlobalColor.red if user.is_locked else Qt.GlobalColor.darkGreen
            )
            row_items.append(locked_item)

            # آخر دخول
            if user.last_login:
                if isinstance(user.last_login, datetime):
                    login_str = user.last_login.strftime("%Y-%m-%d %H:%M")
                else:
                    login_str = str(user.last_login)
            else:
                login_str = "—"
            row_items.append(QStandardItem(login_str))

            # Make all items non-editable and store user id
            for item in row_items:
                item.setEditable(False)
                item.setData(user.id, Qt.ItemDataRole.UserRole)

            model.appendRow(row_items)

        self.table.setModel(model)

    # ── Helper: get selected user ──────────────────────────
    def _selected_user(self) -> User | None:
        """Return the User object for the currently selected table row, or None."""
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.information(self, "تنبيه", "يرجى اختيار مستخدم من الجدول.")
            return None
        row = indexes[0].row()
        user_id = self.table.model().index(row, 0).data(Qt.ItemDataRole.UserRole)
        for u in self.users:
            if u.id == user_id:
                return u
        return None

    # ── Actions ────────────────────────────────────────────
    def _on_add(self):
        dlg = UserFormDialog(self.db_manager, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_users()

    def _on_edit(self):
        user = self._selected_user()
        if not user:
            return
        dlg = UserFormDialog(self.db_manager, user=user, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_users()

    def _on_toggle_active(self):
        user = self._selected_user()
        if not user:
            return
        new_state = not user.is_active
        state_text = "تفعيل" if new_state else "تعطيل"
        reply = QMessageBox.question(
            self,
            "تأكيد",
            f"هل تريد {state_text} المستخدم «{user.full_name or user.username}»؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            manager = UserManager(self.db_manager)
            user.is_active = new_state
            ok = manager.update_user(user)
            if ok:
                QMessageBox.information(self, "نجاح", f"تم {state_text} المستخدم بنجاح.")
                self._load_users()
            else:
                QMessageBox.critical(self, "خطأ", f"فشل في {state_text} المستخدم.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ:\n{str(e)}")

    def _on_reset_password(self):
        user = self._selected_user()
        if not user:
            return
        reply = QMessageBox.question(
            self,
            "تأكيد",
            f"هل تريد إعادة تعيين كلمة مرور المستخدم «{user.full_name or user.username}»؟\n"
            "سيتم إنشاء كلمة مرور عشوائية جديدة.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            new_password = self._generate_password(8)
            manager = UserManager(self.db_manager)
            ok = manager.reset_password(user.id, new_password)
            if ok:
                QMessageBox.information(
                    self,
                    "كلمة المرور الجديدة",
                    f"تم إعادة تعيين كلمة المرور بنجاح.\n\n"
                    f"كلمة المرور الجديدة:\n{new_password}\n\n"
                    "يرجى نسخها وتسليمها للمستخدم.",
                )
                self._load_users()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في إعادة تعيين كلمة المرور.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ:\n{str(e)}")

    def _on_unlock(self):
        user = self._selected_user()
        if not user:
            return
        if not user.is_locked:
            QMessageBox.information(self, "معلومة", "هذا المستخدم غير مقفل.")
            return
        reply = QMessageBox.question(
            self,
            "تأكيد",
            f"هل تريد فتح قفل المستخدم «{user.full_name or user.username}»؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            manager = UserManager(self.db_manager)
            ok = manager.unlock_user(user.id)
            if ok:
                QMessageBox.information(self, "نجاح", "تم فتح القفل بنجاح.")
                self._load_users()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في فتح القفل.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ:\n{str(e)}")

    def _on_delete(self):
        user = self._selected_user()
        if not user:
            return
        reply = QMessageBox.warning(
            self,
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف المستخدم «{user.full_name or user.username}»؟\n"
            "لا يمكن التراجع عن هذا الإجراء.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            manager = UserManager(self.db_manager)
            ok = manager.delete_user(user.id)
            if ok:
                QMessageBox.information(self, "نجاح", "تم حذف المستخدم بنجاح.")
                self._load_users()
            else:
                QMessageBox.critical(self, "خطأ", "فشل في حذف المستخدم.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ:\n{str(e)}")

    # ── Context menu ───────────────────────────────────────
    def _on_context_menu(self, pos):
        menu = QMenu(self)
        menu.addAction("تعديل", self._on_edit)
        menu.addAction("حذف", self._on_delete)
        menu.addSeparator()
        menu.addAction("إعادة تعيين كلمة المرور", self._on_reset_password)
        menu.addAction("فتح القفل", self._on_unlock)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    # ── Search ─────────────────────────────────────────────
    def _on_search(self, text: str):
        text = text.strip().lower()
        if not text:
            self._populate_table(self.users)
            self.status_label.setText(f"عدد المستخدمين: {len(self.users)}")
            return
        filtered = [
            u
            for u in self.users
            if text in (u.full_name or "").lower()
            or text in (u.username or "").lower()
            or text in (u.email or "").lower()
        ]
        self._populate_table(filtered)
        self.status_label.setText(
            f"النتائج: {len(filtered)} من {len(self.users)}"
        )

    # ── Utility ────────────────────────────────────────────
    @staticmethod
    def _generate_password(length: int = 8) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))