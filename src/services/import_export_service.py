"""
نظام التصدير والاستيراد الشامل
Comprehensive Import/Export System
"""

import json
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import zipfile
import sqlite3


class DataExportService:
    """
    خدمة تصدير البيانات الشاملة
    تصدير جميع بيانات النظام بصيغ متعددة
    """
    
    def __init__(self, db_manager):
        """
        تهيئة خدمة التصدير
        
        Args:
            db_manager: مدير قاعدة البيانات
        """
        self.db = db_manager
    
    def export_all_data(
        self,
        output_path: str,
        format: str = 'json',
        include_attachments: bool = True
    ) -> dict:
        """
        تصدير جميع البيانات
        
        Args:
            output_path: مسار الملف الناتج
            format: صيغة التصدير (json, csv, xml, sql)
            include_attachments: تضمين المرفقات
            
        Returns:
            معلومات التصدير
        """
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'format': format,
                'version': '1.0'
            },
            'data': {}
        }
        
        # جداول للتصدير
        tables = self._get_exportable_tables()
        
        # تصدير كل جدول
        for table in tables:
            export_data['data'][table] = self._export_table(table)
        
        # حفظ حسب الصيغة
        if format == 'json':
            self._save_as_json(export_data, output_path)
        elif format == 'csv':
            self._save_as_csv(export_data, output_path)
        elif format == 'xml':
            self._save_as_xml(export_data, output_path)
        elif format == 'sql':
            self._save_as_sql(export_data, output_path)
        elif format == 'excel':
            self._save_as_excel(export_data, output_path)
        
        # إنشاء ZIP إذا كانت هناك مرفقات
        if include_attachments:
            self._add_attachments_to_export(output_path)
        
        return {
            'success': True,
            'path': output_path,
            'tables_count': len(tables),
            'total_records': sum(len(data) for data in export_data['data'].values())
        }
    
    def _get_exportable_tables(self) -> List[str]:
        """الحصول على قائمة الجداول القابلة للتصدير"""
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%'
            AND name NOT LIKE 'audit_logs'
            AND name NOT LIKE 'login_history'
            ORDER BY name
        """)
        
        return [row[0] for row in cursor.fetchall()]
    
    def _export_table(self, table_name: str) -> List[Dict]:
        """
        تصدير جدول
        
        Args:
            table_name: اسم الجدول
            
        Returns:
            قائمة الصفوف
        """
        cursor = self.db.connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        
        columns = [description[0] for description in cursor.description]
        rows = []
        
        for row in cursor.fetchall():
            row_dict = {}
            for i, value in enumerate(row):
                # تحويل datetime لنص
                if isinstance(value, datetime):
                    value = value.isoformat()
                row_dict[columns[i]] = value
            rows.append(row_dict)
        
        return rows
    
    def _save_as_json(self, data: dict, output_path: str):
        """حفظ كملف JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_as_csv(self, data: dict, output_path: str):
        """حفظ كملفات CSV (ملف لكل جدول)"""
        output_dir = Path(output_path).parent / f"{Path(output_path).stem}_csv"
        output_dir.mkdir(exist_ok=True)
        
        for table_name, rows in data['data'].items():
            if not rows:
                continue
            
            csv_file = output_dir / f"{table_name}.csv"
            with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
    
    def _save_as_xml(self, data: dict, output_path: str):
        """حفظ كملف XML"""
        root = ET.Element('database_export')
        
        # Metadata
        metadata = ET.SubElement(root, 'metadata')
        for key, value in data['metadata'].items():
            elem = ET.SubElement(metadata, key)
            elem.text = str(value)
        
        # Data
        data_elem = ET.SubElement(root, 'data')
        for table_name, rows in data['data'].items():
            table_elem = ET.SubElement(data_elem, 'table', name=table_name)
            
            for row in rows:
                row_elem = ET.SubElement(table_elem, 'row')
                for key, value in row.items():
                    field_elem = ET.SubElement(row_elem, 'field', name=key)
                    field_elem.text = str(value) if value is not None else ''
        
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    def _save_as_sql(self, data: dict, output_path: str):
        """حفظ كملف SQL"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("-- Database Export\n")
            f.write(f"-- Date: {data['metadata']['export_date']}\n\n")
            
            for table_name, rows in data['data'].items():
                if not rows:
                    continue
                
                f.write(f"\n-- Table: {table_name}\n")
                
                for row in rows:
                    columns = ', '.join(row.keys())
                    values = ', '.join(
                        f"'{str(v).replace(chr(39), chr(39)+chr(39))}'" if v is not None else 'NULL'
                        for v in row.values()
                    )
                    f.write(f"INSERT INTO {table_name} ({columns}) VALUES ({values});\n")
    
    def _save_as_excel(self, data: dict, output_path: str):
        """حفظ كملف Excel"""
        try:
            import pandas as pd
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for table_name, rows in data['data'].items():
                    if not rows:
                        continue
                    
                    df = pd.DataFrame(rows)
                    # اقتطاع اسم الورقة إلى 31 حرف (حد Excel)
                    sheet_name = table_name[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        except ImportError:
            raise ImportError("مكتبة pandas و openpyxl مطلوبة للتصدير إلى Excel")
    
    def _add_attachments_to_export(self, output_path: str):
        """إضافة المرفقات إلى ملف ZIP"""
        attachments_dir = Path("data/attachments")
        if not attachments_dir.exists():
            return
        
        zip_path = Path(output_path).with_suffix('.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # إضافة ملف التصدير
            zipf.write(output_path, Path(output_path).name)
            
            # إضافة المرفقات
            for file_path in attachments_dir.rglob('*'):
                if file_path.is_file():
                    arcname = str(file_path.relative_to(attachments_dir.parent))
                    zipf.write(file_path, arcname)
    
    def export_selection(
        self,
        tables: List[str],
        output_path: str,
        format: str = 'json',
        filters: Optional[Dict[str, str]] = None
    ) -> dict:
        """
        تصدير جداول محددة مع فلاتر
        
        Args:
            tables: قائمة الجداول
            output_path: مسار الخروج
            format: الصيغة
            filters: فلاتر SQL (table_name -> WHERE clause)
            
        Returns:
            معلومات التصدير
        """
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'format': format,
                'tables': tables
            },
            'data': {}
        }
        
        for table in tables:
            where_clause = filters.get(table, '') if filters else ''
            export_data['data'][table] = self._export_table_filtered(table, where_clause)
        
        # حفظ حسب الصيغة
        if format == 'json':
            self._save_as_json(export_data, output_path)
        elif format == 'csv':
            self._save_as_csv(export_data, output_path)
        elif format == 'excel':
            self._save_as_excel(export_data, output_path)
        
        return {
            'success': True,
            'path': output_path,
            'tables_count': len(tables)
        }
    
    def _export_table_filtered(self, table_name: str, where_clause: str) -> List[Dict]:
        """تصدير جدول مع فلتر"""
        cursor = self.db.connection.cursor()
        
        query = f"SELECT * FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        cursor.execute(query)
        
        columns = [description[0] for description in cursor.description]
        rows = []
        
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            rows.append(row_dict)
        
        return rows


class DataImportService:
    """
    خدمة استيراد البيانات الشاملة
    استيراد البيانات من مصادر خارجية
    """
    
    def __init__(self, db_manager):
        """
        تهيئة خدمة الاستيراد
        
        Args:
            db_manager: مدير قاعدة البيانات
        """
        self.db = db_manager
    
    def import_from_json(
        self,
        input_path: str,
        merge_mode: str = 'replace',
        validation: bool = True
    ) -> dict:
        """
        استيراد من ملف JSON
        
        Args:
            input_path: مسار الملف
            merge_mode: طريقة الدمج (replace, append, update)
            validation: تفعيل التحقق
            
        Returns:
            معلومات الاستيراد
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return self._import_data(data, merge_mode, validation)
    
    def import_from_csv(
        self,
        directory_path: str,
        merge_mode: str = 'append'
    ) -> dict:
        """
        استيراد من ملفات CSV
        
        Args:
            directory_path: مجلد الملفات
            merge_mode: طريقة الدمج
            
        Returns:
            معلومات الاستيراد
        """
        import_data = {'data': {}}
        
        csv_dir = Path(directory_path)
        for csv_file in csv_dir.glob('*.csv'):
            table_name = csv_file.stem
            
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                import_data['data'][table_name] = rows
        
        return self._import_data(import_data, merge_mode, validation=False)
    
    def import_from_excel(
        self,
        input_path: str,
        merge_mode: str = 'append'
    ) -> dict:
        """
        استيراد من ملف Excel
        
        Args:
            input_path: مسار الملف
            merge_mode: طريقة الدمج
            
        Returns:
            معلومات الاستيراد
        """
        try:
            import pandas as pd
            
            excel_file = pd.ExcelFile(input_path)
            import_data = {'data': {}}
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                rows = df.to_dict('records')
                import_data['data'][sheet_name] = rows
            
            return self._import_data(import_data, merge_mode, validation=False)
        
        except ImportError:
            raise ImportError("مكتبة pandas و openpyxl مطلوبة للاستيراد من Excel")
    
    def _import_data(
        self,
        data: dict,
        merge_mode: str,
        validation: bool
    ) -> dict:
        """
        استيراد البيانات
        
        Args:
            data: البيانات
            merge_mode: طريقة الدمج
            validation: تفعيل التحقق
            
        Returns:
            معلومات الاستيراد
        """
        cursor = self.db.connection.cursor()
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        try:
            for table_name, rows in data.get('data', {}).items():
                # التحقق من وجود الجدول
                if not self._table_exists(table_name):
                    skipped_count += len(rows)
                    continue
                
                # حذف البيانات الموجودة في وضع replace
                if merge_mode == 'replace':
                    cursor.execute(f"DELETE FROM {table_name}")
                
                # استيراد الصفوف
                for row in rows:
                    try:
                        if merge_mode == 'update':
                            self._update_or_insert_row(table_name, row)
                        else:
                            self._insert_row(table_name, row)
                        imported_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"Error importing row in {table_name}: {e}")
            
            self.db.connection.commit()
            
            return {
                'success': True,
                'imported': imported_count,
                'skipped': skipped_count,
                'errors': error_count
            }
        
        except Exception as e:
            self.db.connection.rollback()
            return {
                'success': False,
                'error': str(e),
                'imported': imported_count,
                'errors': error_count
            }
    
    def _table_exists(self, table_name: str) -> bool:
        """التحقق من وجود جدول"""
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        return cursor.fetchone() is not None
    
    def _insert_row(self, table_name: str, row: dict):
        """إدراج صف"""
        columns = ', '.join(row.keys())
        placeholders = ', '.join(['?' for _ in row])
        
        cursor = self.db.connection.cursor()
        cursor.execute(
            f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
            list(row.values())
        )
    
    def _update_or_insert_row(self, table_name: str, row: dict):
        """تحديث أو إدراج صف"""
        # افترض أن 'id' هو المفتاح الأساسي
        if 'id' in row:
            cursor = self.db.connection.cursor()
            cursor.execute(f"SELECT id FROM {table_name} WHERE id = ?", (row['id'],))
            
            if cursor.fetchone():
                # تحديث
                set_clause = ', '.join([f"{k} = ?" for k in row.keys() if k != 'id'])
                values = [v for k, v in row.items() if k != 'id']
                values.append(row['id'])
                
                cursor.execute(
                    f"UPDATE {table_name} SET {set_clause} WHERE id = ?",
                    values
                )
            else:
                # إدراج
                self._insert_row(table_name, row)
        else:
            self._insert_row(table_name, row)
    
    def validate_import_file(self, input_path: str) -> dict:
        """
        التحقق من ملف الاستيراد
        
        Args:
            input_path: مسار الملف
            
        Returns:
            نتائج التحقق
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'tables': []
        }
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # التحقق من الهيكل
            if 'data' not in data:
                results['errors'].append("ملف غير صحيح: لا يحتوي على 'data'")
                results['valid'] = False
                return results
            
            # التحقق من الجداول
            for table_name, rows in data['data'].items():
                if not self._table_exists(table_name):
                    results['warnings'].append(f"الجدول '{table_name}' غير موجود")
                else:
                    results['tables'].append({
                        'name': table_name,
                        'rows_count': len(rows)
                    })
        
        except json.JSONDecodeError:
            results['errors'].append("ملف JSON غير صحيح")
            results['valid'] = False
        except Exception as e:
            results['errors'].append(f"خطأ: {str(e)}")
            results['valid'] = False
        
        return results
