"""
نافذة البحث المتقدم والفلترة
Advanced Search & Filter Window
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QCheckBox, QSpinBox, QDateEdit, QSplitter, QListWidget,
    QListWidgetItem, QMessageBox, QDialog, QFormLayout, QDialogButtonBox
)
from PySide6.QtCore import Qt, QDate, QTimer, Signal
from PySide6.QtGui import QFont
from datetime import date, datetime
import json
from typing import List, Optional

from ...core.database_manager import DatabaseManager
from ...services.advanced_search_service import AdvancedSearchService
from ...models.search import (
    SearchEntity, SearchQuery, SearchFilter, FilterOperator,
    SortDirection, SortCriteria, SavedFilter
)


class AdvancedSearchWindow(QMainWindow):
    """نافذة البحث المتقدم"""
    
    # Window Manager attributes (للتسجيل التلقائي)
    window_key = "advanced_search"
    window_singleton = True
    window_title = "البحث المتقدم"
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.service = AdvancedSearchService(self.db)
        
        self.setWindowTitle("🔍 البحث المتقدم")
        self.setMinimumSize(1200, 700)
        
        self.current_query = SearchQuery(entity=SearchEntity.PRODUCTS)
        self.suggestion_timer = QTimer()
        self.suggestion_timer.setSingleShot(True)
        self.suggestion_timer.timeout.connect(self._show_suggestions)
        
        self._setup_ui()
        self._load_saved_filters()
    
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        
        # Left panel: Filters and options
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        
        # Entity selector
        entity_group = QGroupBox("البحث في")
        entity_layout = QVBoxLayout(entity_group)
        self.entity_combo = QComboBox()
        for entity in SearchEntity:
            self.entity_combo.addItem(entity.value, entity)
        self.entity_combo.currentIndexChanged.connect(self._on_entity_changed)
        entity_layout.addWidget(self.entity_combo)
        left_layout.addWidget(entity_group)
        
        # Search keyword
        search_group = QGroupBox("كلمة البحث")
        search_layout = QVBoxLayout(search_group)
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("ابحث...")
        self.keyword_input.textChanged.connect(self._on_keyword_changed)
        self.keyword_input.returnPressed.connect(self._execute_search)
        search_layout.addWidget(self.keyword_input)
        
        # Search options
        opts_layout = QHBoxLayout()
        self.case_sensitive_check = QCheckBox("حساس لحالة الأحرف")
        self.whole_word_check = QCheckBox("كلمة كاملة")
        opts_layout.addWidget(self.case_sensitive_check)
        opts_layout.addWidget(self.whole_word_check)
        search_layout.addLayout(opts_layout)
        
        self.include_inactive_check = QCheckBox("تضمين غير النشط")
        search_layout.addWidget(self.include_inactive_check)
        
        left_layout.addWidget(search_group)
        
        # Saved filters
        filters_group = QGroupBox("الفلاتر المحفوظة")
        filters_layout = QVBoxLayout(filters_group)
        self.saved_filters_list = QListWidget()
        self.saved_filters_list.itemDoubleClicked.connect(self._load_selected_filter)
        filters_layout.addWidget(self.saved_filters_list)
        
        filter_buttons = QHBoxLayout()
        load_filter_btn = QPushButton("تحميل")
        load_filter_btn.clicked.connect(self._load_selected_filter)
        save_filter_btn = QPushButton("حفظ")
        save_filter_btn.clicked.connect(self._save_current_filter)
        filter_buttons.addWidget(load_filter_btn)
        filter_buttons.addWidget(save_filter_btn)
        filters_layout.addLayout(filter_buttons)
        
        left_layout.addWidget(filters_group)
        
        # Limit
        limit_group = QGroupBox("عدد النتائج")
        limit_layout = QHBoxLayout(limit_group)
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(10, 1000)
        self.limit_spin.setValue(100)
        self.limit_spin.setSingleStep(10)
        limit_layout.addWidget(self.limit_spin)
        left_layout.addWidget(limit_group)
        
        left_layout.addStretch()
        
        # Search button
        search_btn = QPushButton("🔍 بحث")
        search_btn.setMinimumHeight(40)
        f = QFont(); f.setPointSize(12); f.setBold(True)
        search_btn.setFont(f)
        search_btn.clicked.connect(self._execute_search)
        left_layout.addWidget(search_btn)
        
        root.addWidget(left_panel)
        
        # Right panel: Results
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Results header
        header_layout = QHBoxLayout()
        self.results_label = QLabel("النتائج: 0")
        self.results_label.setStyleSheet("font-weight:bold; font-size:14px;")
        header_layout.addWidget(self.results_label)
        header_layout.addStretch()
        
        export_btn = QPushButton("📥 تصدير")
        export_btn.clicked.connect(self._export_results)
        header_layout.addWidget(export_btn)
        
        right_layout.addLayout(header_layout)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        right_layout.addWidget(self.results_table)
        
        # Pagination
        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch()
        self.prev_btn = QPushButton("◀ السابق")
        self.prev_btn.clicked.connect(self._previous_page)
        self.next_btn = QPushButton("التالي ▶")
        self.next_btn.clicked.connect(self._next_page)
        self.page_label = QLabel("صفحة 1")
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addStretch()
        right_layout.addLayout(pagination_layout)
        
        root.addWidget(right_panel, 1)
    
    def _on_entity_changed(self):
        """عند تغيير الكيان"""
        entity = self.entity_combo.currentData()
        if entity:
            self.current_query.entity = entity
            self._load_saved_filters()
    
    def _on_keyword_changed(self, text: str):
        """عند تغيير كلمة البحث"""
        self.current_query.keyword = text
        # Trigger suggestions after 300ms
        if len(text) >= 2:
            self.suggestion_timer.start(300)
    
    def _show_suggestions(self):
        """عرض الاقتراحات"""
        keyword = self.keyword_input.text()
        entity = self.entity_combo.currentData()
        
        if not keyword or not entity:
            return
        
        suggestions = self.service.get_suggestions(keyword, entity, 5)
        # Could show suggestions in a popup or dropdown
        # For now, just log
        if suggestions:
            pass  # TODO: Show suggestion popup
    
    def _execute_search(self):
        """تنفيذ البحث"""
        # Update query from UI
        self.current_query.keyword = self.keyword_input.text()
        self.current_query.entity = self.entity_combo.currentData()
        self.current_query.limit = self.limit_spin.value()
        self.current_query.case_sensitive = self.case_sensitive_check.isChecked()
        self.current_query.whole_word = self.whole_word_check.isChecked()
        self.current_query.include_inactive = self.include_inactive_check.isChecked()
        
        # Execute
        result = self.service.search(self.current_query)
        
        # Display results
        self._display_results(result)
        
        # Update UI
        self.results_label.setText(f"النتائج: {result.total_count} ({result.execution_time_ms:.1f}ms)")
        self.page_label.setText(f"صفحة {result.page} من {result.total_pages}")
        self.prev_btn.setEnabled(result.page > 1)
        self.next_btn.setEnabled(result.has_more)
    
    def _display_results(self, result):
        """عرض النتائج"""
        self.results_table.clear()
        
        if not result.records:
            self.results_table.setRowCount(0)
            self.results_table.setColumnCount(0)
            return
        
        # Setup columns
        first_record = result.records[0]
        columns = list(first_record.keys())
        self.results_table.setColumnCount(len(columns))
        self.results_table.setHorizontalHeaderLabels(columns)
        
        # Fill rows
        self.results_table.setRowCount(len(result.records))
        for row_idx, record in enumerate(result.records):
            for col_idx, col_name in enumerate(columns):
                value = record.get(col_name, '')
                if value is None:
                    value = ''
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.results_table.setItem(row_idx, col_idx, item)
        
        self.results_table.resizeColumnsToContents()
    
    def _previous_page(self):
        """الصفحة السابقة"""
        if self.current_query.offset >= self.current_query.limit:
            self.current_query.offset -= self.current_query.limit
            self._execute_search()
    
    def _next_page(self):
        """الصفحة التالية"""
        self.current_query.offset += self.current_query.limit
        self._execute_search()
    
    def _load_saved_filters(self):
        """تحميل الفلاتر المحفوظة"""
        self.saved_filters_list.clear()
        
        entity = self.entity_combo.currentData()
        filters = self.service.list_saved_filters(entity=entity if entity != SearchEntity.ALL else None)
        
        for filt in filters:
            item = QListWidgetItem(f"{'⭐ ' if filt.is_default else ''}{filt.name}")
            item.setData(Qt.ItemDataRole.UserRole, filt)
            self.saved_filters_list.addItem(item)
    
    def _load_selected_filter(self):
        """تحميل الفلتر المحدد"""
        item = self.saved_filters_list.currentItem()
        if not item:
            return
        
        saved_filter: SavedFilter = item.data(Qt.ItemDataRole.UserRole)
        if not saved_filter or not saved_filter.query_data:
            return
        
        try:
            query_dict = json.loads(saved_filter.query_data)
            self.current_query = SearchQuery.from_dict(query_dict)
            
            # Update UI
            self.keyword_input.setText(self.current_query.keyword)
            self.limit_spin.setValue(self.current_query.limit)
            self.case_sensitive_check.setChecked(self.current_query.case_sensitive)
            self.whole_word_check.setChecked(self.current_query.whole_word)
            self.include_inactive_check.setChecked(self.current_query.include_inactive)
            
            # Execute search
            self._execute_search()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل تحميل الفلتر: {e}")
    
    def _save_current_filter(self):
        """حفظ الفلتر الحالي"""
        dialog = SaveFilterDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.name_input.text()
            description = dialog.description_input.text()
            is_shared = dialog.shared_check.isChecked()
            
            saved_filter = SavedFilter(
                name=name,
                description=description,
                entity=self.current_query.entity,
                query_data=json.dumps(self.current_query.to_dict(), ensure_ascii=False),
                is_shared=is_shared
            )
            
            try:
                self.service.save_filter(saved_filter)
                QMessageBox.information(self, "نجاح", "تم حفظ الفلتر بنجاح")
                self._load_saved_filters()
            except Exception as e:
                QMessageBox.warning(self, "خطأ", f"فشل حفظ الفلتر: {e}")
    
    def _export_results(self):
        """تصدير النتائج"""
        QMessageBox.information(self, "تصدير", "سيتم إضافة ميزة التصدير قريباً")


class SaveFilterDialog(QDialog):
    """حوار حفظ الفلتر"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("حفظ الفلتر")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        self.name_input = QLineEdit()
        layout.addRow("الاسم:", self.name_input)
        
        self.description_input = QLineEdit()
        layout.addRow("الوصف:", self.description_input)
        
        self.shared_check = QCheckBox("مشاركة مع المستخدمين الآخرين")
        layout.addRow("", self.shared_check)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
