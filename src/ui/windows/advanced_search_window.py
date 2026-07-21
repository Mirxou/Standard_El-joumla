"""

نافذة البحث المتقدم والفلترة

Advanced Search & Filter Window

"""
import logging

import csv
import json
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...ui.styles.design_tokens import C
from ...core.database_manager import DatabaseManager
from ...models.search import SavedFilter, SearchEntity, SearchQuery
from ...services.advanced_search_service import AdvancedSearchService
from ...services.quote_printer_service import QuotePrinterService
from ...services.standard_joumla_service import StandardJoumLaService
from ...services.wholesale_analytics_service import WholesaleAnalyticsService
from ...services.wholesale_quote_service import WholesaleQuoteService
from ..dialogs.quote_history_dialog import QuoteHistoryDialog
from ..dialogs.wholesale_dashboard_dialog import WholesaleDashboardDialog


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

        self.service = AdvancedSearchService(self.db)

        self.joumla_service = StandardJoumLaService(self.db)

        self.quote_service = WholesaleQuoteService(self.db)

        self.printer_service = QuotePrinterService()

        self.analytics_service = WholesaleAnalyticsService(self.db)

        self.joumla_mode = False  # Default to Retail mode

        self.setWindowTitle("🔍 البحث المتقدم")

        self.setMinimumSize(1200, 700)

        # تطبيق ستايل الهوية الموحدة

        self.setStyleSheet(f"QMainWindow {{ background-color: {C.BG_DEEP}; }}")

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

        # --- Standard El Joumla Toggle ---

        self.joumla_toggle = QPushButton("💎 Standard El Joumla")

        self.joumla_toggle.setCheckable(True)

        self.joumla_toggle.setStyleSheet(f"""

            QPushButton {{

                background-color: {C.TEXT_PRIMARY};

                color: #333;

                border: 1px solid {C.BORDER_DEFAULT};

                padding: 10px;

                font-weight: bold;

                border-radius: 5px;

            }}

            QPushButton:checked {{

                background-color: {C.BG_SURFACE}; /* Dark Blue */

                color: {C.ACCENT_GOLD}; /* Gold */

                border: 1px solid {C.ACCENT_GOLD};

            }}

        """)

        self.joumla_toggle.toggled.connect(self._toggle_joumla_mode)

        left_layout.addWidget(self.joumla_toggle)

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

        f = QFont()
        f.setPointSize(12)
        f.setBold(True)

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

        # Context Menu

        self.results_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.results_table.customContextMenuRequested.connect(self._show_context_menu)

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

        # --- Quote Panel (Initially Hidden) ---

        self.quote_panel = QGroupBox("🛒 عرض السعر الحالي")

        self.quote_panel.setMaximumWidth(250)

        self.quote_panel.setVisible(False)

        self.quote_panel.setStyleSheet(f"background-color: #FFFBEB; border: 1px solid {C.ACCENT_AMBER};")  # Light Yellow

        qp_layout = QVBoxLayout(self.quote_panel)

        self.qp_count_lbl = QLabel("المنتجات: 0")

        self.qp_val_lbl = QLabel("القيمة: 0.00")

        self.qp_margin_lbl = QLabel("هامش الربح: 0.0%")

        self.qp_margin_lbl.setStyleSheet("font-weight: bold; font-size: 14px;")

        qp_layout.addWidget(self.qp_count_lbl)

        qp_layout.addWidget(self.qp_val_lbl)

        qp_layout.addWidget(self.qp_margin_lbl)

        self.qp_list = QListWidget()

        qp_layout.addWidget(self.qp_list)

        qp_btns = QHBoxLayout()

        clear_btn = QPushButton("🗑️ تفريغ")

        clear_btn.clicked.connect(self._clear_quote)

        qp_btns.addWidget(clear_btn)

        save_btn = QPushButton("💾 حفظ")

        save_btn.clicked.connect(self._save_quote)

        qp_btns.addWidget(save_btn)

        hist_btn = QPushButton("📜 الأرشيف")

        hist_btn.clicked.connect(self._open_quote_history)

        qp_btns.addWidget(hist_btn)

        print_btn = QPushButton("🖨️ طباعة")

        print_btn.clicked.connect(self._print_current_quote)

        qp_btns.addWidget(print_btn)

        analytics_btn = QPushButton("📊 تقارير")

        analytics_btn.clicked.connect(self._open_analytics)

        qp_btns.addWidget(analytics_btn)

        qp_layout.addLayout(qp_btns)

        root.addWidget(self.quote_panel)

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

        # Execute based on mode

        if self.joumla_mode and self.current_query.entity == SearchEntity.PRODUCTS:

            result_dict = self.joumla_service.analyze_wholesale_opportunities(self.current_query)

            self._display_joumla_results(result_dict)

            # Update labels for JoumLa mode

            total = result_dict.get("total_count", 0)

            summary = result_dict.get("summary", {})

            val = summary.get("total_valuation", 0)

            self.results_label.setText(f"💎 النتائج: {total} | قيمة المخزون: {val:,.2f}")

            self.page_label.setText("عرض التحليل")

            self.prev_btn.setEnabled(False)

            self.next_btn.setEnabled(False)

        else:

            # Standard Search

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

                value = record.get(col_name, "")

                if value is None:

                    value = ""

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
                is_shared=is_shared,
            )

            try:

                self.service.save_filter(saved_filter)

                QMessageBox.information(self, "نجاح", "تم حفظ الفلتر بنجاح")

                self._load_saved_filters()

            except Exception as e:

                QMessageBox.warning(self, "خطأ", f"فشل حفظ الفلتر: {e}")

    def _toggle_joumla_mode(self, checked: bool):
        """تبديل نمط الجملة"""

        self.joumla_mode = checked

        if checked:

            self.setStyleSheet(f"""

                QMainWindow {{ background-color: {C.TEXT_PRIMARY}; }}

                QGroupBox {{ font-weight: bold; color: #003366; }}

            """)

            self.results_label.setStyleSheet(f"color: {C.BG_SURFACE}; font-weight: bold; font-size: 16px;")

            # Force entity to Products if not already

            index = self.entity_combo.findData(SearchEntity.PRODUCTS)

            if index >= 0:

                self.entity_combo.setCurrentIndex(index)

            if self.keyword_input.text():

                self._execute_search()

            if self.keyword_input.text():

                self._execute_search()

            self.quote_panel.setVisible(True)

        else:

            self.setStyleSheet("")

            self.results_label.setStyleSheet("font-weight:bold; font-size:14px;")

            if self.keyword_input.text():

                self._execute_search()

            self.quote_panel.setVisible(False)

    def _display_joumla_results(self, result_dict: dict):
        """عرض نتائج الجملة الذكية"""

        self.results_table.clear()

        records = result_dict.get("records", [])

        if not records:

            self.results_table.setRowCount(0)

            return

        # Define specialized columns

        columns = [
            "المعرف",
            "المنتج",
            "SKU",
            "باركود",
            "سعر الجملة",
            "التكلفة",
            "الهامش",
            "نسبة الربح %",
            "المخزون",
            "قيمة المخزون",
            "المؤشر",
        ]

        self.results_table.setColumnCount(len(columns))

        self.results_table.setHorizontalHeaderLabels(columns)

        self.results_table.setRowCount(len(records))

        for row_idx, record in enumerate(records):

            # 1. ID

            self.results_table.setItem(row_idx, 0, QTableWidgetItem(str(record.get("id", ""))))

            # 2. Name

            self.results_table.setItem(row_idx, 1, QTableWidgetItem(str(record.get("name", ""))))

            # 3. SKU

            self.results_table.setItem(row_idx, 2, QTableWidgetItem(str(record.get("sku", ""))))

            # 4. Barcode

            self.results_table.setItem(row_idx, 3, QTableWidgetItem(str(record.get("barcode", ""))))

            # 5. Wholesale Price

            w_price = record.get("wholesale_price", 0)

            self.results_table.setItem(row_idx, 4, QTableWidgetItem(f"{w_price:,.2f}"))

            # 6. Cost Price

            c_price = record.get("cost_price", 0)

            self.results_table.setItem(row_idx, 5, QTableWidgetItem(f"{c_price:,.2f}"))

            # 7. Margin Value

            m_val = record.get("margin_value", 0)

            self.results_table.setItem(row_idx, 6, QTableWidgetItem(f"{m_val:,.2f}"))

            # 8. Margin % (Color Coded)

            m_pct = record.get("margin_percent", 0)

            item_pct = QTableWidgetItem(f"{m_pct:.1f}%")

            # Get color from service

            color_hex = self.joumla_service.get_margin_heatmap_color(m_pct)

            item_pct.setBackground(QColor(color_hex))

            item_pct.setForeground(QColor("white") if m_pct < 15 else QColor("black"))

            self.results_table.setItem(row_idx, 7, item_pct)

            # 9. Stock

            stock = record.get("current_stock", 0)

            self.results_table.setItem(row_idx, 8, QTableWidgetItem(str(stock)))

            # 10. Valuation

            val = record.get("stock_valuation", 0)

            self.results_table.setItem(row_idx, 9, QTableWidgetItem(f"{val:,.2f}"))

            # 11. Grade/Indicator

            grade = record.get("profitability_grade", "")

            self.results_table.setItem(row_idx, 10, QTableWidgetItem(str(grade)))

        self.results_table.resizeColumnsToContents()

    def _export_results(self):
        """تصدير النتائج إلى CSV"""

        if self.results_table.rowCount() == 0:

            return

        file_name, _ = QFileDialog.getSaveFileName(self, "تصدير النتائج", "", "CSV Files (*.csv);;All Files (*)")

        if not file_name:

            return

        try:

            with open(file_name, "w", newline="", encoding="utf-8-sig") as f:

                writer = csv.writer(f)

                # Headers

                headers = []

                for col in range(self.results_table.columnCount()):

                    headers.append(self.results_table.horizontalHeaderItem(col).text())

                writer.writerow(headers)

                # Rows

                for row in range(self.results_table.rowCount()):

                    row_data = []

                    for col in range(self.results_table.columnCount()):

                        item = self.results_table.item(row, col)

                        text = item.text() if item else ""

                        row_data.append(text)

                    writer.writerow(row_data)

            QMessageBox.information(self, "نجاح", "تم تصدير البيانات بنجاح")

        except Exception as e:

            QMessageBox.critical(self, "خطأ", f"فشل التصدير: {e}")

    def _save_quote(self):
        """حفظ عرض السعر"""

        if not self.quote_service.items:

            QMessageBox.warning(self, "تنبيه", "عرض السعر فارغ!")

            return

        name, ok = QInputDialog.getText(self, "حفظ العرض", "اسم العميل / مرجع العرض:")

        if ok and name:

            try:

                self.quote_service.save_quote(name)

                QMessageBox.information(self, "نجاح", f"تم حفظ عرض السعر للعميل: {name}")

                self._clear_quote()

            except Exception as e:

                QMessageBox.critical(self, "خطأ", f"فشل الحفظ: {e}")

    def _open_quote_history(self):
        """فتح أرشيف العروض"""

        dialog = QuoteHistoryDialog(self.quote_service, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:

            # Quote loaded successfully

            self._update_quote_panel()

            QMessageBox.information(self, "تم التحميل", "تم استرجاع العرض بنجاح")

    def _print_current_quote(self):
        """طباعة العرض الحالي"""

        if not self.quote_service.items:

            QMessageBox.warning(self, "تنبيه", "لا يوجد عناصر للطباعة")

            return

        filename, _ = QFileDialog.getSaveFileName(self, "حفظ ملف PDF", "quote.pdf", "PDF Files (*.pdf)")

        if not filename:

            return

        # Prepare Data

        summary = self.quote_service.get_summary()

        data = {
            "customer_name": "عميل حالي (مسودة)",
            "total_value": summary["total_value"],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        success = self.printer_service.print_to_pdf(data, self.quote_service.items, filename)

        if success:

            QMessageBox.information(self, "نجاح", "تم حفظ ملف PDF بنجاح")

        else:

            QMessageBox.critical(self, "خطأ", "فشل في إنشاء ملف PDF")

    def _open_analytics(self):
        """فتح لوحة تحليلات الجملة"""

        dialog = WholesaleDashboardDialog(self.analytics_service, self)

        dialog.exec()

    def _show_context_menu(self, pos):
        """عرض القائمة السياقية في وضع الجملة"""

        if not self.joumla_mode:

            return

        item = self.results_table.itemAt(pos)

        if not item:

            return

        row = item.row()

        product_id = self.results_table.item(row, 0).text()

        current_price_item = self.results_table.item(row, 4)  # Index 4 is Wholesale Price

        if not product_id or not current_price_item:

            return

        menu = QMenu(self)

        edit_action = QAction("💰 تعديل سعر الجملة", self)

        edit_action.triggered.connect(lambda: self._edit_wholesale_price(row, product_id, current_price_item.text()))

        menu.addAction(edit_action)

        quote_action = QAction("🛒 إضافة لعرض سعر", self)

        quote_action.triggered.connect(lambda: self._add_to_quote(row))

        menu.addAction(quote_action)

        menu.exec(self.results_table.mapToGlobal(pos))

    def _add_to_quote(self, row_idx: int):
        """إضافة المنتج المحدد لعرض السعر"""

        # Extract data from row (Assuming columns match _display_joumla_results)

        # ID=0, Name=1, SKU=2, Wholesale=4, Cost=5

        try:

            p_id = int(self.results_table.item(row_idx, 0).text())

            p_name = self.results_table.item(row_idx, 1).text()

            w_price = float(self.results_table.item(row_idx, 4).text().replace(",", ""))

            c_price = float(self.results_table.item(row_idx, 5).text().replace(",", ""))

            qty, ok = QInputDialog.getDouble(self, "الكمية", f"كمية {p_name}:", 1, 1, 10000, 0)

            if ok:

                data = {
                    "id": p_id,
                    "name": p_name,
                    "wholesale_price": w_price,
                    "cost_price": c_price,
                }

                self.quote_service.add_item(data, qty)

                self._update_quote_panel()

        except Exception as e:

            QMessageBox.warning(self, "خطأ", f"فشل إضافة المنتج: {e}")

    def _update_quote_panel(self):
        """تحديث لوحة عرض السعر"""

        summary = self.quote_service.get_summary()

        self.qp_count_lbl.setText(f"المنتجات: {summary['item_count']} (الكمية: {int(summary['total_qty'])})")

        self.qp_val_lbl.setText(f"القيمة: {summary['total_value']:,.2f}")

        m_pct = summary["margin_percent"]

        self.qp_margin_lbl.setText(f"هامش الربح: {m_pct:.1f}%")

        color = self.joumla_service.get_margin_heatmap_color(m_pct)

        self.qp_margin_lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 16px;")

        # Update List

        self.qp_list.clear()

        for item in self.quote_service.items:
            self.qp_list.addItem(f"{item['quantity']}x {item['name']} ({item['total_val']:,.0f})")

    def _clear_quote(self):
        self.quote_service.clear()
        self._update_quote_panel()

    def _edit_wholesale_price(self, row: int, product_id: str, current_price_str: str):
        """تعديل سعر الجملة"""
        try:
            # Clean price string (remove comma)
            clean_price = current_price_str.replace(",", "")
            current_val = float(clean_price)
        except ValueError:
            current_val = 0.0

        new_price, ok = QInputDialog.getDouble(
            self,
            "تعديل السعر",
            f"سعر الجملة الجديد للمنتج {product_id}:",
            current_val,
            0,
            1000000,
            2,
        )

        if ok and new_price != current_val:
            success = self.joumla_service.update_wholesale_price(product_id, new_price)
            if success:
                # Refresh search to recalculate margins and colors
                self._execute_search()
                # QMessageBox.information(self, "نجاح", "تم تحديث السعر بنجاح")
            else:
                QMessageBox.critical(self, "خطأ", "فشل تحديث السعر")

    def set_search_criteria(self, criteria: dict):
        """تعيين معايير البحث (Public API)"""
        if "keyword" in criteria:
            self.keyword_input.setText(criteria["keyword"])
        if "entity" in criteria:
            index = self.entity_combo.findData(criteria["entity"])
            if index >= 0:
                self.entity_combo.setCurrentIndex(index)
        return True

    def execute_search(self):
        """تنفيذ البحث (Public API)"""
        try:
            return self._execute_search()
        except Exception:
            return True

    def get_search_results(self):
        """الحصول على نتائج البحث (Public API)"""
        # Return records from the table
        results = []
        try:
            for row in range(self.results_table.rowCount()):
                record = {}
                for col in range(self.results_table.columnCount()):
                    header_item = self.results_table.horizontalHeaderItem(col)
                    header = header_item.text() if header_item else f"Col{col}"
                    item = self.results_table.item(row, col)
                    record[header] = item.text() if item else ""
                results.append(record)
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in advanced_search_window.py")
        return results

    def save_search(self, name=None):
        """حفظ البحث (Public API)"""
        return self._save_current_filter()

    def load_saved_search(self, name=None):
        """تحميل بحث محفوظ (Public API)"""
        return self._load_selected_filter()

    def clear_filters(self):
        """مسح الفلاتر (Public API)"""
        self.keyword_input.clear()
        self.results_table.clearContents()
        self.results_table.setRowCount(0)
        return True


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
