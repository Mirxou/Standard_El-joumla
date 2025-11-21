# Dashboard Features

This dashboard provides at-a-glance KPIs and charts for sales and inventory performance.

- KPIs
  - Total sales (period), today sales, month-to-date sales
  - Gross profit (computed from `sale_items.profit`)
  - Inventory value (`SUM(products.current_stock * products.cost_price)`)
  - Low-stock count (`current_stock <= min_stock`)
  - Receivables/Payables (from `account_balances`, with receivables fallback to `customers.current_balance`)

- Charts
  - Sales per day (line): aggregates `sales.final_amount` by `DATE(sale_date)`
  - Top products (bar): `SUM(sale_items.total_price)`; filter by category and limit (Top 5/10/15)
  - Distribution donut: selectable by payment method (`sales.payment_method`) or category (`categories.name` via `sale_items`)

- Personalization
  - Period presets: 7, 30, 90 days
  - Toggle visibility for charts; preferences persist via `QSettings`

## Data Seeding
To populate demo data for charts and KPIs:

```powershell
& "C:\Users\pc\Desktop\الإصدار المنطقي trae\.venv\Scripts\python.exe" "C:\Users\pc\Desktop\الإصدار المنطقي trae\scripts\seed_dashboard_sample.py"
& "C:\Users\pc\Desktop\الإصدار المنطقي trae\.venv\Scripts\python.exe" "C:\Users\pc\Desktop\الإصدار المنطقي trae\scripts\test_dashboard_service.py"
```

This seeds 14 days of purchases and sales, several products, customers, and suppliers.

## Notes
- The dashboard queries target the enhanced schema created by `DatabaseManager` and migrations (e.g., `sales.final_amount`, `sale_items.total_price`, `products.min_stock`).
- If your data uses different columns, update `src/services/dashboard_service.py` accordingly.
