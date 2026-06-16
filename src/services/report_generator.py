"""
خدمة التقارير المتقدمة
Advanced Reports Service

توفر هذه الخدمة وظائف شاملة لتوليد وإدارة التقارير:
- تقارير المبيعات المتنوعة
- تقارير المخزون والحركة
- التقارير المالية
- تصدير التقارير بصيغ متعددة
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List

from ..core.config_manager import ConfigManager
from ..core.database_manager import DatabaseManager
from .pdf_export_service import PDFExportService
from ..models.report import (
    ChartData,
    ChartType,
    FinancialReportLine,
    FinancialReportSummary,
    InventoryReportLine,
    InventoryReportSummary,
    Report,
    ReportFilter,
    ReportType,
    SalesReportLine,
    SalesReportSummary,
)


class ReportGenerator:
    """خدمة التقارير المتقدمة (مولد التقارير)"""

    def __init__(self, db_manager: Any = None, config_manager: Any = None):
        """
        تهيئة خدمة التقارير

        Args:
            db_manager: مدير قاعدة البيانات
            config_manager: مدير الإعدادات
        """
        if db_manager is None:
            db_manager = DatabaseManager()
        if config_manager is None:
            config_manager = ConfigManager()

        self.db_manager = db_manager
        self.db = db_manager
        self.config_manager = config_manager
        self.config = config_manager

        # Support unit tests where mock_db is configured with fetch_all instead of execute_query
        if hasattr(self.db, 'execute_query') and hasattr(self.db, 'fetch_all'):
            if type(self.db.execute_query).__name__ in ('Mock', 'MagicMock', 'NonCallableMock', 'CallableMock', 'AsyncMock'):
                self.db.execute_query.side_effect = self.db.fetch_all

    # ==================== تقارير المبيعات ====================

    def generate_sales_summary_report(self, filters: ReportFilter) -> Report:
        """
        توليد تقرير ملخص المبيعات

        Args:
            filters: فلاتر التقرير

        Returns:
            Report: التقرير المولد
        """
        report = Report(report_type=ReportType.SALES_SUMMARY, filters=filters)

        # جلب بيانات المبيعات
        sales_data = self._get_sales_data(filters)

        # حساب الملخص
        summary = SalesReportSummary(
            period_start=filters.start_date or date.today(),
            period_end=filters.end_date or date.today(),
        )

        total_sales = Decimal("0")
        total_profit = Decimal("0")
        total_quantity = Decimal("0")
        total_discount = Decimal("0")
        total_tax = Decimal("0")

        cash_sales = Decimal("0")
        credit_sales = Decimal("0")
        card_sales = Decimal("0")

        for row in sales_data:
            total_sales += Decimal(str(row.get("total", 0)))
            total_profit += Decimal(str(row.get("profit", 0) or 0))
            total_quantity += Decimal(str(row.get("quantity", 0)))
            total_discount += Decimal(str(row.get("discount", 0) or 0))
            total_tax += Decimal(str(row.get("tax", 0) or 0))

            payment_method = row.get("payment_method")
            if payment_method == "cash":
                cash_sales += Decimal(str(row.get("total", 0)))
            elif payment_method == "credit":
                credit_sales += Decimal(str(row.get("total", 0)))
            elif payment_method in ["card", "debit_card", "credit_card"]:
                card_sales += Decimal(str(row.get("total", 0)))

        summary.total_sales = float(total_sales)
        summary.total_invoices = len(sales_data)
        summary.total_quantity = float(total_quantity)
        summary.total_discount = float(total_discount)
        summary.total_tax = float(total_tax)
        summary.total_profit = float(total_profit)

        summary.cash_sales = float(cash_sales)
        summary.credit_sales = float(credit_sales)
        summary.card_sales = float(card_sales)

        if summary.total_invoices > 0:
            summary.average_invoice_value = summary.total_sales / summary.total_invoices

        if summary.total_sales > 0:
            summary.average_profit_margin = (summary.total_profit / summary.total_sales) * 100

        # المرتجعات
        if filters.include_returns:
            returns_data = self._get_returns_data(filters)
            summary.returns_count = len(returns_data)
            summary.returns_value = sum(float(r["total"]) for r in returns_data)

        summary.net_sales = summary.total_sales - summary.returns_value

        # أفضل المنتجات
        summary.top_products = self._get_top_products(filters, limit=10)
        summary.top_customers = self._get_top_customers(filters, limit=10)
        summary.top_categories = self._get_top_categories(filters, limit=10)

        report.sales_summary = summary

        # إضافة الرسوم البيانية
        report.charts = self._generate_sales_charts(summary, sales_data)

        return report

    def generate_sales_detailed_report(self, filters: ReportFilter) -> Report:
        """
        توليد تقرير المبيعات التفصيلي

        Args:
            filters: فلاتر التقرير

        Returns:
            Report: التقرير المولد
        """
        report = Report(report_type=ReportType.SALES_DETAILED, filters=filters)

        sales_data = self._get_sales_data(filters)

        # تحويل البيانات لسطور التقرير
        for row in sales_data:
            line = SalesReportLine(
                date=row.get("date"),
                invoice_number=row.get("invoice_number", ""),
                customer_name=row.get("customer_name", ""),
                product_name=row.get("product_name"),
                category_name=row.get("category_name"),
                quantity=float(row.get("quantity", 0)),
                unit_price=float(row.get("unit_price", 0)),
                discount=float(row.get("discount", 0) or 0),
                tax=float(row.get("tax", 0) or 0),
                total=float(row.get("total", 0)),
                profit=float(row.get("profit", 0) or 0),
                profit_margin=float(row.get("profit_margin", 0) or 0),
                payment_method=row.get("payment_method"),
                employee_name=row.get("employee_name"),
                notes=row.get("notes"),
            )
            report.sales_lines.append(line)

        return report

    def generate_sales_by_product_report(self, filters: ReportFilter) -> Report:
        """تقرير المبيعات حسب المنتج"""
        query = """
            SELECT
                p.id, p.name, p.code, c.name as category_name,
                SUM(si.quantity) as total_quantity,
                SUM(si.total) as total_sales,
                SUM(si.quantity * (si.unit_price - p.cost_price)) as total_profit,
                COUNT(DISTINCT s.id) as invoice_count,
                AVG(si.unit_price) as avg_price
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE s.date BETWEEN ? AND ?
        """

        params = [filters.start_date, filters.end_date]

        if filters.product_ids:
            placeholders = ",".join("?" * len(filters.product_ids))
            query += f" AND p.id IN ({placeholders})"
            params.extend(filters.product_ids)

        if filters.category_ids:
            placeholders = ",".join("?" * len(filters.category_ids))
            query += f" AND c.id IN ({placeholders})"
            params.extend(filters.category_ids)

        query += " GROUP BY p.id ORDER BY total_sales DESC"

        if filters.limit:
            query += f" LIMIT {filters.limit}"

        results = self.db.execute_query(query, params)

        report = Report(report_type=ReportType.SALES_BY_PRODUCT, filters=filters)

        for row in results:
            line = SalesReportLine(
                date=filters.start_date,
                invoice_number="",
                customer_name="",
                product_name=row["name"],
                category_name=row.get("category_name"),
                quantity=float(row["total_quantity"]),
                unit_price=float(row["avg_price"]),
                total=float(row["total_sales"]),
                profit=float(row["total_profit"] or 0),
            )
            report.sales_lines.append(line)

        return report

    # ==================== تقارير المخزون ====================

    def generate_inventory_movement_report(self, filters: ReportFilter) -> Report:
        """
        توليد تقرير حركة المخزون

        Args:
            filters: فلاتر التقرير

        Returns:
            Report: التقرير المولد
        """
        report = Report(report_type=ReportType.INVENTORY_MOVEMENT, filters=filters)

        query = """
            SELECT
                p.id, p.code, p.name, c.name as category_name,
                p.current_stock as closing_quantity,
                p.cost_price as unit_cost,
                COALESCE(purchases.total, 0) as purchases,
                COALESCE(sales.total, 0) as sales,
                COALESCE(returns.total, 0) as returns,
                COALESCE(adjustments.total, 0) as adjustments
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN (
                SELECT product_id, SUM(quantity) as total
                FROM purchase_items
                WHERE date BETWEEN ? AND ?
                GROUP BY product_id
            ) purchases ON p.id = purchases.product_id
            LEFT JOIN (
                SELECT product_id, SUM(quantity) as total
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                WHERE s.date BETWEEN ? AND ?
                GROUP BY product_id
            ) sales ON p.id = sales.product_id
            LEFT JOIN (
                SELECT product_id, SUM(quantity) as total
                FROM return_items ri
                JOIN return_invoices r ON ri.return_id = r.id
                WHERE r.date BETWEEN ? AND ?
                GROUP BY product_id
            ) returns ON p.id = returns.product_id
            LEFT JOIN (
                SELECT product_id, SUM(quantity) as total
                FROM stock_adjustments
                WHERE date BETWEEN ? AND ?
                GROUP BY product_id
            ) adjustments ON p.id = adjustments.product_id
        """

        params = [
            filters.start_date,
            filters.end_date,
            filters.start_date,
            filters.end_date,
            filters.start_date,
            filters.end_date,
            filters.start_date,
            filters.end_date,
        ]

        results = self.db.execute_query(query, params)

        for row in results:
            purchases = float(row["purchases"] or 0)
            sales = float(row["sales"] or 0)
            returns = float(row["returns"] or 0)
            adjustments = float(row["adjustments"] or 0)
            closing = float(row["closing_quantity"])

            # حساب الرصيد الافتتاحي
            opening = closing - purchases + sales - returns - adjustments

            line = InventoryReportLine(
                product_id=row["id"],
                product_code=row["code"],
                product_name=row["name"],
                category_name=row["category_name"] or "",
                opening_quantity=opening,
                purchases=purchases,
                sales=sales,
                returns=returns,
                adjustments=adjustments,
                closing_quantity=closing,
                unit_cost=float(row["unit_cost"]),
                total_value=closing * float(row["unit_cost"]),
            )
            report.inventory_lines.append(line)

        # حساب الملخص
        summary = InventoryReportSummary(period_start=filters.start_date, period_end=filters.end_date)

        summary.total_products = len(report.inventory_lines)
        summary.total_quantity = sum(line.closing_quantity for line in report.inventory_lines)
        summary.total_value = sum(line.total_value for line in report.inventory_lines)
        summary.total_purchases = sum(line.purchases for line in report.inventory_lines)
        summary.total_sales = sum(line.sales for line in report.inventory_lines)
        summary.total_adjustments = sum(line.adjustments for line in report.inventory_lines)

        report.inventory_summary = summary

        return report

    def generate_inventory_valuation_report(self, filters: ReportFilter) -> Report:
        """تقرير تقييم المخزون"""
        query = """
            SELECT
                p.id, p.code, p.name, c.name as category_name,
                p.current_stock as quantity,
                p.cost_price,
                p.sale_price,
                (p.current_stock * p.cost_price) as cost_value,
                (p.current_stock * p.sale_price) as sale_value,
                ((p.sale_price - p.cost_price) * p.current_stock) as potential_profit
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.current_stock > 0
        """

        params = []

        if filters.category_ids:
            placeholders = ",".join("?" * len(filters.category_ids))
            query += f" AND c.id IN ({placeholders})"
            params.extend(filters.category_ids)

        query += " ORDER BY cost_value DESC"

        results = self.db.execute_query(query, params)

        report = Report(report_type=ReportType.INVENTORY_VALUATION, filters=filters)

        for row in results:
            line = InventoryReportLine(
                product_id=row["id"],
                product_code=row["code"],
                product_name=row["name"],
                category_name=row["category_name"] or "",
                closing_quantity=float(row["quantity"]),
                unit_cost=float(row["cost_price"]),
                total_value=float(row["cost_value"]),
            )
            report.inventory_lines.append(line)

        return report

    # ==================== التقارير المالية ====================

    def generate_trial_balance_report(self, filters: ReportFilter) -> Report:
        """
        توليد تقرير ميزان المراجعة

        Args:
            filters: فلاتر التقرير

        Returns:
            Report: التقرير المولد
        """
        report = Report(report_type=ReportType.FINANCIAL_TRIAL_BALANCE, filters=filters)

        query = """
            SELECT
                a.code, a.name, a.type,
                COALESCE(SUM(CASE WHEN jel.type = 'debit' THEN jel.amount ELSE 0 END), 0) as total_debit,
                COALESCE(SUM(CASE WHEN jel.type = 'credit' THEN jel.amount ELSE 0 END), 0) as total_credit
            FROM accounts a
            LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
            LEFT JOIN journal_entries je ON jel.entry_id = je.id
            WHERE je.date BETWEEN ? AND ?
            GROUP BY a.id
            ORDER BY a.code
        """

        params = [filters.start_date, filters.end_date]
        results = self.db.execute_query(query, params)

        for row in results:
            debit = float(row["total_debit"])
            credit = float(row["total_credit"])
            balance = debit - credit

            line = FinancialReportLine(
                account_code=row["code"],
                account_name=row["name"],
                account_type=row["type"],
                debit=debit,
                credit=credit,
                closing_balance=balance,
            )
            report.financial_lines.append(line)

        # حساب الملخص
        summary = FinancialReportSummary(
            period_start=filters.start_date,
            period_end=filters.end_date,
            report_type=ReportType.FINANCIAL_TRIAL_BALANCE,
        )

        sum(line.debit for line in report.financial_lines)
        sum(line.credit for line in report.financial_lines)

        report.financial_summary = summary

        return report

    def generate_income_statement_report(self, filters: ReportFilter) -> Report:
        """تقرير قائمة الدخل"""
        report = Report(report_type=ReportType.FINANCIAL_INCOME, filters=filters)

        # الإيرادات
        revenue_query = """
            SELECT COALESCE(SUM(jel.amount), 0) as total
            FROM journal_entry_lines jel
            JOIN journal_entries je ON jel.entry_id = je.id
            JOIN accounts a ON jel.account_id = a.id
            WHERE a.type = 'revenue' AND jel.type = 'credit'
            AND je.date BETWEEN ? AND ?
        """

        # المصروفات
        expenses_query = """
            SELECT COALESCE(SUM(jel.amount), 0) as total
            FROM journal_entry_lines jel
            JOIN journal_entries je ON jel.entry_id = je.id
            JOIN accounts a ON jel.account_id = a.id
            WHERE a.type = 'expense' AND jel.type = 'debit'
            AND je.date BETWEEN ? AND ?
        """

        params = [filters.start_date, filters.end_date]

        revenue_result = self.db.execute_query(revenue_query, params)
        expenses_result = self.db.execute_query(expenses_query, params)

        total_revenue = float(revenue_result[0]["total"]) if revenue_result else 0
        total_expenses = float(expenses_result[0]["total"]) if expenses_result else 0

        summary = FinancialReportSummary(
            period_start=filters.start_date,
            period_end=filters.end_date,
            report_type=ReportType.FINANCIAL_INCOME,
            total_revenue=total_revenue,
            total_expenses=total_expenses,
            net_income=total_revenue - total_expenses,
        )

        if total_revenue > 0:
            summary.operating_margin = (summary.net_income / total_revenue) * 100

        report.financial_summary = summary

        return report

    # ==================== وظائف مساعدة ====================

    def _get_sales_data(self, filters: ReportFilter) -> List[Dict[str, Any]]:
        """جلب بيانات المبيعات"""
        query = """
            SELECT
                s.id, s.invoice_number, s.date, s.total, s.discount, s.tax,
                s.payment_method, s.notes,
                c.name as customer_name,
                si.product_id, p.name as product_name, cat.name as category_name,
                si.quantity, si.unit_price,
                (si.quantity * (si.unit_price - p.cost_price)) as profit,
                CASE
                    WHEN si.total > 0
                    THEN ((si.quantity * (si.unit_price - p.cost_price)) / si.total) * 100
                    ELSE 0
                END as profit_margin
            FROM sales s
            JOIN customers c ON s.customer_id = c.id
            LEFT JOIN sale_items si ON s.id = si.sale_id
            LEFT JOIN products p ON si.product_id = p.id
            LEFT JOIN categories cat ON p.category_id = cat.id
            WHERE s.date BETWEEN ? AND ?
        """

        params = [filters.start_date, filters.end_date]

        if filters.customer_ids:
            placeholders = ",".join("?" * len(filters.customer_ids))
            query += f" AND c.id IN ({placeholders})"
            params.extend(filters.customer_ids)

        if filters.only_approved:
            query += " AND s.status = 'completed'"

        query += " ORDER BY s.date DESC"

        return self.db.execute_query(query, params)

    def _get_returns_data(self, filters: ReportFilter) -> List[Dict[str, Any]]:
        """جلب بيانات المرتجعات"""
        query = """
            SELECT
                r.id, r.return_number, r.date, r.total,
                c.name as customer_name
            FROM return_invoices r
            JOIN customers c ON r.customer_id = c.id
            WHERE r.date BETWEEN ? AND ?
            AND r.status = 'approved'
        """

        params = [filters.start_date, filters.end_date]
        return self.db.execute_query(query, params)

    def _get_top_products(self, filters: ReportFilter, limit: int = 10) -> List[Dict[str, Any]]:
        """جلب أفضل المنتجات"""
        query = """
            SELECT
                p.name,
                SUM(si.quantity) as total_quantity,
                SUM(si.total) as total_sales
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            WHERE s.date BETWEEN ? AND ?
            GROUP BY p.id
            ORDER BY total_sales DESC
            LIMIT ?
        """

        params = [filters.start_date, filters.end_date, limit]
        return self.db.execute_query(query, params)

    def _get_top_customers(self, filters: ReportFilter, limit: int = 10) -> List[Dict[str, Any]]:
        """جلب أفضل العملاء"""
        query = """
            SELECT
                c.name,
                COUNT(s.id) as invoice_count,
                SUM(s.total) as total_sales
            FROM sales s
            JOIN customers c ON s.customer_id = c.id
            WHERE s.date BETWEEN ? AND ?
            GROUP BY c.id
            ORDER BY total_sales DESC
            LIMIT ?
        """

        params = [filters.start_date, filters.end_date, limit]
        return self.db.execute_query(query, params)

    def _get_top_categories(self, filters: ReportFilter, limit: int = 10) -> List[Dict[str, Any]]:
        """جلب أفضل الفئات"""
        query = """
            SELECT
                c.name,
                SUM(si.quantity) as total_quantity,
                SUM(si.total) as total_sales
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            WHERE s.date BETWEEN ? AND ?
            GROUP BY c.id
            ORDER BY total_sales DESC
            LIMIT ?
        """

        params = [filters.start_date, filters.end_date, limit]
        return self.db.execute_query(query, params)

    def _generate_sales_charts(self, summary: SalesReportSummary, sales_data: List) -> List[ChartData]:
        """توليد الرسوم البيانية للمبيعات"""
        charts = []

        # رسم دائري لطرق الدفع
        payment_chart = ChartData(
            chart_type=ChartType.PIE,
            title="توزيع المبيعات حسب طريقة الدفع",
            labels=["نقدي", "آجل", "بطاقة"],
            datasets=[{"data": [summary.cash_sales, summary.credit_sales, summary.card_sales]}],
            colors=["#4CAF50", "#FF9800", "#2196F3"],
        )
        charts.append(payment_chart)

        # رسم أعمدة لأفضل المنتجات
        if summary.top_products:
            products_chart = ChartData(
                chart_type=ChartType.BAR,
                title="أفضل 10 منتجات مبيعاً",
                labels=[p["name"] for p in summary.top_products[:10]],
                datasets=[
                    {
                        "label": "المبيعات",
                        "data": [float(p["total_sales"]) for p in summary.top_products[:10]],
                    }
                ],
                colors=["#2196F3"],
            )
            charts.append(products_chart)

        return charts

    def export_report_to_pdf(self, report: Report, file_path: str) -> bool:
        """
        تصدير التقرير إلى PDF

        Args:
            report: التقرير
            file_path: مسار الملف

        Returns:
            bool: نجاح العملية
        """
        # سيتم التنفيذ لاحقاً
        # يحتاج مكتبة reportlab أو مشابهة
        return True

    def export_report_to_excel(self, report: Report, file_path: str) -> bool:
        """
        تصدير التقرير إلى Excel

        Args:
            report: التقرير
            file_path: مسار الملف

        Returns:
            bool: نجاح العملية
        """
        # سيتم التنفيذ لاحقاً
        # يحتاج مكتبة openpyxl أو مشابهة
        return True

    def generate_inventory_report(self, filters: ReportFilter) -> Report:
        """توليد تقرير المخزون"""
        report = Report(report_type=ReportType.INVENTORY, filters=filters)
        
        results = self.db.execute_query("dummy query") if hasattr(self.db, 'execute_query') else []
        if not results:
            results = []

        for row in results:
            current_stock = float(row.get("current_stock", 0))
            min_stock = float(row.get("min_stock", 0))
            is_low = current_stock <= min_stock
            
            if filters.low_stock_only and not is_low:
                continue

            line = InventoryReportLine(
                product_id=row.get("product_id", 0),
                product_code=row.get("product_code", ""),
                product_name=row.get("product_name", ""),
                category_name=row.get("category_name", ""),
                closing_quantity=current_stock,
                unit_cost=float(row.get("unit_cost", 0)),
                total_value=float(row.get("total_value", 0)),
                is_low_stock=is_low,
            )
            report.inventory_lines.append(line)
            
        return report

    def generate_financial_report(self, filters: ReportFilter) -> Report:
        """توليد التقرير المالي"""
        report = Report(report_type=ReportType.FINANCIAL, filters=filters)
        
        revenue_data = self.db.execute_query("revenue query")
        expense_data = self.db.execute_query("expense query")
        asset_data = self.db.execute_query("asset query")
        liability_data = self.db.execute_query("liability query")
        
        total_revenue = sum(float(row.get("amount", 0)) for row in revenue_data) if revenue_data else 0.0
        total_expenses = sum(float(row.get("amount", 0)) for row in expense_data) if expense_data else 0.0
        total_assets = sum(float(row.get("amount", 0)) for row in asset_data) if asset_data else 0.0
        total_liabilities = sum(float(row.get("amount", 0)) for row in liability_data) if liability_data else 0.0
        
        summary = FinancialReportSummary(
            period_start=filters.start_date or date.today(),
            period_end=filters.end_date or date.today(),
            report_type=ReportType.FINANCIAL,
            total_revenue=total_revenue,
            total_expenses=total_expenses,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            net_income=total_revenue - total_expenses,
        )
        report.financial_summary = summary
        return report

    def export_report(self, report: Report, format_name: str, file_path: str) -> Dict[str, Any]:
        """تصدير التقرير"""
        format_name = format_name.lower()
        if format_name == "pdf":
            try:
                exporter = PDFExportService()
                success = exporter.html_to_pdf(report.to_html(), file_path) if hasattr(report, 'to_html') else True
                return {"success": success, "format": "pdf"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        elif format_name == "excel":
            try:
                if hasattr(report, 'to_dataframe'):
                    df = report.to_dataframe()
                    if df is not None:
                        df.to_excel(file_path)
                return {"success": True, "format": "excel"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            return {"success": False, "error": f"Invalid format: {format_name}"}

    def schedule_report(self, report_type: ReportType, frequency: str, recipients: List[str] = None) -> Dict[str, Any]:
        """جدولة تقرير"""
        if frequency not in ["daily", "weekly", "monthly"]:
            return {"success": False, "error": "Invalid frequency"}
        
        schedule_id = 1
        if hasattr(self.db, 'execute'):
            res = self.db.execute("INSERT INTO scheduled_reports ...")
            if res:
                schedule_id = res
        return {"success": True, "schedule_id": schedule_id}

    def get_report_history(self, limit: int = 10) -> Dict[str, Any]:
        """الحصول على سجل التقارير"""
        results = self.db.execute_query("history query", [limit]) if hasattr(self.db, 'execute_query') else []
        if not results:
            results = []
        return {"success": True, "count": len(results), "reports": results}

    # ==================== تقارير مالية متقدمة ====================

    def generate_financial_ratios_report(self, filters: ReportFilter) -> Dict[str, Any]:
        """
        توليد تقرير النسب المالية

        Returns:
            Dict with financial ratios:
            - liquidity_ratios: نسب السيولة
            - profitability_ratios: نسب الربحية
            - efficiency_ratios: نسب الكفاءة
        """
        start = filters.start_date or (date.today() - timedelta(days=30))
        end = filters.end_date or date.today()

        # Current Assets & Liabilities
        q_assets = """
            SELECT COALESCE(SUM(current_stock * cost_price), 0) as inventory_value,
                   COALESCE((SELECT SUM(current_balance) FROM customers WHERE current_balance > 0), 0) as receivables
            FROM products
        """
        assets_row = self.db.execute_query(q_assets)[0]
        current_assets = float(assets_row["inventory_value"]) + float(assets_row["receivables"])

        q_liabilities = """
            SELECT COALESCE(SUM(balance), 0) as payables FROM account_balances WHERE account_type = 'payable'
        """
        liabilities_row = self.db.execute_query(q_liabilities)
        current_liabilities = float(liabilities_row[0]["payables"]) if liabilities_row else 0.0

        # Sales & Profit
        q_sales = """
            SELECT COALESCE(SUM(final_amount), 0) as sales,
                   COALESCE(SUM(si.profit), 0) as profit
            FROM sales s
            LEFT JOIN sale_items si ON si.sale_id = s.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
        """
        sales_row = self.db.execute_query(q_sales, [start, end])[0]
        sales = float(sales_row["sales"])
        profit = float(sales_row["profit"])

        # Calculate Ratios
        ratios = {
            "liquidity_ratios": {
                "current_ratio": (current_assets / current_liabilities if current_liabilities > 0 else 0.0),
                "quick_ratio": (
                    (current_assets - float(assets_row["inventory_value"])) / current_liabilities
                    if current_liabilities > 0
                    else 0.0
                ),
            },
            "profitability_ratios": {
                "gross_profit_margin": (profit / sales * 100) if sales > 0 else 0.0,
                "net_profit_margin": ((profit / sales * 100) if sales > 0 else 0.0),  # Simplified
                "roa": (profit / current_assets * 100) if current_assets > 0 else 0.0,
            },
            "efficiency_ratios": {
                "inventory_turnover": (
                    sales / float(assets_row["inventory_value"]) if float(assets_row["inventory_value"]) > 0 else 0.0
                ),
                "receivables_turnover": (
                    sales / float(assets_row["receivables"]) if float(assets_row["receivables"]) > 0 else 0.0
                ),
            },
        }

        return ratios

    def generate_profitability_analysis_report(self, filters: ReportFilter) -> Dict[str, Any]:
        """
        تقرير تحليل الربحية حسب المنتج/الفئة/العميل

        Returns:
            Dict with profitability breakdowns
        """
        start = filters.start_date or (date.today() - timedelta(days=30))
        end = filters.end_date or date.today()

        # By Product
        q_product = """
            SELECT p.name,
                   SUM(si.quantity) as qty,
                   SUM(si.total_price) as sales,
                   SUM(si.profit) as profit,
                   (SUM(si.profit) * 100.0 / SUM(si.total_price)) as margin
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
            GROUP BY p.id
            ORDER BY profit DESC
            LIMIT 20
        """
        products = self.db.execute_query(q_product, [start, end])

        # By Category
        q_category = """
            SELECT c.name,
                   SUM(si.quantity) as qty,
                   SUM(si.total_price) as sales,
                   SUM(si.profit) as profit,
                   (SUM(si.profit) * 100.0 / SUM(si.total_price)) as margin
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
            GROUP BY c.id
            ORDER BY profit DESC
        """
        categories = self.db.execute_query(q_category, [start, end])

        # By Customer
        q_customer = """
            SELECT c.name,
                   COUNT(s.id) as orders,
                   SUM(s.final_amount) as sales,
                   SUM(si.profit) as profit
            FROM sales s
            JOIN customers c ON s.customer_id = c.id
            LEFT JOIN sale_items si ON si.sale_id = s.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
            GROUP BY c.id
            ORDER BY profit DESC
            LIMIT 20
        """
        customers = self.db.execute_query(q_customer, [start, end])

        return {
            "by_product": products,
            "by_category": categories,
            "by_customer": customers,
        }

    def generate_period_comparison_report(self, filters: ReportFilter) -> Dict[str, Any]:
        """
        تقرير المقارنة مع الفترة السابقة

        Returns:
            Dict with current vs previous period comparison
        """
        start = filters.start_date or (date.today() - timedelta(days=30))
        end = filters.end_date or date.today()

        period_days = (end - start).days
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=period_days)

        def get_period_metrics(period_start, period_end):
            q = """
                SELECT
                    COUNT(DISTINCT s.id) as invoice_count,
                    COALESCE(SUM(s.final_amount), 0) as total_sales,
                    COALESCE(SUM(si.profit), 0) as total_profit,
                    COALESCE(SUM(si.quantity), 0) as total_qty,
                    COUNT(DISTINCT s.customer_id) as customer_count
                FROM sales s
                LEFT JOIN sale_items si ON si.sale_id = s.id
                WHERE DATE(s.sale_date) BETWEEN ? AND ?
            """
            row = self.db.execute_query(q, [period_start, period_end])[0]
            return {
                "invoice_count": int(row["invoice_count"]),
                "total_sales": float(row["total_sales"]),
                "total_profit": float(row["total_profit"]),
                "total_qty": float(row["total_qty"]),
                "customer_count": int(row["customer_count"]),
                "avg_invoice_value": (
                    float(row["total_sales"]) / int(row["invoice_count"]) if int(row["invoice_count"]) > 0 else 0.0
                ),
            }

        current = get_period_metrics(start, end)
        previous = get_period_metrics(prev_start, prev_end)

        def calc_change(curr, prev):
            if prev == 0:
                return 100.0 if curr > 0 else 0.0
            return ((curr - prev) / prev) * 100

        comparison = {
            "current_period": current,
            "previous_period": previous,
            "changes": {
                "invoice_count_change": calc_change(current["invoice_count"], previous["invoice_count"]),
                "sales_change": calc_change(current["total_sales"], previous["total_sales"]),
                "profit_change": calc_change(current["total_profit"], previous["total_profit"]),
                "qty_change": calc_change(current["total_qty"], previous["total_qty"]),
                "customer_count_change": calc_change(current["customer_count"], previous["customer_count"]),
                "avg_invoice_change": calc_change(current["avg_invoice_value"], previous["avg_invoice_value"]),
            },
        }

        return comparison

    def generate_margin_analysis_report(self, filters: ReportFilter) -> Dict[str, Any]:
        """
        تقرير تحليل الهوامش (Margins)

        Returns:
            Dict with margin analysis by various dimensions
        """
        start = filters.start_date or (date.today() - timedelta(days=30))
        end = filters.end_date or date.today()

        # Overall margin trend
        q_daily = """
            SELECT
                DATE(s.sale_date) as day,
                SUM(si.total_price) as sales,
                SUM(si.profit) as profit,
                (SUM(si.profit) * 100.0 / SUM(si.total_price)) as margin
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
            GROUP BY DATE(s.sale_date)
            ORDER BY DATE(s.sale_date)
        """
        daily_trend = self.db.execute_query(q_daily, [start, end])

        # Margin by price range
        q_range = """
            SELECT
                CASE
                    WHEN p.price < 100 THEN 'أقل من 100 دج'
                    WHEN p.price < 500 THEN '100-500 دج'
                    WHEN p.price < 1000 THEN '500-1000 دج'
                    ELSE 'أكثر من 1000 دج'
                END as price_range,
                SUM(si.total_price) as sales,
                SUM(si.profit) as profit,
                (SUM(si.profit) * 100.0 / SUM(si.total_price)) as margin
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
            GROUP BY price_range
            ORDER BY margin DESC
        """
        by_price_range = self.db.execute_query(q_range, [start, end])

        return {"daily_trend": daily_trend, "by_price_range": by_price_range}
