"""
نظام التصدير والاستيراد الشامل
Comprehensive Import/Export System
"""

import csv
import json
import logging
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..utils.db_helpers import validate_path_within_base

logger = logging.getLogger(__name__)

# Sensitive columns that should NEVER be exported
SENSITIVE_COLUMNS = frozenset({
    "password_hash", "password", "passwd", "salt",
    "otp_secret", "secret_key", "access_key", "api_key", "api_secret",
    "encryption_key", "smtp_password", "ftp_password",
    "secret", "token", "refresh_token", "access_token",
})

# Tables that should be excluded from export entirely (too sensitive or too large)
EXCLUDED_EXPORT_TABLES = frozenset({
    "audit_logs", "login_history", "sessions",
    "schema_migrations", "sqlite_sequence",
})

# Maximum file size for imports (50 MB)
MAX_IMPORT_FILE_SIZE = 50 * 1024 * 1024

# Maximum number of rows per table import (to prevent DoS)
MAX_ROWS_PER_TABLE = 100_000

# Dangerous formula prefixes for CSV/Excel injection
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


class DataExportService:
    """
    خدمة تصدير البيانات الشاملة
    تصدير جميع بيانات النظام بصيغ متعددة
    """

    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)

    def export_all_data(self, output_path: str, format: str = "json", include_attachments: bool = True) -> dict:
        """
        تصدير جميع البيانات

        Args:
            output_path: مسار الملف الناتج
            format: صيغة التصدير (json, csv, xml, sql)
            include_attachments: تضمين المرفقات

        Returns:
            معلومات التصدير
        """
        # VALIDATION: prevent path traversal for output
        try:
            output_path = str(validate_path_within_base(output_path, Path.cwd()))
        except ValueError:
            return {"success": False, "error": f"Output path '{output_path}' is outside allowed directory"}

        export_data = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "format": format,
                "version": "1.0",
            },
            "data": {},
        }

        # جداول للتصدير
        tables = self._get_exportable_tables()

        # تصدير كل جدول
        for table in tables:
            export_data["data"][table] = self._export_table(table)

        # حفظ حسب الصيغة
        if format == "json":
            self._save_as_json(export_data, output_path)
        elif format == "csv":
            self._save_as_csv(export_data, output_path)
        elif format == "xml":
            self._save_as_xml(export_data, output_path)
        elif format == "sql":
            self._save_as_sql(export_data, output_path)
        elif format == "excel":
            self._save_as_excel(export_data, output_path)

        # إنشاء ZIP إذا كانت هناك مرفقات
        if include_attachments:
            self._add_attachments_to_export(output_path)

        return {
            "success": True,
            "path": output_path,
            "tables_count": len(tables),
            "total_records": sum(len(data) for data in export_data["data"].values()),
        }

    def _get_exportable_tables(self) -> List[str]:
        """الحصول على قائمة الجداول القابلة للتصدير"""
        cursor = self.db.connection.cursor()

        # Build exclusion clause
        exclude_clause = " AND ".join([f"AND name NOT LIKE ?" for _ in EXCLUDED_EXPORT_TABLES])
        exclude_params = list(EXCLUDED_EXPORT_TABLES)

        cursor.execute(f"""
            SELECT name FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%'
            {exclude_clause}
            ORDER BY name
        """, exclude_params)

        rows = cursor.fetchall()
        return [row[0] if isinstance(row, (list, tuple)) else row.get('name', '') for row in rows]

    def _validate_table_name(self, table_name: str) -> bool:
        """تحقق من صحة اسم الجدول (منع SQL injection)"""
        if not table_name or not isinstance(table_name, str):
            return False
        # فقط أحرف إنجليزية وأرقام وشرطة سفلية
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name))

    def _validate_column_name(self, col_name: str) -> bool:
        """تحقق من صحة اسم العمود (منع SQL injection)"""
        if not col_name or not isinstance(col_name, str):
            return False
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col_name))

    def _get_safe_columns(self, table_name: str) -> Optional[List[str]]:
        """الحصول على قائمة الأعمدة الآمنة للتصدير (استبعاد الأعمدة الحساسة)"""
        cursor = self.db.connection.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")  # SQL_SAFE: validated by caller
        columns_info = cursor.fetchall()

        safe_columns = []
        for col_info in columns_info:
            # col_info format: (cid, name, type, notnull, dflt_value, pk)
            col_name = col_info[1] if isinstance(col_info, (list, tuple)) else col_info.get('name', '')
            if col_name.lower() not in SENSITIVE_COLUMNS:
                safe_columns.append(col_name)

        return safe_columns if safe_columns else None

    def _export_table(self, table_name: str) -> List[Dict]:
        """
        تصدير جدول مع استبعاد الأعمدة الحساسة

        Args:
            table_name: اسم الجدول

        Returns:
            قائمة الصفوف
        """
        if not self._validate_table_name(table_name):
            return []

        # Get safe columns (exclude sensitive columns like password_hash, otp_secret, etc.)
        safe_columns = self._get_safe_columns(table_name)
        if not safe_columns:
            self.logger.warning(f"No safe columns to export for table {table_name}")
            return []

        columns_str = ", ".join(safe_columns)
        cursor = self.db.connection.cursor()
        cursor.execute(f"SELECT {columns_str} FROM {table_name}")  # SQL_SAFE: all validated

        rows = []
        for row in cursor.fetchall():
            row_dict = {}
            for i, value in enumerate(row):
                # تحويل datetime لنص
                if isinstance(value, datetime):
                    value = value.isoformat()
                row_dict[safe_columns[i]] = value
            rows.append(row_dict)

        return rows

    def _sanitize_csv_value(self, value) -> str:
        """Sanitize a value for CSV/Excel export to prevent formula injection"""
        str_val = str(value) if value is not None else ""
        if str_val.startswith(FORMULA_PREFIXES):
            # Prefix with a single quote to defang formula injection
            return "'" + str_val
        return str_val

    def _save_as_json(self, data: dict, output_path: str):
        """حفظ كملف JSON"""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_as_csv(self, data: dict, output_path: str):
        """حفظ كملفات CSV (ملف لكل جدول)"""
        output_dir = Path(output_path).parent / f"{Path(output_path).stem}_csv"
        output_dir.mkdir(exist_ok=True)

        for table_name, rows in data["data"].items():
            if not rows:
                continue

            csv_file = output_dir / f"{table_name}.csv"
            with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                # Sanitize rows to prevent formula injection
                for row in rows:
                    sanitized_row = {k: self._sanitize_csv_value(v) for k, v in row.items()}
                    writer.writerow(sanitized_row)

    def _save_as_xml(self, data: dict, output_path: str):
        """حفظ كملف XML"""
        root = ET.Element("database_export")

        # Metadata
        metadata = ET.SubElement(root, "metadata")
        for key, value in data["metadata"].items():
            elem = ET.SubElement(metadata, key)
            elem.text = str(value)

        # Data
        data_elem = ET.SubElement(root, "data")
        for table_name, rows in data["data"].items():
            table_elem = ET.SubElement(data_elem, "table", name=table_name)

            for row in rows:
                row_elem = ET.SubElement(table_elem, "row")
                for key, value in row.items():
                    field_elem = ET.SubElement(row_elem, "field", name=key)
                    field_elem.text = str(value) if value is not None else ""

        tree = ET.ElementTree(root)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

    def _save_as_sql(self, data: dict, output_path: str):
        """حفظ كملف SQL"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("-- Database Export\n")
            f.write(f"-- Date: {data['metadata']['export_date']}\n\n")

            for table_name, rows in data["data"].items():
                if not rows:
                    continue

                f.write(f"\n-- Table: {table_name}\n")

                for row in rows:
                    columns = ", ".join(row.keys())
                    values = ", ".join(
                        (f"'{str(v).replace(chr(39), chr(39)+chr(39))}'" if v is not None else "NULL")
                        for v in row.values()
                    )
                    f.write(f"INSERT INTO {table_name} ({columns}) VALUES ({values});\n")  # SQL_SAFE: table_name validated; values escaped for SQL dump output

    def _save_as_excel(self, data: dict, output_path: str):
        """حفظ كملف Excel"""
        try:
            import pandas as pd

            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                for table_name, rows in data["data"].items():
                    if not rows:
                        continue

                    df = pd.DataFrame(rows)
                    # Sanitize cells to prevent formula injection
                    for col in df.columns:
                        df[col] = df[col].apply(self._sanitize_csv_value)
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

        zip_path = Path(output_path).with_suffix(".zip")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # إضافة ملف التصدير
            zipf.write(output_path, Path(output_path).name)

            # إضافة المرفقات
            for file_path in attachments_dir.rglob("*"):
                if file_path.is_file():
                    arcname = str(file_path.relative_to(attachments_dir.parent))
                    zipf.write(file_path, arcname)

    def export_selection(
        self,
        tables: List[str],
        output_path: str,
        format: str = "json",
        filters: Optional[Dict[str, str]] = None,
        filter_params: Optional[Dict[str, tuple]] = None,
    ) -> dict:
        """
        تصدير جداول محددة مع فلاتر

        Args:
            tables: قائمة الجداول
            output_path: مسار الخروج
            format: الصيغة
            filters: فلاتر WHERE clause (table_name -> WHERE clause with ? placeholders)
            filter_params: قيم المعاملات (table_name -> tuple of values)

        Returns:
            معلومات التصدير
        """
        # VALIDATION: prevent path traversal for output
        try:
            output_path = str(validate_path_within_base(output_path, Path.cwd()))
        except ValueError:
            return {"success": False, "error": f"Output path '{output_path}' is outside allowed directory"}

        export_data = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "format": format,
                "tables": tables,
            },
            "data": {},
        }

        for table in tables:
            where_clause = filters.get(table, "") if filters else ""
            params = filter_params.get(table, ()) if filter_params else ()
            export_data["data"][table] = self._export_table_filtered(table, where_clause, params)

        # حفظ حسب الصيغة
        if format == "json":
            self._save_as_json(export_data, output_path)
        elif format == "csv":
            self._save_as_csv(export_data, output_path)
        elif format == "excel":
            self._save_as_excel(export_data, output_path)

        return {"success": True, "path": output_path, "tables_count": len(tables)}

    def _export_table_filtered(self, table_name: str, where_clause: str, params: tuple = ()) -> List[Dict]:
        """تصدير جدول مع فلتر

        Args:
            table_name: اسم الجدول (يتم التحقق منه)
            where_clause: جملة WHERE (يجب أن تستخدم ? placeholder مع params)
            params: قيم المعاملات للـ placeholders

        Raises:
            ValueError: If table_name is invalid
        """
        if not self._validate_table_name(table_name):
            raise ValueError(f"Invalid table name: {table_name}")

        # Get safe columns (exclude sensitive columns)
        safe_columns = self._get_safe_columns(table_name)
        if not safe_columns:
            self.logger.warning(f"No safe columns to export for table {table_name}")
            return []

        columns_str = ", ".join(safe_columns)
        cursor = self.db.connection.cursor()

        query = f"SELECT {columns_str} FROM {table_name}"  # SQL_SAFE: validated
        if where_clause:
            query += f" WHERE {where_clause}"  # SQL_SAFE: where_clause built from parameterized conditions

        cursor.execute(query, params)

        rows = []
        for row in cursor.fetchall():
            row_dict = dict(zip(safe_columns, row))
            rows.append(row_dict)

        return rows


class DataImportService:
    """
    خدمة استيراد البيانات الشاملة
    استيراد البيانات من مصادر خارجية
    """

    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)

    def _validate_import_path(self, input_path: str) -> Tuple[bool, str, Optional[str]]:
        """Validate an import path: check path traversal and file size.

        Returns:
            (is_valid, resolved_path, error_message)
        """
        # Path traversal check
        try:
            resolved = str(validate_path_within_base(input_path, Path.cwd()))
        except ValueError:
            return False, "", f"Path '{input_path}' is outside allowed directory"

        # File size check (prevent DoS)
        if os.path.exists(resolved):
            file_size = os.path.getsize(resolved)
            if file_size > MAX_IMPORT_FILE_SIZE:
                return False, resolved, f"File size ({file_size} bytes) exceeds maximum ({MAX_IMPORT_FILE_SIZE} bytes)"

        return True, resolved, None

    def _validate_table_name(self, table_name: str) -> bool:
        """تحقق من صحة اسم الجدول (منع SQL injection)"""
        if not table_name or not isinstance(table_name, str):
            return False
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name))

    def _validate_column_name(self, col_name: str) -> bool:
        """تحقق من صحة اسم العمود (منع SQL injection)"""
        if not col_name or not isinstance(col_name, str):
            return False
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col_name))

    def _validate_row_data(self, table_name: str, row: dict) -> List[str]:
        """Validate a row before import: check column names and sanitize values.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Validate column names
        for col in row.keys():
            if not self._validate_column_name(str(col)):
                errors.append(f"Invalid column name: {col}")

        # Check for formula injection in string values
        for col, val in row.items():
            if isinstance(val, str) and val.startswith(FORMULA_PREFIXES):
                # Defang by prefixing with single quote
                row[col] = "'" + val

        return errors

    def import_from_json(self, input_path: str, merge_mode: str = "replace", validation: bool = True) -> dict:
        """
        استيراد من ملف JSON

        Args:
            input_path: مسار الملف
            merge_mode: طريقة الدمج (replace, append, update)
            validation: تفعيل التحقق

        Returns:
            معلومات الاستيراد
        """
        is_valid, resolved_path, error = self._validate_import_path(input_path)
        if not is_valid:
            return {"success": False, "error": error}

        try:
            with open(resolved_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON: {e}"}

        # Schema validation
        if validation:
            if not isinstance(data, dict):
                return {"success": False, "error": "JSON root must be an object with 'data' key"}
            if "data" not in data:
                return {"success": False, "error": "JSON must contain 'data' key"}
            if not isinstance(data["data"], dict):
                return {"success": False, "error": "'data' must be an object (table_name -> rows)"}

            # Check row counts
            for table_name, rows in data["data"].items():
                if not isinstance(rows, list):
                    return {"success": False, "error": f"Table '{table_name}' data must be a list"}
                if len(rows) > MAX_ROWS_PER_TABLE:
                    return {"success": False, "error": f"Table '{table_name}' has {len(rows)} rows, max is {MAX_ROWS_PER_TABLE}"}

        return self._import_data(data, merge_mode, validation)

    def import_from_csv(self, directory_path: str, merge_mode: str = "append") -> dict:
        """
        استيراد من ملفات CSV

        Args:
            directory_path: مجلد الملفات
            merge_mode: طريقة الدمج

        Returns:
            معلومات الاستيراد
        """
        is_valid, resolved_path, error = self._validate_import_path(directory_path)
        if not is_valid:
            return {"success": False, "error": error}

        import_data = {"data": {}}

        csv_dir = Path(resolved_path)
        for csv_file in csv_dir.glob("*.csv"):
            table_name = csv_file.stem

            # Validate table name from filename
            if not self._validate_table_name(table_name):
                self.logger.warning(f"Skipping CSV file with invalid table name: {table_name}")
                continue

            # Check file size
            if csv_file.stat().st_size > MAX_IMPORT_FILE_SIZE:
                self.logger.warning(f"Skipping CSV file too large: {csv_file.name}")
                continue

            with open(csv_file, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = []
                for i, row in enumerate(reader):
                    if i >= MAX_ROWS_PER_TABLE:
                        self.logger.warning(f"CSV {csv_file.name}: truncated at {MAX_ROWS_PER_TABLE} rows")
                        break
                    # Sanitize formula injection in values
                    for key, val in row.items():
                        if isinstance(val, str) and val.startswith(FORMULA_PREFIXES):
                            row[key] = "'" + val
                    rows.append(row)
                import_data["data"][table_name] = rows

        return self._import_data(import_data, merge_mode, validation=True)

    def import_from_excel(self, input_path: str, merge_mode: str = "append") -> dict:
        """
        استيراد من ملف Excel

        Args:
            input_path: مسار الملف
            merge_mode: طريقة الدمج

        Returns:
            معلومات الاستيراد
        """
        is_valid, resolved_path, error = self._validate_import_path(input_path)
        if not is_valid:
            return {"success": False, "error": error}

        # Additional check for xlsx zip bomb (file size already checked above)
        try:
            with zipfile.ZipFile(resolved_path, 'r') as zf:
                total_uncompressed = sum(info.file_size for info in zf.infolist())
                if total_uncompressed > MAX_IMPORT_FILE_SIZE * 10:  # 10x compression ratio limit
                    return {"success": False, "error": "Excel file exceeds decompressed size limit (possible zip bomb)"}
        except zipfile.BadZipFile:
            return {"success": False, "error": "Invalid Excel file (not a valid ZIP/XLSX)"}

        try:
            import pandas as pd

            excel_file = pd.ExcelFile(resolved_path)
            import_data = {"data": {}}

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)

                # Validate table name from sheet name
                if not self._validate_table_name(sheet_name):
                    self.logger.warning(f"Skipping sheet with invalid name: {sheet_name}")
                    continue

                # Truncate if too many rows
                if len(df) > MAX_ROWS_PER_TABLE:
                    self.logger.warning(f"Sheet '{sheet_name}': truncated at {MAX_ROWS_PER_TABLE} rows")
                    df = df.head(MAX_ROWS_PER_TABLE)

                rows = df.to_dict("records")

                # Sanitize formula injection in all string cells
                for row in rows:
                    for key, val in row.items():
                        if isinstance(val, str) and val.startswith(FORMULA_PREFIXES):
                            row[key] = "'" + val

                import_data["data"][sheet_name] = rows

            return self._import_data(import_data, merge_mode, validation=True)

        except ImportError:
            raise ImportError("مكتبة pandas و openpyxl مطلوبة للاستيراد من Excel")

    def _import_data(self, data: dict, merge_mode: str, validation: bool) -> dict:
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
            for table_name, rows in data.get("data", {}).items():
                # التحقق من وجود الجدول واسمه
                if not self._validate_table_name(table_name):
                    self.logger.warning(f"Skipping invalid table name: {table_name}")
                    skipped_count += len(rows)
                    continue

                if not self._table_exists(table_name):
                    self.logger.warning(f"Skipping non-existent table: {table_name}")
                    skipped_count += len(rows)
                    continue

                # حذف البيانات الموجودة في وضع replace
                if merge_mode == "replace":
                    cursor.execute(f"DELETE FROM {table_name}")  # SQL_SAFE: validated by _validate_table_name

                # استيراد الصفوف
                for row in rows:
                    try:
                        # Validate row data (column names + formula injection)
                        if validation:
                            validation_errors = self._validate_row_data(table_name, row)
                            if validation_errors:
                                error_count += 1
                                self.logger.warning(f"Skipping row in {table_name}: {validation_errors}")
                                continue

                        if merge_mode == "update":
                            self._update_or_insert_row(table_name, row)
                        else:
                            self._insert_row(table_name, row)
                        imported_count += 1
                    except Exception as e:
                        error_count += 1
                        self.logger.error(f"Error importing row in {table_name}: {e}")

            self.db.connection.commit()

            return {
                "success": True,
                "imported": imported_count,
                "skipped": skipped_count,
                "errors": error_count,
            }

        except Exception as e:
            self.db.connection.rollback()
            self.logger.error(f"Import failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "imported": imported_count,
                "errors": error_count,
            }

    def _table_exists(self, table_name: str) -> bool:
        """التحقق من وجود جدول"""
        cursor = self.db.connection.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """,
            (table_name,),
        )
        return cursor.fetchone() is not None

    def _insert_row(self, table_name: str, row: dict):
        """إدراج صف"""
        if not self._validate_table_name(table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        for col in row.keys():
            if not self._validate_column_name(str(col)):
                raise ValueError(f"Invalid column name: {col}")
        columns = ", ".join(row.keys())
        placeholders = ", ".join(["?" for _ in row])

        cursor = self.db.connection.cursor()
        cursor.execute(
            f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",  # SQL_SAFE: validated
            list(row.values()),
        )

    def _update_or_insert_row(self, table_name: str, row: dict):
        """تحديث أو إدراج صف"""
        if not self._validate_table_name(table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        for col in row.keys():
            if not self._validate_column_name(str(col)):
                raise ValueError(f"Invalid column name: {col}")
        # افترض أن 'id' هو المفتاح الأساسي
        if "id" in row:
            cursor = self.db.connection.cursor()
            cursor.execute(f"SELECT id FROM {table_name} WHERE id = ?", (row.get("id"),))  # SQL_SAFE: validated

            if cursor.fetchone():
                # تحديث
                set_clause = ", ".join([f"{k} = ?" for k in row.keys() if k != "id"])  # SQL_SAFE: validated
                values = [v for k, v in row.items() if k != "id"]
                values.append(row.get("id"))

                cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE id = ?", values)  # SQL_SAFE: validated
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
        results = {"valid": True, "errors": [], "warnings": [], "tables": []}

        is_valid, resolved_path, error = self._validate_import_path(input_path)
        if not is_valid:
            results["errors"].append(error)
            results["valid"] = False
            return results

        try:
            with open(resolved_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # التحقق من الهيكل
            if "data" not in data:
                results["errors"].append("ملف غير صحيح: لا يحتوي على 'data'")
                results["valid"] = False
                return results

            # التحقق من الجداول
            for table_name, rows in data["data"].items():
                if not self._validate_table_name(table_name):
                    results["warnings"].append(f"Invalid table name: '{table_name}'")
                elif not self._table_exists(table_name):
                    results["warnings"].append(f"الجدول '{table_name}' غير موجود")
                else:
                    # Check for sensitive column import attempts
                    if rows:
                        sensitive_found = [c for c in rows[0].keys() if c.lower() in SENSITIVE_COLUMNS]
                        if sensitive_found:
                            results["warnings"].append(
                                f"Table '{table_name}' contains sensitive columns: {sensitive_found}"
                            )
                    results["tables"].append({"name": table_name, "rows_count": len(rows)})

        except json.JSONDecodeError:
            results["errors"].append("ملف JSON غير صحيح")
            results["valid"] = False
        except Exception as e:
            results["errors"].append(f"خطأ: {str(e)}")
            results["valid"] = False

        return results
