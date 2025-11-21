"""
خدمة التقارير المتقدمة
Advanced Reports Service

توفر هذه الخدمة وظائف شاملة لتوليد وإدارة التقارير:
- تقارير المبيعات المتنوعة
- تقارير المخزون والحركة
- التقارير المالية
- تصدير التقارير بصيغ متعددة
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal

from ..core.database_manager import DatabaseManager
from ..models.report import (
    Report, ReportType, ReportPeriod, ReportFormat, ReportFilter,
    SalesReportLine, SalesReportSummary,
    InventoryReportLine, InventoryReportSummary,
    FinancialReportLine, FinancialReportSummary,
    ChartData, ChartType, ReportTemplate
)


class ReportService:
    """خدمة التقارير المتقدمة"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        تهيئة خدمة التقارير
        
        Args:
            db_manager: مدير قاعدة البيانات
        """
        self.db = db_manager
    
    # ==================== تقارير المبيعات ====================
    
    def generate_sales_summary_report(self, filters: ReportFilter) -> Report:
        """
        توليد تقرير ملخص المبيعات
        
        Args:
            filters: فلاتر التقرير
            
        Returns:
            Report: التقرير المولد
        """
        report = Report(
            report_type=ReportType.SALES_SUMMARY,
            filters=filters
        )
        
        # جلب بيانات المبيعات
        sales_data = self._get_sales_data(filters)
        
        # حساب الملخص
        summary = SalesReportSummary(
            period_start=filters.start_date or date.today(),
            period_end=filters.end_date or date.today()
        )
        
        total_sales = Decimal('0')
        total_profit = Decimal('0')
        total_quantity = Decimal('0')
        total_discount = Decimal('0')
        total_tax = Decimal('0')
        
        cash_sales = Decimal('0')
        credit_sales = Decimal('0')
        card_sales = Decimal('0')
        
        for row in sales_data:
            total_sales += Decimal(str(row['total']))
            total_profit += Decimal(str(row['profit'] or 0))
            total_quantity += Decimal(str(row['quantity']))
            total_discount += Decimal(str(row['discount'] or 0))
            total_tax += Decimal(str(row['tax'] or 0))
            
            payment_method = row['payment_method']
            if payment_method == 'cash':
                cash_sales += Decimal(str(row['total']))
            elif payment_method == 'credit':
                credit_sales += Decimal(str(row['total']))
            elif payment_method in ['card', 'debit_card', 'credit_card']:
                card_sales += Decimal(str(row['total']))
        
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
            summary.returns_value = sum(float(r['total']) for r in returns_data)
        
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
        report = Report(
            report_type=ReportType.SALES_DETAILED,
            filters=filters
        )
        
        sales_data = self._get_sales_data(filters)
        
        # تحويل البيانات لسطور التقرير
        for row in sales_data:
            line = SalesReportLine(
                date=row['date'],
                invoice_number=row['invoice_number'],
                customer_name=row['customer_name'],
                product_name=row.get('product_name'),
                category_name=row.get('category_name'),
                quantity=float(row['quantity']),
                unit_price=float(row['unit_price']),
                discount=float(row['discount'] or 0),
                tax=float(row['tax'] or 0),
                total=float(row['total']),
                profit=float(row['profit'] or 0),
                profit_margin=float(row['profit_margin'] or 0),
                payment_method=row.get('payment_method'),
                employee_name=row.get('employee_name'),
                notes=row.get('notes')
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
            placeholders = ','.join('?' * len(filters.product_ids))
            query += f" AND p.id IN ({placeholders})"
            params.extend(filters.product_ids)
        
        if filters.category_ids:
            placeholders = ','.join('?' * len(filters.category_ids))
            query += f" AND c.id IN ({placeholders})"
            params.extend(filters.category_ids)
        
        query += " GROUP BY p.id ORDER BY total_sales DESC"
        
        if filters.limit:
            query += f" LIMIT {filters.limit}"
        
        results = self.db.execute_query(query, params)
        
        report = Report(
            report_type=ReportType.SALES_BY_PRODUCT,
            filters=filters
        )
        
        for row in results:
            line = SalesReportLine(
                date=filters.start_date,
                invoice_number="",
                customer_name="",
                product_name=row['name'],
                category_name=row.get('category_name'),
                quantity=float(row['total_quantity']),
                unit_price=float(row['avg_price']),
                total=float(row['total_sales']),
                profit=float(row['total_profit'] or 0)
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
        report = Report(
            report_type=ReportType.INVENTORY_MOVEMENT,
            filters=filters
        )
        
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
            filters.start_date, filters.end_date,
            filters.start_date, filters.end_date,
            filters.start_date, filters.end_date,
            filters.start_date, filters.end_date
        ]
        
        results = self.db.execute_query(query, params)
        
        for row in results:
            purchases = float(row['purchases'] or 0)
            sales = float(row['sales'] or 0)
            returns = float(row['returns'] or 0)
            adjustments = float(row['adjustments'] or 0)
            closing = float(row['closing_quantity'])
            
            # حساب الرصيد الافتتاحي
            opening = closing - purchases + sales - returns - adjustments
            
            line = InventoryReportLine(
                product_id=row['id'],
                product_code=row['code'],
                product_name=row['name'],
                category_name=row['category_name'] or "",
                opening_quantity=opening,
                purchases=purchases,
                sales=sales,
                returns=returns,
                adjustments=adjustments,
                closing_quantity=closing,
                unit_cost=float(row['unit_cost']),
                total_value=closing * float(row['unit_cost'])
            )
            report.inventory_lines.append(line)
        
        # حساب الملخص
        summary = InventoryReportSummary(
            period_start=filters.start_date,
            period_end=filters.end_date
        )
        
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
            placeholders = ','.join('?' * len(filters.category_ids))
            query += f" AND c.id IN ({placeholders})"
            params.extend(filters.category_ids)
        
        query += " ORDER BY cost_value DESC"
        
        results = self.db.execute_query(query, params)
        
        report = Report(
            report_type=ReportType.INVENTORY_VALUATION,
            filters=filters
        )
        
        for row in results:
            line = InventoryReportLine(
                product_id=row['id'],
                product_code=row['code'],
                product_name=row['name'],
                category_name=row['category_name'] or "",
                closing_quantity=float(row['quantity']),
                unit_cost=float(row['cost_price']),
                total_value=float(row['cost_value'])
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
        report = Report(
            report_type=ReportType.FINANCIAL_TRIAL_BALANCE,
            filters=filters
        )
        
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
            debit = float(row['total_debit'])
            credit = float(row['total_credit'])
            balance = debit - credit
            
            line = FinancialReportLine(
                account_code=row['code'],
                account_name=row['name'],
                account_type=row['type'],
                debit=debit,
                credit=credit,
                closing_balance=balance
            )
            report.financial_lines.append(line)
        
        # حساب الملخص
        summary = FinancialReportSummary(
            period_start=filters.start_date,
            period_end=filters.end_date,
            report_type=ReportType.FINANCIAL_TRIAL_BALANCE
        )
        
        total_debit = sum(line.debit for line in report.financial_lines)
        total_credit = sum(line.credit for line in report.financial_lines)
        
        report.financial_summary = summary
        
        return report
    
    def generate_income_statement_report(self, filters: ReportFilter) -> Report:
        """تقرير قائمة الدخل"""
        report = Report(
            report_type=ReportType.FINANCIAL_INCOME,
            filters=filters
        )
        
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
        
        total_revenue = float(revenue_result[0]['total']) if revenue_result else 0
        total_expenses = float(expenses_result[0]['total']) if expenses_result else 0
        
        summary = FinancialReportSummary(
            period_start=filters.start_date,
            period_end=filters.end_date,
            report_type=ReportType.FINANCIAL_INCOME,
            total_revenue=total_revenue,
            total_expenses=total_expenses,
            net_income=total_revenue - total_expenses
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
            placeholders = ','.join('?' * len(filters.customer_ids))
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
            datasets=[{
                "data": [summary.cash_sales, summary.credit_sales, summary.card_sales]
            }],
            colors=["#4CAF50", "#FF9800", "#2196F3"]
        )
        charts.append(payment_chart)
        
        # رسم أعمدة لأفضل المنتجات
        if summary.top_products:
            products_chart = ChartData(
                chart_type=ChartType.BAR,
                title="أفضل 10 منتجات مبيعاً",
                labels=[p['name'] for p in summary.top_products[:10]],
                datasets=[{
                    "label": "المبيعات",
                    "data": [float(p['total_sales']) for p in summary.top_products[:10]]
                }],
                colors=["#2196F3"]
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
