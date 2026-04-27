"""
خدمة التقارير المتقدمة - Phase 8
Advanced Reporting Service for Unified Commerce 2030 ERP
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import os

from src.core.database_manager import DatabaseManager
from src.utils.logger import setup_logger

@dataclass
class ReportTemplate:
    """قالب تقرير"""
    template_id: str
    name: str
    description: str
    category: str
    template_config: Dict[str, Any]
    query_template: str
    ui_config: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None
    is_active: bool = True

@dataclass
class GeneratedReport:
    """تقرير مولد"""
    report_id: str
    template_id: str
    report_name: str
    parameters: Dict[str, Any]
    generated_data: Dict[str, Any]
    execution_time: float
    row_count: int
    generated_by: Optional[str] = None

@dataclass
class DashboardConfig:
    """تكوين لوحة تحكم"""
    dashboard_id: str
    name: str
    description: str
    category: str
    layout_config: Dict[str, Any]
    widgets_config: List[Dict[str, Any]]
    refresh_interval: int = 300

@dataclass
class KPIMetric:
    """مقياس KPI"""
    kpi_id: str
    name: str
    value: float
    target_value: Optional[float]
    unit: str
    trend: str  # 'improving', 'declining', 'stable'
    calculation_date: datetime

class AdvancedReportingService:
    """
    خدمة التقارير المتقدمة
    توفر إمكانيات التقارير المتقدمة ولوحات التحكم التفاعلية
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = setup_logger(__name__)

        # مجلد حفظ التقارير المصدرة
        self.exports_dir = os.path.join('data', 'exports')
        os.makedirs(self.exports_dir, exist_ok=True)

    def generate_report(self, template_id: str, parameters: Dict[str, Any] = None,
                       user_id: str = None) -> Optional[GeneratedReport]:
        """
        توليد تقرير من قالب

        Args:
            template_id: معرف القالب
            parameters: معلمات التقرير
            user_id: معرف المستخدم

        Returns:
            GeneratedReport: التقرير المولد أو None إذا فشل
        """
        try:
            self.logger.info(f"🔄 بدء توليد التقرير: {template_id}")

            # الحصول على القالب
            template = self._get_report_template(template_id)
            if not template:
                self.logger.error(f"القالب غير موجود: {template_id}")
                return None

            # دمج المعلمات
            params = parameters or {}
            default_params = self._get_default_parameters(template)
            merged_params = {**default_params, **params}

            # تنفيذ الاستعلام
            start_time = datetime.now()
            query_result = self._execute_report_query(template, merged_params)
            execution_time = (datetime.now() - start_time).total_seconds()

            if not query_result:
                self.logger.warning(f"لم يتم العثور على بيانات للتقرير: {template_id}")
                return None

            # إنشاء كائن التقرير
            report = GeneratedReport(
                report_id=f"REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                template_id=template_id,
                report_name=f"{template.name} - {datetime.now().strftime('%Y-%m-%d')}",
                parameters=merged_params,
                generated_data=query_result,
                execution_time=execution_time,
                row_count=len(query_result.get('data', [])),
                generated_by=user_id
            )

            # حفظ التقرير
            self._save_generated_report(report)

            self.logger.info(f"✅ تم توليد التقرير: {report.report_id} ({report.row_count} صف)")
            return report

        except Exception as e:
            self.logger.error(f"❌ فشل في توليد التقرير: {e}")
            return None

    def create_dashboard(self, config: Dict[str, Any], user_id: str = None) -> Optional[DashboardConfig]:
        """
        إنشاء لوحة تحكم جديدة

        Args:
            config: تكوين لوحة التحكم
            user_id: معرف المستخدم

        Returns:
            DashboardConfig: لوحة التحكم المُنشأة
        """
        try:
            self.logger.info("🔄 إنشاء لوحة تحكم جديدة")

            dashboard = DashboardConfig(
                dashboard_id=f"DASH_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                name=config.get('name', 'لوحة تحكم جديدة'),
                description=config.get('description', ''),
                category=config.get('category', 'analytical'),
                layout_config=config.get('layout_config', {}),
                widgets_config=config.get('widgets_config', []),
                refresh_interval=config.get('refresh_interval', 300)
            )

            # حفظ لوحة التحكم
            self._save_dashboard_config(dashboard, user_id)

            self.logger.info(f"✅ تم إنشاء لوحة التحكم: {dashboard.dashboard_id}")
            return dashboard

        except Exception as e:
            self.logger.error(f"❌ فشل في إنشاء لوحة التحكم: {e}")
            return None

    def get_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        """
        الحصول على بيانات لوحة التحكم

        Args:
            dashboard_id: معرف لوحة التحكم

        Returns:
            Dict[str, Any]: بيانات لوحة التحكم
        """
        try:
            # الحصول على تكوين لوحة التحكم
            dashboard = self._get_dashboard_config(dashboard_id)
            if not dashboard:
                return {}

            # جمع بيانات الودجيت
            widgets_data = []
            for widget_config in dashboard.widgets_config:
                widget_data = self._get_widget_data(widget_config)
                widgets_data.append({
                    'widget_id': widget_config.get('widget_id'),
                    'type': widget_config.get('type'),
                    'data': widget_data
                })

            return {
                'dashboard_id': dashboard_id,
                'name': dashboard.name,
                'widgets': widgets_data,
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"❌ فشل في الحصول على بيانات لوحة التحكم: {e}")
            return {}

    def calculate_kpis(self, date_filter: str = None) -> List[KPIMetric]:
        """
        حساب مؤشرات الأداء الرئيسية

        Args:
            date_filter: فلتر التاريخ

        Returns:
            List[KPIMetric]: قائمة المؤشرات المحسوبة
        """
        try:
            self.logger.info("📊 حساب مؤشرات الأداء الرئيسية")

            kpis = []

            # KPI 1: إجمالي المبيعات اليومية
            sales_kpi = self._calculate_sales_kpi(date_filter)
            if sales_kpi:
                kpis.append(sales_kpi)

            # KPI 2: عدد الطلبات
            orders_kpi = self._calculate_orders_kpi(date_filter)
            if orders_kpi:
                kpis.append(orders_kpi)

            # KPI 3: متوسط قيمة الطلب
            avg_order_kpi = self._calculate_avg_order_kpi(date_filter)
            if avg_order_kpi:
                kpis.append(avg_order_kpi)

            self.logger.info(f"✅ تم حساب {len(kpis)} مؤشر أداء")
            return kpis

        except Exception as e:
            self.logger.error(f"❌ فشل في حساب مؤشرات الأداء: {e}")
            return []

    def export_report(self, report_id: str, format_type: str = 'pdf') -> Optional[str]:
        """
        تصدير تقرير بصيغ مختلفة

        Args:
            report_id: معرف التقرير
            format_type: نوع الصيغة (pdf, excel, csv)

        Returns:
            str: مسار الملف المصدر أو None إذا فشل
        """
        try:
            self.logger.info(f"📤 تصدير التقرير: {report_id} بصيغة {format_type}")

            # الحصول على التقرير
            report = self._get_generated_report(report_id)
            if not report:
                return None

            # تحديد مسار الملف
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"report_{report_id}_{timestamp}.{format_type}"
            filepath = os.path.join(self.exports_dir, filename)

            # تصدير حسب الصيغة
            if format_type == 'csv':
                self._export_csv(report, filepath)
            elif format_type == 'excel':
                self._export_excel(report, filepath)
            elif format_type == 'pdf':
                self._export_pdf(report, filepath)
            else:
                raise ValueError(f"صيغة غير مدعومة: {format_type}")

            # تحديث مسار الملف في قاعدة البيانات
            self._update_report_file_path(report_id, filepath)

            self.logger.info(f"✅ تم تصدير التقرير إلى: {filepath}")
            return filepath

        except Exception as e:
            self.logger.error(f"❌ فشل في تصدير التقرير: {e}")
            return None

    # طرق مساعدة للقوالب والتقارير
    def _get_report_template(self, template_id: str) -> Optional[ReportTemplate]:
        """الحصول على قالب تقرير"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM report_templates WHERE template_id = ? AND is_active = 1
                """, (template_id,))

                row = cursor.fetchone()
                if row:
                    return ReportTemplate(
                        template_id=row[0],
                        name=row[1],
                        description=row[2] or '',
                        category=row[3],
                        template_config=json.loads(row[4]) if row[4] else {},
                        query_template=row[5] or '',
                        ui_config=json.loads(row[6]) if row[6] else None,
                        created_by=row[7],
                        is_active=bool(row[8])
                    )
                return None
        except Exception as e:
            self.logger.error(f"فشل في الحصول على قالب التقرير: {e}")
            return None

    def _execute_report_query(self, template: ReportTemplate, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """تنفيذ استعلام التقرير"""
        try:
            # تحليل الاستعلام وقيم المعلمات
            query = template.query_template
            param_values = []

            # استبدال placeholders بالقيم
            for key, value in parameters.items():
                placeholder = f"{{{key}}}"
                if placeholder in query:
                    query = query.replace(placeholder, '?')
                    param_values.append(value)

            # تنفيذ الاستعلام
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, param_values)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

            # تحويل إلى تنسيق مناسب
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))

            return {
                'columns': columns,
                'data': data,
                'metadata': {
                    'template_id': template.template_id,
                    'generated_at': datetime.now().isoformat(),
                    'parameters': parameters
                }
            }

        except Exception as e:
            self.logger.error(f"فشل في تنفيذ استعلام التقرير: {e}")
            return None

    def _save_generated_report(self, report: GeneratedReport) -> None:
        """حفظ التقرير المولد"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO generated_reports
                    (report_id, template_id, report_name, parameters, generated_data,
                     execution_time, row_count, generated_by, generated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report.report_id, report.template_id, report.report_name,
                    json.dumps(report.parameters), json.dumps(report.generated_data),
                    report.execution_time, report.row_count, report.generated_by,
                    datetime.now()
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"فشل في حفظ التقرير المولد: {e}")

    # طرق مساعدة للوحات التحكم
    def _get_dashboard_config(self, dashboard_id: str) -> Optional[DashboardConfig]:
        """الحصول على تكوين لوحة التحكم"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM dashboard_configs WHERE dashboard_id = ? AND is_active = 1
                """, (dashboard_id,))

                row = cursor.fetchone()
                if row:
                    return DashboardConfig(
                        dashboard_id=row[0],
                        name=row[1],
                        description=row[2] or '',
                        category=row[3],
                        layout_config=json.loads(row[4]) if row[4] else {},
                        widgets_config=json.loads(row[5]) if row[5] else [],
                        refresh_interval=row[6] or 300
                    )
                return None
        except Exception as e:
            self.logger.error(f"فشل في الحصول على تكوين لوحة التحكم: {e}")
            return None

    def _save_dashboard_config(self, dashboard: DashboardConfig, user_id: str = None) -> None:
        """حفظ تكوين لوحة التحكم"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO dashboard_configs
                    (dashboard_id, name, description, category, layout_config,
                     widgets_config, refresh_interval, created_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dashboard.dashboard_id, dashboard.name, dashboard.description,
                    dashboard.category, json.dumps(dashboard.layout_config),
                    json.dumps(dashboard.widgets_config), dashboard.refresh_interval,
                    user_id, datetime.now()
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"فشل في حفظ تكوين لوحة التحكم: {e}")

    def _get_widget_data(self, widget_config: Dict[str, Any]) -> Dict[str, Any]:
        """الحصول على بيانات ودجيت"""
        try:
            widget_type = widget_config.get('type')
            data_query = widget_config.get('data_query')

            if not data_query:
                return {'error': 'no data query defined'}

            # تنفيذ استعلام البيانات
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(data_query)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

            data = [dict(zip(columns, row)) for row in rows]

            return {
                'type': widget_type,
                'data': data,
                'columns': columns,
                'count': len(data)
            }

        except Exception as e:
            return {'error': str(e)}

    # طرق مساعدة للمؤشرات
    def _calculate_sales_kpi(self, date_filter: str = None) -> Optional[KPIMetric]:
        """حساب KPI المبيعات"""
        try:
            date_condition = ""
            params = []

            if date_filter:
                date_condition = "AND DATE(created_at) = ?"
                params.append(date_filter)
            else:
                # افتراضياً اليوم الحالي
                date_condition = "AND DATE(created_at) = DATE('now')"
                params = []

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT SUM(total_amount) as total_sales
                    FROM sales
                    WHERE status = 'completed' {date_condition}
                """, params)

                result = cursor.fetchone()
                current_value = result[0] or 0

                # حساب القيمة المستهدفة (يمكن تحسينها)
                target_value = 50000  # قيمة ثابتة للاختبار

                # تحديد الاتجاه (بسيط)
                trend = 'stable'
                if current_value > target_value * 1.1:
                    trend = 'improving'
                elif current_value < target_value * 0.9:
                    trend = 'declining'

                return KPIMetric(
                    kpi_id='KPI_TOTAL_SALES',
                    name='إجمالي المبيعات',
                    value=current_value,
                    target_value=target_value,
                    unit='SAR',
                    trend=trend,
                    calculation_date=datetime.now()
                )

        except Exception as e:
            self.logger.error(f"فشل في حساب KPI المبيعات: {e}")
            return None

    def _calculate_orders_kpi(self, date_filter: str = None) -> Optional[KPIMetric]:
        """حساب KPI عدد الطلبات"""
        try:
            date_condition = ""
            params = []

            if date_filter:
                date_condition = "AND DATE(created_at) = ?"
                params.append(date_filter)

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT COUNT(*) as order_count
                    FROM sales
                    WHERE status = 'completed' {date_condition}
                """, params)

                result = cursor.fetchone()
                current_value = result[0] or 0

                return KPIMetric(
                    kpi_id='KPI_ORDER_COUNT',
                    name='عدد الطلبات',
                    value=float(current_value),
                    target_value=50.0,
                    unit='orders',
                    trend='stable',  # يمكن تحسينه
                    calculation_date=datetime.now()
                )

        except Exception as e:
            self.logger.error(f"فشل في حساب KPI الطلبات: {e}")
            return None

    def _calculate_avg_order_kpi(self, date_filter: str = None) -> Optional[KPIMetric]:
        """حساب KPI متوسط قيمة الطلب"""
        try:
            date_condition = ""
            params = []

            if date_filter:
                date_condition = "AND DATE(created_at) = ?"
                params.append(date_filter)

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT AVG(total_amount) as avg_order_value
                    FROM sales
                    WHERE status = 'completed' {date_condition}
                """, params)

                result = cursor.fetchone()
                current_value = result[0] or 0

                return KPIMetric(
                    kpi_id='KPI_AVG_ORDER_VALUE',
                    name='متوسط قيمة الطلب',
                    value=current_value,
                    target_value=500.0,
                    unit='SAR',
                    trend='stable',
                    calculation_date=datetime.now()
                )

        except Exception as e:
            self.logger.error(f"فشل في حساب KPI متوسط الطلب: {e}")
            return None

    # طرق مساعدة للتصدير
    def _export_csv(self, report: GeneratedReport, filepath: str) -> None:
        """تصدير كـ CSV"""
        data = report.generated_data.get('data', [])
        if data:
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')

    def _export_excel(self, report: GeneratedReport, filepath: str) -> None:
        """تصدير كـ Excel"""
        data = report.generated_data.get('data', [])
        if data:
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False, engine='openpyxl')

    def _export_pdf(self, report: GeneratedReport, filepath: str) -> None:
        """تصدير كـ PDF"""
        # تنفيذ بسيط - يمكن تحسينه باستخدام reportlab
        data = report.generated_data.get('data', [])
        if data:
            df = pd.DataFrame(data)
            # حفظ كـ HTML أولاً ثم تحويل لـ PDF
            html_content = df.to_html(index=False)
            with open(filepath.replace('.pdf', '.html'), 'w', encoding='utf-8') as f:
                f.write(html_content)

    def _update_report_file_path(self, report_id: str, filepath: str) -> None:
        """تحديث مسار ملف التقرير"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE generated_reports
                    SET file_path = ?
                    WHERE report_id = ?
                """, (filepath, report_id))
                conn.commit()
        except Exception as e:
            self.logger.error(f"فشل في تحديث مسار الملف: {e}")

    def _get_generated_report(self, report_id: str) -> Optional[GeneratedReport]:
        """الحصول على تقرير مولد"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM generated_reports WHERE report_id = ?
                """, (report_id,))

                row = cursor.fetchone()
                if row:
                    return GeneratedReport(
                        report_id=row[0],
                        template_id=row[1],
                        report_name=row[2],
                        parameters=json.loads(row[3]) if row[3] else {},
                        generated_data=json.loads(row[4]) if row[4] else {},
                        execution_time=row[5] or 0,
                        row_count=row[6] or 0,
                        generated_by=row[7]
                    )
                return None
        except Exception as e:
            self.logger.error(f"فشل في الحصول على التقرير المولد: {e}")
            return None

    def _get_default_parameters(self, template: ReportTemplate) -> Dict[str, Any]:
        """الحصول على المعلمات الافتراضية للقالب"""
        # معلمات افتراضية بسيطة - يمكن تحسينها
        return {
            'start_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d')
        }
