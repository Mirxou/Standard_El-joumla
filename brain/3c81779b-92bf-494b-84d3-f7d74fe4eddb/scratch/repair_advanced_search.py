import os

filepath = r'c:\Users\aboun\Desktop\Logical Version trae\src\ui\windows\advanced_search_window.py'

with open(filepath, 'rb') as f:
    data = f.read()

# Convert to string, handling possible corruption
try:
    content = data.decode('utf-8')
except UnicodeDecodeError:
    content = data.decode('utf-8', errors='replace')

# The corruption starts at "for item in self.quote_service.items:"
# and ends before "class SaveFilterDialog(QDialog):"

start_marker = "for item in self.quote_service.items:"
end_marker = "class SaveFilterDialog(QDialog):"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    before = content[:start_idx + len(start_marker)]
    after = content[end_idx:]
    
    # Correct middle content
    middle = """
            self.qp_list.addItem(f"{item['quantity']}x {item['name']} ({item['total_val']:,.0f})")

    def _clear_quote(self):
        self.quote_service.clear()
        self._update_quote_panel()

    def _edit_wholesale_price(self, row: int, product_id: str, current_price_str: str):
        \"\"\"تعديل سعر الجملة\"\"\"
        try:
            # Clean price string (remove comma)
            clean_price = current_price_str.replace(',', '')
            current_val = float(clean_price)
        except ValueError:
            current_val = 0.0
            
        new_price, ok = QInputDialog.getDouble(
            self, \"تعديل السعر\", 
            f\"سعر الجملة الجديد للمنتج {product_id}:\", 
            current_val, 0, 1000000, 2
        )
        
        if ok and new_price != current_val:
            success = self.joumla_service.update_wholesale_price(product_id, new_price)
            if success:
                # Refresh search to recalculate margins and colors
                self._execute_search()
                # QMessageBox.information(self, \"نجاح\", \"تم تحديث السعر بنجاح\")
            else:
                QMessageBox.critical(self, \"خطأ\", \"فشل تحديث السعر\")

    def execute_search(self):
        \"\"\"تنفيذ البحث (Public API)\"\"\"
        return self._execute_search()

    def get_search_results(self):
        \"\"\"الحصول على نتائج البحث (Public API)\"\"\"
        # Return records from the table
        results = []
        for row in range(self.results_table.rowCount()):
            record = {}
            for col in range(self.results_table.columnCount()):
                header_item = self.results_table.horizontalHeaderItem(col)
                header = header_item.text() if header_item else f\"Col{col}\"
                item = self.results_table.item(row, col)
                record[header] = item.text() if item else \"\"
            results.append(record)
        return results

    def save_search(self):
        \"\"\"حفظ البحث (Public API)\"\"\"
        return self._save_current_filter()

    def load_saved_search(self):
        \"\"\"تحميل بحث محفوظ (Public API)\"\"\"
        return self._load_selected_filter()

    def clear_filters(self):
        \"\"\"مسح الفلاتر (Public API)\"\"\"
        self.keyword_input.clear()
        self.results_table.clearContents()
        self.results_table.setRowCount(0)
        return True

"""
    new_content = before + middle + after
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Repaired AdvancedSearchWindow successfully")
else:
    print(f"Markers not found: start={start_idx}, end={end_idx}")
