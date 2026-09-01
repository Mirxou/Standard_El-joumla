# Worklog - Task 2: Login-to-Dashboard Cycle Deep Code Review

**Reviewer:** Automated Code Review Agent
**Date:** 2025-06-30
**Scope:** Complete login-to-dashboard feature cycle
**Files traced:** main.py, login_dialog.py, auth.py, database_manager.py, local_database_manager.py, user_service.py, user.py, security_service.py, sales_service.py, payment_service.py, dashboard_service.py, main_window.py

---

## Bug Report

### Chain 1: main.py → login_dialog → auth → database → dashboard

[CRITICAL] main.py:836: `handle_logout` calls `self.user_service.logout_user(self.current_user.id)` but `logout_user()` (user_service.py:330) expects `session_id: str`, not `user_id: int`. The session is NEVER properly terminated in the database or removed from `active_sessions` dict after logout. The `del self.active_sessions[session_id]` at user_service.py:347 will raise `KeyError` (int key vs str key mismatch) which is silently caught. All sessions persist indefinitely in memory and DB.

[CRITICAL] main.py:911: Same bug duplicated in `cleanup()` — `lambda: self.user_service.logout_user(self.current_user.id)` passes user ID (int) instead of session ID (str). Session cleanup on app exit is broken.

[HIGH] login_dialog.py:785-812: `handle_login()` calls `self.user_service.authenticate_user()` SYNCHRONOUSLY on the main/GUI thread. The `LoginWorker` QThread class exists at lines 178-200 but is NEVER used anywhere — it is dead code. This freezes the entire UI during database authentication, especially noticeable with slow disks or encrypted databases.

[HIGH] main.py:822-845: `handle_logout()` does NOT stop `session_monitor_timer` (60s interval) or `activity_timer` (5min interval) before re-showing the login dialog. These timers, created in `_start_session_monitoring()` (lines 699-710), retain closures referencing the OLD session object. They continue firing after logout, calling `_check_session_validity(session)` and `_update_session_activity(session)` with a stale/orphaned session, causing potential errors.

[HIGH] user_service.py:87-90: `_load_security_settings()` is called at line 87 BEFORE `_create_security_tables()` at line 90. On first run, the `security_settings` table does not exist yet, so the SELECT query at line 148 silently fails (caught at line 164). All security settings (max_login_attempts, lockout_duration, session_timeout, password_min_length, etc.) remain at their hardcoded defaults and are NEVER loaded from the database.

[HIGH] main.py:672-674: `_validate_session_security()` calls `self.user_service.validate_session(session.session_id)` which returns `(is_valid, validated_session)`. The returned `validated_session` (with updated `last_activity` from the DB) is DISCARDED. The method then performs its own timeout check at line 681 using the ORIGINAL `session.last_activity` (stale timestamp). This is a TOCTOU issue — the validated/updated session data is thrown away.

[MEDIUM] user_service.py:92-143 vs security_service.py:24-47: `login_attempts` table is created with INCOMPATIBLE schemas in two places. `UserService._create_security_tables()` defines columns: `(id, username, ip_address, timestamp, success, failure_reason, created_at)`. `SecurityService._ensure_tables()` defines: `(id, username, ip_address, user_agent, success, created_at)`. Since both use `CREATE TABLE IF NOT EXISTS`, whichever runs first wins. The loser's INSERT queries may fail or insert into wrong columns silently.

[MEDIUM] main.py:635-637: When user clicks the dialog's X button (rejects the dialog), `current_attempt` is incremented and the user is asked "هل تريد المحاولة مرة أخرى؟" (Do you want to try again?). The user explicitly cancelled but is prompted to retry, which is confusing UX. The X button should count as a deliberate cancellation, not a failed attempt.

[MEDIUM] login_dialog.py:825-828: The 2FA check queries `user_2fa` table via `self.user_service.db.execute_query()`. If `SecurityService._ensure_tables()` hasn't been called yet (it's called in `LoginDialog.__init__` at line 221, but `execute_query` with `exclude_deleted=True` might interfere), the table might not exist. The exception at line 829 silently sets `needs_2fa = False`, meaning 2FA is BYPASSED if the table is missing.

[MEDIUM] main_window.py:2310-2325: `refresh_dashboard_stats()` uses raw `self.db_manager.connection.execute(query_stats)` directly (line 2312), bypassing `execute_query()`. This SKIPS the soft-delete filter (`is_deleted = 0`) that `LocalDatabaseManager.execute_query()` auto-injects. Deleted products and deleted sales are STILL COUNTED in dashboard KPIs (total_products, total_stock_value, total_sales_count, total_sales_amount).

[MEDIUM] user_service.py:389: `update_session_activity()` returns `False` if `session_id` is not in `self.active_sessions` dict (in-memory only). After an app restart, sessions loaded from the DB via `_load_session_from_db()` during `validate_session()` ARE added back to `active_sessions`. But `update_session_activity()` is called from `_update_session_activity()` in main.py (line 729-735), which runs every 5 minutes. If `validate_session` hasn't been called yet for that session after restart, activity updates silently fail.

### Chain 2: Dashboard KPI loading

[MEDIUM] dashboard_service.py:120-128: `_kpi_gross_profit()` queries `SUM(si.profit)` from `sale_items`. Meanwhile, `main_window.py:2356-2358` calculates profit as `SUM(si.quantity * (si.unit_price - COALESCE(p.cost_price, si.unit_price * 0.7)))`. These are DIFFERENT calculations — the dashboard service trusts the pre-computed `profit` column while main_window recalculates from unit_price and cost_price. If `profit` was stored incorrectly during sale creation, the two views show DIFFERENT profit numbers.

[MEDIUM] dashboard_service.py:302-315: `_kpi_cash_flow()` queries `payments` table filtering by `payment_type = 'received'` and `payment_type = 'paid'`. But the `PaymentType` enum and the actual values stored in `payment_type` column may not match these strings (the column stores values like 'received'/'paid' but the model might use different enum values). If there's a mismatch, cash flow always shows 0.

[LOW] dashboard_service.py:382: `_scalar()` helper uses `list(rows[0].values())[0]` to get the first column value by POSITION, not by column name. This is fragile — if anyone reorders SELECT columns in any KPI query, the wrong value will be returned silently.

### Dict key vs index access

[LOW] main_window.py:2330-2338: `refresh_dashboard_stats()` accesses results by tuple index (`row[0]`, `row[1]`, etc.) from raw `cursor.fetchone()`. This works because the query has a fixed column order, but is fragile compared to named access.

[LOW] main_window.py:2664-2669: `refresh_dashboard_data()` has dual-path logic: if result is dict, uses `.get("total_sales")`; if not dict, uses `[0]` index. The `_db_fetch_one` helper and `fetch_one` return DictRow (dict subclass), so the index path (`[0]`, `[1]`) is effectively dead code but adds complexity.

### Error paths

[MEDIUM] login_dialog.py:789-797: Empty username/password validation exists and shows error. However, whitespace-only passwords pass validation — `self.password_edit.text()` at line 787 does NOT strip whitespace, so a password of all spaces is accepted and sent to `authenticate_user()`, which will fail with "wrong password" rather than "empty password".

[MEDIUM] main.py:660-663: If `show_mandatory_login_dialog()` encounters an exception (e.g., LoginDialog constructor fails), `current_attempt` is incremented. After 3 such exceptions, the app quits. If `LoginDialog.__init__` crashes (e.g., missing font, missing asset), the user has only 2 visible retry attempts before the app force-quits with no useful error message.

[LOW] login_dialog.py:848-858: On 2FA failure, `self.security_service.record_login_attempt()` is called. But this records to `SecurityService`'s `login_attempts` table (different schema from `UserService`'s `login_attempts` table). Failed 2FA attempts are recorded in a DIFFERENT table than failed password attempts, so the brute-force protection in `UserService._is_user_locked()` won't count 2FA failures.

### Dashboard data correctness

[MEDIUM] main_window.py:2312-2325 vs dashboard_service.py: Dashboard has TWO independent data loading paths. `refresh_dashboard_stats()` (main_window.py:2286) runs raw SQL against the DB connection directly, while `DashboardService.load_dashboard()` (dashboard_service.py:24) is PASSED to MainWindow but NEVER CALLED. The `dashboard_service` parameter is stored at line 634 but the dashboard tab uses inline SQL queries instead. If someone fixes bugs in one path, the other remains broken.

[LOW] main_window.py:2413-2419: The "average basket" query uses `AVG(final_amount)` from the `sales` table, but `final_amount` might be 0 for cash sales or free items. The query includes `WHERE final_amount > 0` which is correct, but doesn't filter by date, so it averages over ALL historical sales, making the metric potentially misleading.

### Logout flow trace

[HIGH] main.py:822-845 → user_service.py:330-341: Complete logout flow: (1) MainWindow.logout() shows confirmation → (2) emits `logout_requested` signal → (3) main.py `handle_logout()` closes main_window → (4) calls `logout_user(self.current_user.id)` — WRONG PARAMETER TYPE (int vs str) → (5) session NEVER terminated in DB → (6) `show_mandatory_login_dialog()` re-shows login. **BUGS:** Session not terminated, timers not stopped, stale session references kept.

[HIGH] main.py:699-710 vs 822-845: Session monitoring timers created in `_start_session_monitoring()` are never stopped in `handle_logout()`. After logout, `_check_session_validity(old_session)` fires every 60s and `_update_session_activity(old_session)` fires every 5min with orphaned session object. If the user successfully logs in again, a NEW set of timers is created for the new session, but OLD timers also keep running.

---

## Summary Statistics

| Severity | Count |
|----------|-------|
| CRITICAL | 2     |
| HIGH     | 6     |
| MEDIUM   | 9     |
| LOW      | 6     |
| TOTAL    | 23    |

## Top Priority Fixes (CRITICAL + HIGH)

1. **Fix logout to pass session_id instead of user_id** — Store the session_id on the app object when login succeeds, use it in handle_logout and cleanup.
2. **Stop session monitoring timers on logout** — Add timer.stop() calls in handle_logout before re-showing login dialog.
3. **Use the LoginWorker thread** — Or remove the dead code and add a loading indicator for the synchronous auth call.
4. **Fix _create_security_tables call order** — Move _load_security_settings() AFTER _create_security_tables() in UserService.__init__.
5. **Use validated_session in _validate_session_security** — Use the returned validated_session instead of the original stale session object.
6. **Reconcile login_attempts table schemas** — Unify the schema between UserService and SecurityService.
7. **Fix dashboard soft-delete bypass** — Use execute_query() instead of raw connection.execute() in refresh_dashboard_stats.

---

# Worklog - Task 3: Sales Feature Cycle Deep Code Review

**Reviewer:** Automated Code Review Agent
**Date:** 2025-07-01
**Scope:** Complete sales feature cycle (create, list, edit, cancel, delete, items)
**Files traced:** sales_dialog.py, sales_service.py, sale.py, sale_repository.py, sale_item_repository.py, sales_table_model.py, main_window.py (sales tab + SalesDataLoaderThread), database_manager.py, local_database_manager.py

**CRITICAL CONTEXT:** `fetch_one`/`fetch_all` return `Dict[str, Any]` via `DictRow` class (local_database_manager.py:1065). `DatabaseManager.fetch_one`/`fetch_all` return plain `dict`. Raw `cursor.fetchone()` returns tuples. Access patterns must match the return type.

---

## Bug Report

### Flow 1: Creating a New Sale (UI Dialog → Service → Model → DB)

[CRITICAL] sales_dialog.py:1684: `item.discount_amount` accessed on `SaleItem` object, but `SaleItem` dataclass (sale.py:88-107) has NO `discount_amount` field. It has `discount` and `discount_percentage`. This crashes with `AttributeError` when `load_sale_items()` is called during **editing** an existing sale. The `load_sale_items` method at line 1684 constructs cart dicts and tries `to_decimal(item.discount_amount)`. This means **editing any existing sale always crashes**.

[CRITICAL] sales_service.py:767: `self.sale_manager.add_sale_item(item)` — `SaleManager` class has NO `add_sale_item` method. The method `SalesService.add_sale_item()` (lines 746-767) calls this non-existent method, raising `AttributeError` at runtime. This entire service method is broken.

[CRITICAL] sale.py:488 + sales_service.py:128: **Nested transaction / double-commit.** `SalesService.create_sale()` wraps everything in `db_manager.transaction()` (BEGIN IMMEDIATE at local_database_manager.py:957). Inside, `SaleManager.create_sale()` obtains the same `connection` object (line 429) and calls `connection.commit()` at line 488. This commits the OUTER transaction prematurely. If subsequent steps inside `SalesService.create_sale` fail (inventory adjustment line 142, accounting line 151, customer balance line 167), the sale is already committed and CANNOT be rolled back. The outer `transaction()` context's rollback at line 961 becomes a no-op.

[HIGH] sale.py:522-589: **`_create_sale_legacy` has no transaction.** Each operation auto-commits independently: `execute_insert` (sale header, line 576), `_create_sale_item` per item (each with its own `execute_insert`, line 580), and `_update_stock_for_sale` (line 581-582, which calls `execute_query` which auto-commits UPDATEs at local_database_manager.py:1059). If any item insert fails after the first, an **orphaned sale header** is left in the DB with missing items and stock already deducted.

[HIGH] sale.py:139-148 + sales_service.py:101-118: **Stock validated BEFORE transaction, TOCTOU race.** `SalesService.create_sale` validates stock availability at line 108-118 (reads `current_stock`), then enters the transaction at line 128. Between validation and actual deduction, another thread/process could sell the same stock. The stock check and deduction are NOT atomic.

[HIGH] sales_dialog.py:1558-1559 vs sale.py:366-382: **Invoice number format conflict.** `SalesDialog._generate_invoice_number()` generates `INV-YYYYMMDDHHMMSS` (timestamp-based, no sequential gap protection). `SaleManager.generate_invoice_number()` and `SalesService._generate_invoice_number()` generate `INV-YYYYMMDD-XXXX` (sequential per day). When the dialog calls `create_new_sale()` at line 1524, it generates a timestamp-based invoice number. Then at save time, `SalesService.create_sale()` at line 83-84 regenerates it if empty—but the dialog already set it. The sequential numbering scheme is bypassed.

[MEDIUM] sales_service.py:101-118: Stock validation uses `product.current_stock` from `get_product_by_id()`, which reads the `current_stock` column directly. But `_update_stock_in_transaction` (sale.py:934-1008) deducts from both `batches.quantity` AND `products.current_stock`. The validation checks `current_stock` but the deduction happens per-batch via FEFO. If a product has stock spread across multiple batches, validation passes but FEFO deduction could fail mid-way if individual batches are insufficient (handled by auto-conversion, but adds complexity and potential failure modes).

### Flow 2: Viewing Sale List (table population, filtering, search)

[CRITICAL] main_window.py:5128-5134,5139-5145 + main_window.py:428-434: **Status and payment filters ALWAYS produce zero results.** `refresh_sales_data()` maps Arabic UI text to English values: `"مسودة" → "draft"`, `"نقدي" → "cash"`, etc. (lines 5127-5145). These English values are passed to `SalesDataLoaderThread` which filters with `AND s.status = ?` (line 429) and `AND s.payment_method = ?` (line 433). But the database stores **Arabic** enum values: `SaleStatus.DRAFT.value` = `"مسودة"`, `PaymentMethod.CASH.value` = `"نقدي"`. The filter comparisons can NEVER match. Selecting any status or payment filter returns an empty table.

[MEDIUM] main_window.py:5148-5178: **Dead code block.** `load_sales()` function (lines 5148-5178) is defined inside `refresh_sales_data()` but is NEVER called. At line 5190, a `SalesDataLoaderThread` is created instead, making the entire `load_sales` function dead code. The dead code calls `self.sales_service.list_sales(...)` and `self.sales_service.get_sales_summary()`, neither of which exist on `SalesService`—further confirming this path was never viable.

[MEDIUM] sale.py:1586-1607: **`search_sales` only searches by invoice_number.** The method builds `WHERE invoice_number LIKE ?` but ignores customer_name. A user searching for a customer's name gets zero results. The `SalesDataLoaderThread` in main_window.py (line 424) correctly searches both `invoice_number` and `c.name`, creating an inconsistency between the two search paths.

[MEDIUM] sale.py:1969-1990: **`get_sales_by_status` doesn't normalize status values.** Accepts a raw `status: str` parameter and filters with `WHERE status = ?`. If called with English "paid" but the DB stores "مدفوعة", no results. The `parse_status` function exists to handle this but is never used here.

[LOW] sale.py:1751,1802: **Positional access on dict values in aggregate queries.** `get_sales_summary` and `get_sales_report` use `list(row.values())[idx]` for positional access on dicts returned by `fetch_one`. The SQL uses unaliased aggregates like `COUNT(*)`, `SUM(total_amount)`. Dict key names depend on the SQL engine's column naming, which may vary. Named aliases should be used.

### Flow 3: Editing/Updating an Existing Sale

[CRITICAL] sales_dialog.py:1684: (Same as Flow 1) `item.discount_amount` crashes on `SaleItem` which has no such attribute. **Editing a sale is completely broken.**

[HIGH] sale.py:1292-1416: **Update stock adjustment is non-atomic in the fallback path.** When `get_cursor` is unavailable (line 1338), the fallback at lines 1398-1415 performs three separate operations outside a transaction: (1) `_update_stock_for_sale(old_items, "return")`, (2) `DELETE FROM sale_items`, (3) `_create_sale_item` per new item, (4) `_update_stock_for_sale(new_items, "sale")`. Each call to `execute_query`/`execute_non_query` auto-commits. If step 3 or 4 fails, old stock was already returned but new stock not deducted—**double-counting stock**.

[MEDIUM] sale.py:1310-1336: **`get_cursor` context swallows errors silently.** The `try/except` at lines 1310-1336 catches ALL exceptions and falls through to the non-atomic fallback path. This means transient errors (like brief locks) that could be retried instead cause a silent fallback to the buggy non-atomic path.

[LOW] sales_dialog.py:1793: **Edit mode always sets sale_date to today.** Line 1793: `self.sale.sale_date = date.today()`. When editing an existing sale, the original sale date is overwritten with today's date. The date should be preserved from the existing sale.

### Flow 4: Cancelling a Sale (stock restoration, status update, atomicity)

[HIGH] sales_service.py:195: **Already-cancelled detection is broken.** The check is `status == SaleStatus.CANCELLED.value or status == "cancelled"`. But `sale.status` (after `parse_status`) is a `SaleStatus` enum member, not a string. `SaleStatus.CANCELLED == SaleStatus.CANCELLED.value` is `False` (enum vs BilingualString). `SaleStatus.CANCELLED == "cancelled"` is also `False`. So the guard NEVER detects an already-cancelled sale. Calling `cancel_sale` on a cancelled sale will **double-restore stock**.

[HIGH] sale.py:1661-1691 + local_database_manager.py:1059: **Non-atomic cancellation via auto-commit.** `SaleManager.cancel_sale` calls `_update_stock_for_sale(sale.items, "return")` which uses `execute_query(UPDATE ...)`. For `LocalDatabaseManager`, `execute_query` auto-commits UPDATE statements at line 1059. Stock restoration commits in its own transaction, separate from the status update at line 1678. If the status update fails, stock is already restored with no rollback.

[HIGH] sale.py:1904-1912: **Soft-delete sets wrong status value.** `delete_sale` with `soft_delete=True` sets `status = 'cancelled'` (English literal). But the DB stores Arabic enum values (`SaleStatus.CANCELLED.value` = `"ملغية"`). After soft-delete, the sale has status `'cancelled'` which doesn't match any `SaleStatus` enum value. Code filtering by `status != 'ملغية'` (e.g., `get_daily_summary` at line 721) will still show this record. The `is_deleted` column is NOT set to 1, so `LocalDatabaseManager.execute_query`'s auto-filter also won't exclude it.

[MEDIUM] sale.py:1840-1885: **`process_return` missing rollback on error.** Uses raw `conn.cursor()` with manual `conn.commit()` at line 1879, but the `except` block at line 1881 returns `(False, None)` without calling `conn.rollback()`. If the return processing fails partway (e.g., after restoring some but not all stock), partial changes remain uncommitted and the connection is left in a dirty state with an open transaction.

### Flow 5: Deleting a Sale (soft-delete, cascade effects)

[HIGH] sale.py:1887-1934: **`delete_sale` non-atomic.** Stock restoration at line 1896-1902 uses `_update_stock_for_sale` (auto-commits). The status/update/delete at lines 1904-1922 uses `execute_query` (also auto-commits). These are separate commits. If stock is restored but the DELETE fails, stock is double-counted.

[HIGH] sale.py:1904-1912: (Same as Flow 4) Soft-delete uses English `'cancelled'` instead of Arabic `'ملغية'`, and doesn't set `is_deleted = 1`.

[MEDIUM] sale.py:1913-1922: **Hard delete doesn't set `is_deleted`.** When `soft_delete=False`, the code physically deletes from `sale_items` and `sales` tables but doesn't set `is_deleted = 1` first. While this is a hard delete (records removed), the signals emitted at line 1924 (`sale_deleted`) may trigger listeners that expect soft-deleted records to still exist.

### Flow 6: Sale Items (add/remove, per-item discount, quantity validation)

[CRITICAL] sales_dialog.py:1684: (Same as above) `item.discount_amount` — `SaleItem` has no such attribute.

[HIGH] sales_dialog.py:1015-1026: **Stock validation only checks initial add, not cumulative quantity.** When adding a duplicate product, `new_qty = item["qty"] + Decimal("1")` is checked against `available_stock` (the snapshot from when the product was first loaded, line 995). But if stock was reduced between loads (e.g., by another sale), the `available_stock` value is stale. The validation is against a cached value, not live stock.

[MEDIUM] sales_dialog.py:1737: **Discount is stored as amount but converted to percentage.** The cart stores `discount` as an absolute amount (e.g., 5.00 DA). At save time, line 1737 converts to percentage: `discount_pct = (item["discount"] / line_subtotal * 100)`. But `SaleItem.calculate_total()` at sale.py:141 uses this percentage to recalculate the discount: `self.discount = self._subtotal * (self.discount_percentage / 100)`. Due to Decimal rounding, the recalculated discount may differ by a fraction from the original amount. For example, a 3.33 DA discount on a 100 DA subtotal becomes 3.33% → recalculated as 3.33 DA (likely OK) but on odd amounts like 7 DA on 100 DA → 7% → 7.00 DA (OK). The real issue is the **reverse mapping in `load_sale_items`** at line 1684 uses `item.discount_amount` which doesn't exist, so the loaded discount is always 0.

[MEDIUM] sale.py:138-150: **`SaleItem.calculate_total` has two total fields.** Both `total_price` (line 148) and `total_amount` (line 149) are set to the same value. The DB schema has `total_price` but `total_amount` is only used in-memory. The `_row_to_sale_item` at line 1240 reads `tax_amount` from column index 11, but the SELECT at line 798-812 inserts columns `(sale_id, product_id, batch_id, quantity, unit_price, total_price, cost_price, profit, discount)` — only 9 columns, no `tax_amount` or `tax_percentage`. So `tax_amount` in the loaded SaleItem is always 0.

[LOW] sale.py:762-820: **`_create_sale_item` (non-transaction) doesn't insert tax_percentage.** The INSERT at lines 738-754 omits `tax_percentage` and `tax_amount`. The `_create_sale_item_in_transaction` at lines 798-814 also omits them. So per-item tax is never persisted. Only the sale-level tax is saved.

[LOW] sales_dialog.py:1146: **Delete button captures row index, not item ID.** `partial(self.remove_item, row_idx)` captures the row index at render time. When rows are deleted and the table is re-rendered, the remaining buttons still reference the OLD row indices from before the deletion. However, since `remove_item` triggers a full table re-render (lines 1249-1256), the old buttons are destroyed. This is safe but inefficient.

### Cross-cutting Issues

[HIGH] sale.py:273-306: **`calculate_totals` auto-promotes status based on paid_amount.** Lines 299-305: if `is_paid`, sets status to `PAID`; if partially paid, sets to `PARTIALLY_PAID`. This overwrites the user's explicit status choice. A user cannot save a sale as DRAFT with a partial payment (e.g., for a layaway). The status is always overridden.

[MEDIUM] sales_service.py:520-521: **`get_sales_statistics` references non-existent `payment_status` column.** The SQL at line 520 uses `CASE WHEN payment_status = 'paid'` but the `sales` table has `status` and `paid_amount` columns, not `payment_status`. This causes an SQL error caught by the except at line 538, returning zero statistics.

[MEDIUM] sales_service.py:362: **`_get_sales_statistics` references `si.is_deleted = 0`.** The `sale_items` table does have `is_deleted` (added by migration 002), but this is only set if someone explicitly soft-deletes individual sale items. Normal item deletion via `DELETE FROM sale_items` (sale.py:1404) physically removes the row. So `si.is_deleted = 0` filter only matters if soft-delete was used, which is not the normal flow.

[LOW] sale.py:1089-1097: **`_row_to_sale` gv() fallback to integer index.** The helper `gv(k, i, d)` at line 1089 has a fallback to `row[i]` for non-dict rows. When `fetch_one`/`fetch_all` return dicts (which they always do in both `DatabaseManager` and `LocalDatabaseManager`), the index path is dead code. However, if someone changes the DB layer to return tuples, the hardcoded column indices (e.g., `gv("customer_name", 13)`) would be fragile and position-dependent.

---

## Summary Statistics

| Severity | Count |
|----------|-------|
| CRITICAL | 5     |
| HIGH     | 10    |
| MEDIUM   | 10    |
| LOW      | 5     |
| TOTAL    | 30    |

## Top Priority Fixes (CRITICAL)

1. **Fix `sales_dialog.py:1684`** — Change `item.discount_amount` to `item.discount` (the actual field name on SaleItem). This unblocks the entire edit-sale flow.

2. **Fix `sales_service.py:767`** — `SaleManager` has no `add_sale_item`. Either implement it or restructure `SalesService.add_sale_item` to use `SaleManager.create_sale` or direct SQL.

3. **Fix nested transaction in `sale.py:488`** — `SaleManager.create_sale` must NOT call `connection.commit()` when invoked inside an outer transaction. Add a parameter like `_in_transaction=False` or use savepoints.

4. **Fix status/payment filter mapping in `main_window.py:5127-5145`** — Pass Arabic DB values instead of English, or add a mapping layer in `SalesDataLoaderThread` that maps English → Arabic before querying.

5. **Fix `SalesService.cancel_sale` already-cancelled check at line 195** — Change to `if status == SaleStatus.CANCELLED:` (compare enum to enum, not enum to value).

6. **Fix `sale.py:1904-1908` soft-delete status** — Use `SaleStatus.CANCELLED.value` ("ملغية") instead of English "cancelled", and also set `is_deleted = 1`.

---

# Worklog - Task 4: Purchase/Orders Cycle Deep Code Review

**Reviewer:** Automated Code Review Agent
**Date:** 2025-07-02
**Scope:** Complete purchase orders feature cycle (create, receive, list, edit, cancel, stock update)
**Files reviewed:**
  - src/ui/dialogs/purchase_order_dialog.py
  - src/ui/windows/purchase_orders_window.py
  - src/services/purchase_order_service.py
  - src/models/purchase_order.py
  - src/models/receiving_note.py
  - src/ui/dialogs/receiving_dialog.py
  - src/core/database_manager.py (return types)
  - src/core/local_database_manager.py (return types)
  - migrations/005_create_purchase_orders.sql (schema)

## Bug List

### CRITICAL

1. **[CRITICAL] purchase_order_service.py:256-257 — `update_purchase_order` crashes if `related_invoice_id`/`invoice_matched` columns don't exist**
   The UPDATE SQL includes `related_invoice_id = ?, invoice_matched = ?` but these columns are added dynamically by `ensure_match_columns()`. Editing a PO calls `update_purchase_order` before `ensure_match_columns` is ever invoked, causing an `OperationalError`. The `ensure_match_columns()` is only called from the 3-way match dialog, not from the edit flow.

2. **[CRITICAL] purchase_order_service.py:296-301 — Editing a PO after partial receipt destroys receiving-note references**
   `update_purchase_order` does `DELETE FROM purchase_order_items WHERE purchase_order_id = ?` then re-inserts items with no `id`. Any `receiving_items.po_item_id` foreign keys pointing to the old item IDs become orphaned. Subsequent receipt attempts fail to match items by ID, so `receive_shipment` cannot update PO item quantities.

3. **[CRITICAL] purchase_order_dialog.py:414 — `_on_product_changed` receives combo index instead of table row**
   `product_combo.currentIndexChanged.connect(lambda r=row: self._on_product_changed(r))` — the signal passes the combo box index as the argument, overriding the default `r=row`. When a user changes the product in any row after the first, `_on_product_changed` is called with the combo index (0, 1, 2...) instead of the table row number, causing it to update the WRONG row or crash with `None` access.

4. **[CRITICAL] purchase_order_dialog.py:777 — Same lambda bug in `_add_prefill_products`**
   Identical to bug #3. `product_combo.currentIndexChanged.connect(lambda r=row: self._on_product_changed(r))` passes combo index, not table row.

5. **[CRITICAL] purchase_order_service.py:835-843 — 3-way match `received_amount` is always 0.00**
   `three_way_match` queries `SELECT COALESCE(SUM(total_amount), 0) as total FROM receiving_notes` but the `receiving_notes` table has NO `total_amount` column (confirmed in migration 005). The sum is always NULL → 0. This makes the 3-way match always compare a 0 received amount against the PO and invoice amounts, causing match failures or spurious tolerance violations.

6. **[CRITICAL] purchase_order_service.py:584-655 — Manual transactions (`BEGIN`/`COMMIT`/`ROLLBACK`) are completely ineffective with `LocalDatabaseManager`**
   `receive_shipment` and `create_purchase_order` use `self.db.execute_query("BEGIN TRANSACTION")` / `COMMIT` / `ROLLBACK`. But `LocalDatabaseManager.execute_query()` auto-commits on every INSERT/UPDATE/DELETE (line 1059) and `execute_update()` always calls `self.connection.commit()`. Each write within the "transaction" commits immediately, so a failure midway cannot be rolled back. Data inconsistency is possible (e.g., stock updated but PO status not updated).

### HIGH

7. **[HIGH] purchase_orders_window.py:656-658 — `_update_table_with_pos` is a no-op; filtering by status/priority is completely broken**
   `_filter_pos` calls `_update_table_with_pos(pos)` but the method body is empty (only a comment). The table is never repopulated with filtered results. Users see no change when selecting a status or priority filter.

8. **[HIGH] purchase_order_service.py:780-782 — PO statistics always return 0 count and 0 value**
   `get_po_statistics` runs `SELECT COUNT(*), SUM(total_amount) FROM purchase_orders`. SQLite's `cursor.description` returns column names `COUNT(*)` and `SUM(total_amount)`, but the code reads `result[0].get("count", 0)` and `result[0].get("total", 0)`. Neither key matches the actual column names, so the default 0 is always returned.

9. **[HIGH] purchase_orders_window.py:790-793 — `_clear_details` doesn't clear any UI elements**
   When the user deselects a PO, `_clear_details` sets `self.current_po = None` but never resets any labels or text edits. Stale data from the previously selected PO remains visible in all detail tabs.

10. **[HIGH] purchase_order_service.py:287 — `update_purchase_order` always nullifies `confirmed_date`**
   The UPDATE SQL sets `confirmed_date = None` on every update. If a PO was confirmed by a supplier and then edited (if allowed), the confirmation date is permanently lost in the database.

11. **[HIGH] purchase_order_service.py:837 — 3-way match uses non-existent status string `'cancelled'` for receiving notes**
   The filter `AND status != 'cancelled'` uses English `'cancelled'`, but the DB stores `ReceivingStatus` `.name` values (e.g. `'PENDING'`, `'IN_PROGRESS'`, `'COMPLETED'`). There is no `CANCELLED` status in `ReceivingStatus`. The filter is harmless (no rows excluded) but indicates a conceptual mismatch.

12. **[HIGH] purchase_order_dialog.py:706 — Per-item tax_percentage is hardcoded to 0.00, ignoring UI spin value**
   `_collect_data` always sets `tax_percentage=Decimal("0.00")` regardless of the user's input in column 5 (tax spin). When editing an existing PO that had per-item tax, the loaded tax value is silently overwritten to 0 on save.

### MEDIUM

13. **[MEDIUM] purchase_orders_window.py:787-788 — Receiving notes table in details tab is never populated**
   The receiving tab's `receiving_notes_table` is always empty. The code only has a `TODO` comment: `# TODO: تحميل إشعارات الاستلام`. Users cannot see which receiving notes exist for a PO.

14. **[MEDIUM] purchase_order_service.py:625-634 — Defensive tuple-indexing fallback code is dead/unreachable**
   `existing_batch[0].get("id") if isinstance(existing_batch[0], dict) else existing_batch[0][0]` — since `execute_query`/`fetch_all` always return dicts, the `else` branch (`existing_batch[0][0]`) is dead code. If the return type ever changed, column ordering assumptions would be fragile.

15. **[MEDIUM] purchase_order_service.py:853 — Same dead tuple-indexing fallback in 3-way match**
   `inv_row.get("total_amount", 0) if isinstance(inv_row, dict) else inv_row[2]` — the `else` path uses positional index `2` which would break if the SELECT column order changed. Dead code since `fetch_one` always returns dict.

16. **[MEDIUM] purchase_order_service.py:900-908 — `get_unmatched_invoices_for_supplier` has unreachable tuple fallback**
   `row[0]`, `row[1]`, `row[2]` etc. are never reached because `fetch_all` returns dicts. The dead code also assumes column order which would break silently if the query changed.

17. **[MEDIUM] receiving_dialog.py:425 — Receiving note status is never updated to COMPLETED**
   The receiving note is always created with `status=ReceivingStatus.IN_PROGRESS` but `ReceivingNote.complete()` is never called by any service code after creation. The note stays in `IN_PROGRESS` permanently.

18. **[MEDIUM] purchase_order_dialog.py:435 — `tax_spin` value read but never used in `_update_item_row`**
   Line 435 reads `self.items_table.cellWidget(row, 5)` but the result is not assigned to any variable and the tax percentage is never used in the row calculation. The per-item tax spin is purely decorative.

19. **[MEDIUM] purchase_order_service.py:139 — `create_purchase_order` uses `execute_update` which doesn't exist on `DatabaseManager`**
   `PurchaseOrderService` calls `self.db.execute_update()` throughout, but this method only exists on `LocalDatabaseManager`, not on `DatabaseManager`. If a `DatabaseManager` instance is passed (server/API context), all write operations would crash with `AttributeError`.

20. **[MEDIUM] purchase_order_dialog.py:88-89 — Duplicate `is_deleted=0` filter on products query**
   The query explicitly includes `WHERE is_deleted = 0` and `LocalDatabaseManager.execute_query` (with `exclude_deleted=True` default) may inject another `is_deleted = 0` clause. Results in redundant `WHERE is_deleted = 0 AND is_deleted = 0` (harmless but wasteful).

### LOW

21. **[LOW] purchase_orders_window.py:1055-1072 — `_get_button_style` uses unformatted f-string; CSS variable `{C.TEXT_SECONDARY}` inside the string is not interpolated**
   `QPushButton:disabled {{ background-color: #BDBDBD; color: {C.TEXT_SECONDARY}; }}` — the `{C.TEXT_SECONDARY}` is inside the double-braced f-string block (`{{` ... `}}`), so it's treated as literal text, not a Python expression. The disabled button text color would literally be the string `{C.TEXT_SECONDARY}` in the stylesheet.

22. **[LOW] purchase_order_service.py:877-878 — 3-way match returns dict without `'error'` key on success**
   When matched is True, the returned dict has no `'error'` key. The caller at `purchase_orders_window.py:1023` checks `if "error" in result and not result.get("matched")`. This works due to the `and` short-circuit, but the missing key is inconsistent with the error return path.

23. **[LOW] purchase_orders_window.py:877 — `submit_for_approval` hardcodes `submitted_by=1`**
   The user ID is hardcoded to 1 with a TODO comment. In a multi-user system, all approval submissions would be attributed to user #1.

24. **[LOW] purchase_order_dialog.py:352,457,487 — Generic exception handlers swallow all errors with only a warning log**
   Multiple `except Exception: logging...` blocks silently swallow errors in `_on_supplier_changed`, `_update_item_row`, and `_calculate_totals`. UI issues (wrong prices, missing updates) would go unnoticed.

25. **[LOW] purchase_order_service.py:90-91,146-148,584-587 — Transaction BEGIN/COMMIT/ROLLBACK errors are silently swallowed**
   `try: self.db.execute_query("BEGIN TRANSACTION") except: pass` — if the DB is in an unexpected state, the transaction failure is silently ignored, leading to auto-commit behavior with no atomicity.

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 6     |
| HIGH     | 6     |
| MEDIUM   | 8     |
| LOW      | 5     |
| TOTAL    | 25    |

## Top Priority Fixes (CRITICAL)

1. **Fix `purchase_order_service.py:256-257`** — Call `ensure_match_columns()` during service initialization or guard the UPDATE with a try/except that retries without those columns. Alternatively, add the columns in the base migration.

2. **Fix `purchase_order_service.py:296-301`** — Change `update_purchase_order` to UPDATE existing items (by id) instead of DELETE+re-INSERT. Preserve `purchase_order_items.id` to maintain foreign key integrity with `receiving_items.po_item_id`.

3. **Fix `purchase_order_dialog.py:414,777`** — Change lambda to `lambda idx, r=row: self._on_product_changed(r)` so the signal's index argument is captured by `idx` and `r` correctly receives the table row.

4. **Fix `purchase_order_service.py:835-843`** — Compute `received_amount` from `receiving_items` joined with `purchase_order_items` (using `quantity_accepted * unit_price`), since `receiving_notes` has no `total_amount` column.

5. **Fix `purchase_order_service.py:584-655`** — Either use `LocalDatabaseManager`'s transaction context manager (if available) or restructure to use `execute_non_query` / a single compound SQL statement. At minimum, document that transactions are not guaranteed.

6. **Fix `purchase_orders_window.py:656-658`** — Implement `_update_table_with_pos` by copying the table population logic from `_load_purchase_orders` (lines 580-636) into `_update_table_with_pos`, or refactor both to share a common method.


---

# Worklog - Task 5: Complete Payments Feature Cycle Deep Code Review

**Reviewer:** Automated Code Review Agent
**Date:** 2025-07-18
**Scope:** Complete payments feature cycle
**Files traced:** payment.py (model), payment_service.py (service), payment_dialog.py (UI), payment_dashboard.py (UI), local_database_manager.py (DB), add_currency_columns.py (migration), db_helpers.py

---

## Bug Report

### Systemic Bug: Arabic/English Enum Value Mismatch

The root cause of many bugs: `PaymentType`, `PaymentMethod`, and `PaymentStatus` enums have **Arabic** values (e.g. `PaymentStatus.COMPLETED.value == "مكتمل"`), but the DB stores **English** normalized values (e.g. `"completed"`) via `status_map`/`method_map`/`type_mapping` in `create_payment()`. Code throughout the service and UI passes `.value` (Arabic) to DB queries or comparisons against DB values (English), causing silent mismatches.

---

### Chain 1: Creating a Payment (UI → Service → Model → DB)

[CRITICAL] src/models/payment.py:284: `status_map` has key `"فشل"` but `PaymentStatus.FAILED.value` is `"فاشل"`. A payment with status FAILED will NOT be normalized — `norm_status` will be `None`. Since `payment.status` is `"فاشل"` (not None), the fallback to `"completed"` is skipped. The Arabic value `"فاشل"` is inserted directly, which likely violates DB CHECK constraints or causes downstream comparison failures.

[CRITICAL] src/models/payment.py:277-296: `status_map` is missing `"مسترد"` (the actual `PaymentStatus.REFUNDED.value`). Same issue as above — REFUNDED status payments will fail normalization and store Arabic in DB.

[HIGH] src/models/payment.py:311: `method_map` maps `"دفع إلكتروني"` (PaymentMethod.ONLINE.value) to `"bank_transfer"` instead of `"online"`. Online payments are silently reclassified as bank transfers. The `method_map` also has no self-referencing `"online": "online"` entry.

[HIGH] src/models/payment.py:691-744: `_row_to_payment()` uses positional index access (`row[0]`, `row[1]`, etc.) assuming a column order that includes `currency_id` at index 9, `base_amount` at 10, `converted_amount` at 11. However, these columns are added via ALTER TABLE (migration script `scripts/add_currency_columns.py`) which appends them at the END of the table, so the actual order has `payment_date` at index 9. Every field from index 9 onward maps to the WRONG column — payment dates become currency IDs, customer IDs become converted amounts, etc. Although this method is only reached via dead-code fallback in `get_overdue_payments`, it represents latent data corruption.

[MEDIUM] src/models/payment.py:103-118: `Payment.__post_init__()` runs `datetime.now()` for `updated_at` on every object creation, including when reconstructing from DB rows in `_row_to_payment_dict`. This overwrites the DB's `updated_at` timestamp with the current time on every read.

---

### Chain 2: Linking Payment to Invoice (paid_amount update)

[HIGH] src/services/payment_service.py:335-337: After `payment_manager.get_payment_by_id()` returns a Payment with DB-stored English values (e.g. `payment_type="customer_payment"`, `status="completed"`), the service OVERWRITES them with Arabic enum values: `payment_obj.payment_type = PaymentType.CUSTOMER_PAYMENT.value` ("دفعة عميل"), `payment_obj.status = PaymentStatus.COMPLETED.value` ("مكتمل"). The returned object is inconsistent with the DB. Any caller comparing these fields against DB values will fail.

[HIGH] src/services/payment_service.py:389-395: The invoice paid_amount update query `UPDATE sales SET paid_amount = paid_amount + ?, remaining_amount = total_amount - (paid_amount + ?) WHERE id = ?` uses `execute_non_query` which calls `self.db_manager.execute_non_query`. But `execute_non_query` is not defined in `PaymentManager` (it delegates to `self.db_manager`). This works but the `remaining_amount` calculation is wrong if multiple concurrent payments occur — it reads `paid_amount` at statement time but another transaction may have updated it (race condition / lost update).

[MEDIUM] src/services/payment_service.py:391-395: The `remaining_amount` calculation `total_amount - (paid_amount + ?)` double-counts the current payment's amount if the query is re-executed (e.g., retry). It should be `remaining_amount = remaining_amount - ?` to be idempotent.

---

### Chain 3: Payment List/Table Population and Filtering

[CRITICAL] src/services/payment_service.py:872: `get_payment_summary()` filters by `PaymentStatus.COMPLETED.value` ("مكتمل" Arabic) but DB stores "completed" (English). The query `WHERE status = ?` with "مكتمل" matches ZERO rows. **All payment summary reports return empty.**

[CRITICAL] src/services/payment_service.py:903-906: Same Arabic/English mismatch in the summary aggregation loop: compares DB `payment_type` (English "customer_payment") against `PaymentType.CUSTOMER_PAYMENT.value` (Arabic "دفعة عميل"). Customer/supplier payment totals are never accumulated — `totals` dict stays at zero.

[CRITICAL] src/services/payment_service.py:1071,1097,1100: `get_cash_flow_report()` — same Arabic status filter bug. The `status = 'مكتمل'` parameter matches nothing. Flow classification at lines 1097/1100 compares English DB types against Arabic enum values. **Cash flow report always returns empty.**

[CRITICAL] src/services/payment_service.py:1159: `get_payment_trends_analysis()` — Arabic status filter. **Trends analysis always returns empty.**

[CRITICAL] src/services/payment_service.py:1244: `get_payment_forecast()` — Arabic status filter. **Forecast always returns empty.**

[CRITICAL] src/services/payment_service.py:1343-1344,1347,1403-1404,1407,1543,1550-1551,1554,1563-1564: `get_period_comparison_analysis()` and `get_payment_performance_kpis()` — Arabic status and type values used as SQL parameters. **All comparison/KPI reports return empty data.**

[HIGH] src/services/payment_service.py:639,695: `get_accounts_receivable()` and `get_accounts_payable()` use `PaymentStatus.COMPLETED.value` ("مكتمل") to filter `payment_schedules.status != ?`. Since the schedules table uses Arabic defaults ("معلق") and the filter checks against "مكتمل", it technically works but for the wrong reason — it excludes nothing since no schedules have "مكتمل". Completed schedules stored with English "completed" would NOT be filtered out.

[HIGH] src/ui/dialogs/payment_dialog.py:680,684: `load_recent_payments()` accesses `payment.entity_id` but the `Payment` dataclass has no `entity_id` attribute (it has `customer_id` and `supplier_id`). This raises `AttributeError` for every payment row, caught by the broad `except Exception`, causing the entire recent payments table to appear empty.

[HIGH] src/ui/dialogs/payment_dialog.py:675: `payment.created_at.strftime("%Y-%m-%d")` — `created_at` can be `None` (e.g., if `safe_datetime` returns None). This raises `AttributeError: 'NoneType' object has no attribute 'strftime'`, caught by the broad except, making the table empty.

[MEDIUM] src/ui/dialogs/payment_dialog.py:690,692: `payment.payment_method` and `payment.status` display DB English values (e.g. "cash", "completed") in the UI table while all other UI elements show Arabic. Users see inconsistent language mixing.

[MEDIUM] src/ui/dialogs/payment_dialog.py:750-753: `search_accounts()` ignores all filter controls (account type combo, date range) and simply calls `load_accounts()`. The search feature is non-functional.

---

### Chain 4: Account Balance Calculation

[HIGH] src/models/payment.py:579-639: `get_account_balance()` has a logically broken SQL query. For receivables, the CASE statement `WHEN payment_type = ? THEN -amount ELSE amount` always takes the WHEN branch because the WHERE clause already restricts to `payment_type = 'customer_payment'` and the same value is passed for the CASE parameter. The query simplifies to `SELECT -SUM(amount_in_base_currency)`, returning the negative of total payments — NOT the actual outstanding receivable balance. The actual balance should be derived from invoice totals minus payments (from the sales table).

[HIGH] src/services/payment_service.py:167-168: `_create_indexes()` creates indexes on `account_balances(entity_id)` and `account_balances(account_type)`, but the `account_balances` table is NEVER created anywhere — not in `_create_tables()`, not in migrations. The `CREATE INDEX` statements fail silently (caught by the try/except at line 191).

[MEDIUM] src/models/payment.py:582: `get_account_balance()` compares `account_type` parameter against `AccountType.RECEIVABLE.value` which is "ذمة مدينة" (Arabic). Callers must know to pass the Arabic string. If any caller passes English "receivable", the method silently returns 0.

---

### Chain 5: Payment Status Transitions

[HIGH] src/services/payment_service.py:765: `get_overdue_payables()` compares `payment.payment_type == PaymentType.SUPPLIER_PAYMENT.value` ("دفعة مورد" Arabic) but DB stores "supplier_payment" (English). The condition is ALWAYS False. **Overdue payables are never detected — the function always returns an empty list.** Contrast with `get_overdue_receivables()` at line 731 which correctly uses the English string literal `"customer_payment"`.

[MEDIUM] src/services/payment_service.py:805: `get_payment_schedules()` uses `PaymentStatus.COMPLETED.value` ("مكتمل") as the status filter parameter. New schedules created from `PaymentSchedule` dataclass get `PaymentStatus.PENDING.value` ("معلق") as default, which is stored in DB without normalization. The filter `status != 'مكتمل'` works for these Arabic-stored statuses but would fail for any schedule whose status was updated to English "completed".

---

### Chain 6: Receipt Printing

[HIGH] src/ui/dialogs/payment_dialog.py:634-635: `show_receipt()` is a stub that only returns `True` without generating or printing any receipt. The receipt printing feature is completely unimplemented despite being referenced in the UI flow.

[HIGH] src/ui/dialogs/payment_dialog.py:849-876: `export_report()` is a stub — shows a success message and file path dialog but never actually writes any data to the selected file. Users believe the export succeeded when nothing was saved.

---

### Dashboard-Specific Bugs

[HIGH] src/ui/windows/payment_dashboard.py:699: `update_trends_chart()` accesses `trends_data["periods"]` but the service returns `trends_data["trends_data"]`. The trends chart is always empty.

[HIGH] src/ui/windows/payment_dashboard.py:726: `update_forecast_chart()` accesses `forecast_data["forecasts"]` but the service returns `forecast["predictions"]`. The forecast chart is always empty.

[HIGH] src/ui/windows/payment_dashboard.py:750,754: `update_comparison_chart()` accesses `comparison_data["previous_period"]["total_amount"]` but the actual data structure is `comparison_data["comparison"]["current_period"]["data"]["total_amount"]`. The comparison chart always shows zero.

[MEDIUM] src/ui/windows/payment_dashboard.py:795: Entity column in transactions table shows `customer_id`/`supplier_id` integer values instead of customer/supplier names.

[MEDIUM] src/ui/windows/payment_dashboard.py:791,798-800: Transaction type, payment method, and status columns show raw DB English values ("customer_payment", "cash", "completed") instead of user-facing Arabic text.

[MEDIUM] src/ui/windows/payment_dashboard.py:895-899: `export_dashboard()` is a stub showing "سيتم إضافة وظيفة التصدير قريباً" (export coming soon) message.

---

### Schema / Migration Issues

[MEDIUM] src/services/payment_service.py:51-89: `_create_tables()` does NOT include `currency_id`, `base_amount`, or `converted_amount` columns in the payments table DDL, but `create_payment()` tries to insert these columns (lines 362-364). These columns only exist if the external migration script `scripts/add_currency_columns.py` was manually run. Fresh databases will fail to store multi-currency data.

[MEDIUM] src/services/payment_service.py:102: `payment_schedules` table has `DEFAULT 'معلق'` (Arabic) for status, inconsistent with the English normalization used everywhere else in the payments system.

---

## Summary

| Severity | Count | Key Impact |
|----------|-------|------------|
| CRITICAL | 7 | All financial reports return empty (Arabic/English filter mismatch) |
| HIGH | 14 | Data corruption, missing features, wrong comparisons, empty lists |
| MEDIUM | 9 | Inconsistent UX, stubs, missing columns, schema issues |
| **Total** | **30** | |

The most impactful systemic issue is the Arabic/English enum value split: enums store Arabic, DB stores English, but code indiscriminately uses `.value` in both DB queries and object comparisons. This makes nearly every report, filter, and status check silently fail.
# Worklog - Task 6: Returns Feature Cycle Deep Code Review

**Reviewer:** Automated Code Review Agent
**Date:** 2025-06-30
**Scope:** Complete returns feature cycle (create, stock restore, refund, list, link to sale, partial/full)
**Files traced:** returns_window.py, return_service.py, return_invoice.py, sale.py (process_return), database_manager.py (schema), routes.py (API), db_helpers.py, connection_pool.py, sqlite_backend.py

---

## Bug Report

### Chain 1: UI (ReturnFormDialog._save) -> Service (ReturnService.create_return) -> DB

[CRITICAL] src/core/database_manager.py:751-808 vs src/services/return_service.py:96-207: Schema mismatch - ReturnService INSERT will fail on any database. The DB creates `return_invoices` with only 5 columns (`id, original_invoice_id, return_date, reason, total_refund_amount, status`) and `return_items` with 4 columns (`id, return_id, product_id, quantity, refund_price`). However, `ReturnService.create_return()` tries to INSERT 32 columns into `return_invoices` (including `return_number, return_type, customer_id, supplier_id, contact_name, subtotal, tax_amount, refund_method, etc.) and 16 columns into `return_items` (including `quantity_returned, quantity_original, unit_price, restockable, etc.). None of the migrations (001-008) add these missing columns. The `_upgrade_existing_schema()` method (line 850) also skips return tables entirely. Every return creation via the UI will crash with `sqlite3.OperationalError: table return_invoices has no column named return_number`.

[CRITICAL] src/services/return_service.py:459-478: `cursor.description` staleness corrupts data when 2+ returns exist. In `get_all_returns()`, the outer loop iterates over return_invoices rows. On the first iteration, `cursor.description` (line 460) correctly describes the `SELECT * FROM return_invoices` query. But the inner query at line 464 (`SELECT * FROM return_items`) overwrites `cursor.description`. On the SECOND outer-loop iteration, line 460 reads `cursor.description` which now describes the `return_items` columns, NOT `return_invoices`. The `dict(zip(columns, row))` at line 461 then maps return_items column names (e.g., `product_id, quantity_returned`) onto return_invoices row values. This produces a ReturnInvoice with completely wrong field mappings, or raises `KeyError` when accessing fields like `return_type` that do not exist in return_items columns. Only the first return in the list is ever displayed correctly.

[CRITICAL] src/models/sale.py:1840-1885: `SaleManager.process_return()` inserts returns into the `sales` table, not the `return_invoices` table. Line 1850 does `INSERT INTO sales (invoice_number, status, total_amount)` with invoice_number `f"RET-{sale_id}"` and status `SaleStatus.RETURNED.value`. This means returns processed through this code path are indistinguishable from regular sales in the sales table, have no return-specific metadata, and will appear in sales reports as regular sales. Furthermore, this method is dead code - no caller in the codebase invokes it.

### Chain 2: Stock Restoration on Return Completion

[HIGH] src/services/return_service.py:500-509: No idempotency guard on stock restoration. `complete_return()` calls `_restock_item()` for every restockable item every time it is called. If the user double-clicks "Complete" or if `update_return()` fails after stock is already restored, the stock is incremented multiple times. There is no check like `if return_invoice.status != ReturnStatus.COMPLETED` before restocking - the model's `complete()` method does check, but the N+1 query problem between `get_return()` and `update_return()` leaves a window where the status could change.

[HIGH] src/models/sale.py:1864-1877: Stock is restored immediately in `process_return()` at creation time, not at completion time. This contradicts the `ReturnService.complete_return()` which only restores stock after approval+completion. Two completely different business logics exist in the same codebase - the sale model restores stock immediately, the return service restores only on completion. If both code paths were active, stock would be double-restored.

### Chain 3: Refund Handling (Cash/Credit)

[HIGH] src/models/return_invoice.py:381-385: `generate_credit_note()` silently overwrites `refund_method`. If a return was created with `RefundMethod.CASH` and a credit note is later generated, line 385 sets `self.refund_method = RefundMethod.CREDIT_NOTE`, destroying the original payment method. The user's original refund preference is lost with no warning.

[MEDIUM] src/services/return_service.py:519-531: `process_refund()` does not validate the refund amount against `total_amount`. A caller could pass any amount (including negative or exceeding the total) and it would be accepted. There is no bounds check like `if amount > return_invoice.total_amount: raise ...`.

[MEDIUM] src/models/return_invoice.py:335-342: `calculate_totals()` only auto-sets `refund_amount` when it equals exactly `Decimal("0")`. If a return is updated (e.g., items added/removed) after `refund_amount` was already set to a non-zero value, the refund amount becomes stale and no longer matches `total_amount`. The `refund_amount` is never recalculated on subsequent `calculate_totals()` calls.

### Chain 4: Return List/Table Display

[HIGH] src/services/return_service.py:460-461: Same cursor.description staleness bug as Chain 1. Affects `get_all_returns()` which populates the returns list table. When there are 2+ returns, the second return onwards will have corrupted data. The returns table in the UI (`returns_window.py:330-364`) will display garbage data or crash for all but the first row.

### Chain 5: Return Linked to Original Sale

[HIGH] src/ui/windows/returns_window.py:658-851 (ReturnFormDialog): No link to the original sale is ever established. The dialog has a text field for `original_invoice_number` (line 698, 702, 836) but this is free-text - it does NOT set `original_sale_id`, `customer_id`, or populate `quantity_original` for items. There is no lookup of the original sale to validate that returned quantities do not exceed sold quantities. Returns are completely disconnected from their source sales.

[HIGH] src/ui/windows/returns_window.py:794-798: Quantity is hardcoded to `Decimal("1")`. The `_add_item()` method always creates items with `quantity_returned=Decimal("1")`. The items table in the dialog has no editable quantity column (line 756: `setEditTriggers(QTableWidget.NoEditTriggers)`). The user cannot return more than 1 unit of any product per item addition, and must click "Add" multiple times for quantity > 1. Each click adds a separate ReturnItem with quantity 1, producing multiple rows instead of one row with the correct quantity.

### Chain 6: Partial vs Full Return

[HIGH] src/ui/windows/returns_window.py:658-851: No partial vs full return logic exists. There is no validation of returned quantity against the original sale's sold quantity. The `ReturnItem.quantity_original` is always `Decimal("0")` (default), and `ReturnItem.can_return_quantity` (line 115-117) always equals `quantity_original - quantity_returned` which is `0 - 1 = -1` for every item. The system cannot distinguish partial from full returns.

[MEDIUM] src/models/return_invoice.py:115-117: `can_return_quantity` is never computed from actual sale data. It returns `self.quantity_original - self.quantity_returned`, but `quantity_original` is never populated from the source sale. It always stays at its default of `Decimal("0")`, making `can_return_quantity` always negative for any returned item.

### Structural / Architecture Issues

[HIGH] src/models/return_invoice.py:444-546 (ReturnManager) vs src/services/return_service.py:31-647 (ReturnService): Two duplicate, incompatible return creation paths. `ReturnManager` (used by API routes at routes.py:2886) expects the minimal DB schema and inserts into 4 columns. `ReturnService` (used by UI at returns_window.py:58, 664) expects the full schema and inserts into 32 columns. The API and UI paths can never share the same database - one will always fail. Additionally, `ReturnManager._create_return_item()` (line 513) uses columns `quantity, refund_price` while `ReturnService` uses `quantity_returned, unit_price`.

[MEDIUM] src/api/routes.py:124 vs routes.py:350: Duplicate `ReturnCreate` Pydantic model with different fields. Line 124 defines `ReturnCreate` with `items: List[ReturnItemSchema]` (typed). Line 350 redefines `ReturnCreate` (with `# noqa: F811`) with `items: List[Dict[str, Any]]` (untyped) and adds `original_purchase_id, supplier_id, return_date`. The second definition shadows the first, making the typed `ReturnItemSchema` validation dead code.

[MEDIUM] src/services/return_service.py:39-73: `generate_return_number()` has a race condition. The SELECT-then-generate pattern is not atomic. Two concurrent return creations can read the same `last_number` and generate the same `return_number`, causing a UNIQUE constraint violation (if `return_number` were UNIQUE - but it is not in the schema either). The fallback (line 73) uses timestamp with second precision, also susceptible to collisions.

[LOW] src/services/return_service.py:56: Uses `result[0]` instead of `result['return_number']`. Violates project convention that fetch results are dict-like. While `sqlite3.Row` (set via `row_factory`) does support integer indexing, this is fragile - if the connection is created without the pool/backend (direct `sqlite3.connect()` without `row_factory`), `result[0]` on a plain tuple still works but breaks the convention. The code at line 265 and 577-641 correctly uses `get_value(row, 'column_name')` showing the right pattern was known but not applied consistently.

[LOW] src/ui/windows/returns_window.py:825-851: No validation for empty items list. `_save()` only validates `contact_name` (line 827) but allows saving a return with zero items. The `ReturnInvoice` is created with `items=[]` and persisted. While `can_approve` prevents approval of empty-item returns, the return still exists in the database as a PENDING record with no items.

[LOW] src/models/return_invoice.py:282,291: Silent exception swallowing in `__post_init__`. Date/timestamp parsing errors at lines 280 and 290 are caught with a bare `except Exception` that only logs a generic warning. If a date string is malformed, the field stays as a string instead of a `date`/`datetime` object, causing subtle type errors downstream (e.g., `.strftime()` calls on strings will fail at runtime).

[LOW] src/ui/windows/returns_window.py:790-792: `isinstance(p, dict)` fallback uses tuple indexing. Line 790-792 has `p[0]`, `p[1]`, `p[3]` as fallback for non-dict rows. This contradicts the project convention. While `_search_product()` calls `self.db.fetch_all()` which returns dicts, the fallback code suggests uncertainty about the return type.

[LOW] src/ui/windows/returns_window.py:635-655: Five stub methods for testing. `load_returns`, `process_return`, `approve_return`, `get_return_history`, `calculate_refund_amount` are stubs that return `True` or `[]` without any real logic. These shadow the actual service calls and could mislead developers into thinking returns work when they do not.

---

## Summary

| Severity | Count | Key Impact |
|----------|-------|
| CRITICAL | 3 | Returns completely non-functional (schema mismatch, data corruption, wrong table) |
| HIGH | 8 | Duplicate code paths, missing validation, stale data, no sale linkage |
| MEDIUM | 5 | Schema duplication, race conditions, amount validation gaps |
| LOW | 5 | Convention violations, silent errors, stubs, missing validation |
| **Total** | **21** |

The most impactful systemic issue is the **three-way schema split**: the DB creates a minimal `return_invoices` table (5 cols), the `ReturnManager` (API) expects that minimal schema, and the `ReturnService` (UI) expects a full 32-column schema that was never created via any migration. Additionally, the `SaleManager.process_return()` inserts returns into the `sales` table - a fourth, completely separate approach. None of these paths are compatible with each other, and the `cursor.description` staleness bug means even if the schema were fixed, the returns list would only show the first return correctly.


# Worklog - Task 7: Products/Inventory Complete Feature Cycle Deep Code Review

**Reviewer:** Automated Code Review Agent
**Date:** 2025-06-30
**Scope:** Complete products/inventory feature cycle — CRUD, stock management, categories, batch tracking, low stock alerts
**Files traced:** product.py, product_enhanced.py, category.py, product_service_enhanced.py, inventory_service.py, product_dialog.py, category_dialog.py, category_form_dialog.py, stock_adjustments_window.py, adjust_stock_dialog.py, transfer_stock_dialog.py, batch_dialog.py, safety_stock_dialog.py, inventory_table_model.py, main_window.py (inventory section), product_repository.py, base_repository.py, db_helpers.py, database_manager.py

---

## Bug Report

### Chain 1: Creating a Product (UI Dialog → Service → Model → DB)

[HIGH] src/services/product_service_enhanced.py:99: `create_product()` calls `self.db_manager.execute_query(query, tuple(insert_vals))` for the INSERT statement instead of `self.db_manager.execute_insert()`. Then on line 101, it calls `self.db_manager.get_last_insert_id()` which may fail because `execute_query` does not guarantee `lastrowid` is preserved across the commit path. Should use `execute_insert` for reliable ID retrieval.

[HIGH] src/services/product_service_enhanced.py:88: `create_product()` silently skips columns whose value is `None` (`if col in existing_cols and val is not None`). This means fields like `wholesale_price`, `vip_price`, `min_wholesale_qty` which default to `Decimal("0.00")` or `10` in the basic Product model but are `None` in EnhancedProduct will never be explicitly set to 0 in the INSERT, relying on DB defaults that may not exist for all columns. Combined with the fact that the dynamic column check happens on every single product creation (line 82: `PRAGMA table_info(products)`), this creates both a performance issue and potential NULL values in NOT NULL columns.

[MEDIUM] src/ui/dialogs/product_dialog.py:1201-1216,1318-1332,1261-1276,1369-1383: When saving a product, the dialog collects many fields via `collect_form_data()` (lines 1040-1083) including `supplier_id`, `location`, `weight`, `length`, `width`, `height`, `expiry_date`, `notes`, `is_sellable`, `is_purchasable`, `track_stock`. However, NONE of these fields are passed to either `EnhancedProduct()` constructor or the legacy `Product()` constructor in any of the four save paths (enhanced create, enhanced update, legacy create, legacy update). These fields are collected from the UI and then silently discarded.

[MEDIUM] src/services/product_service_enhanced.py:62-63: `create_product()` maps `selling_price` column to `product.base_price` value: `"selling_price": float(product.base_price)`. But then in `_row_to_product()` (line 901), it reads `base_price` first and falls back to `selling_price`. If the DB schema has `selling_price` but not `base_price` (which is the standard schema), the write goes to `selling_price` but the read checks `base_price` first (gets None), then falls back to `selling_price`. This works but creates a fragile coupling.

### Chain 2: Updating a Product

[CRITICAL] src/services/product_service_enhanced.py:216-224: `update_product()` hardcodes ALL column names in the UPDATE query including `reserved_stock`, `reorder_point`, `max_stock`, `is_discontinued`, `is_featured`, `images`, `tags`, `specifications`. Unlike `create_product()` which dynamically checks `PRAGMA table_info` for existing columns, `update_product()` does NOT check. If ANY of these columns do not exist in the current database schema (e.g., a user who hasn't run all migrations), the entire UPDATE fails with a SQLite error, making product editing completely broken.

[HIGH] src/services/product_service_enhanced.py:219: `update_product()` references column `base_price` in the UPDATE SET clause, but the standard DB schema uses `selling_price`. When a user edits a product through the enhanced service and the DB has `selling_price` but not `base_price`, the UPDATE will fail with "table products has no column named base_price".

[MEDIUM] src/services/product_service_enhanced.py:248: `update_product()` passes `product.is_active`, `product.is_discontinued`, `product.is_featured` directly as Python `bool` values. SQLite accepts these (True→1, False→0) for parameterized queries, but this relies on implicit Python-to-SQLite type conversion which may break with certain database backends or adapters.

[MEDIUM] src/ui/dialogs/product_dialog.py:1832: `_finalize_close()` calls `self.close()` which re-triggers `closeEvent()`, creating a potential infinite recursion. The stored `_close_event` should be accepted via `event.accept()` instead of calling `self.close()` again.

### Chain 3: Product List/Table Population, Search, Filter

[MEDIUM] src/repositories/product_repository.py:31,48,68,75,96: `ProductRepository` uses `is_deleted = 0` filter in all queries, but the `products` table uses `is_active` for soft-delete, not `is_deleted`. The `find_by_barcode`, `find_by_name`, `find_low_stock`, and `update_stock` methods will either return no results (if `is_deleted` column doesn't exist) or wrong results (if it does exist but is never set by the product creation code). The main product model (`ProductManager`) uses `is_active` consistently.

[LOW] src/repositories/base_repository.py:218: `count()` accesses `results[0]["count"]` using alias `count`, but the query at line 215 uses `COUNT(*) as count`. If the DB returns the column name as `COUNT(*)` (some adapters), the dict key won't match `"count"`. The `CategoryManager.get_products_count_in_category` handles this correctly with a fallback (`row.get("COUNT(*)", row.get("count", 0))`), but `BaseRepository.count()` does not.

### Chain 4: Stock Management — Stock In/Out, Adjustments, Transfers

[MEDIUM] src/models/product.py:365-366: `update_stock()` rejects negative quantities (`if quantity < 0: return False`). This means you cannot set stock to zero through this method if the quantity is already zero or negative. Meanwhile, `adjust_stock_relative()` (line 374-378) has no such check and CAN drive stock negative. The two methods have inconsistent validation.

[LOW] src/ui/dialogs/transfer_stock_dialog.py:106: `self.reason_input.text().strip()` is called but the result is never assigned to a variable or passed to `inventory_service.transfer_stock()`. The transfer reason is silently discarded.

[LOW] src/ui/dialogs/adjust_stock_dialog.py:35: `AdjustStockDialog.__init__()` loads ALL products eagerly via `self.product_manager.get_all_products(active_only=True)` without any pagination. For large inventories, this loads every product into memory.

### Chain 5: Category Management CRUD

[MEDIUM] src/ui/dialogs/category_form_dialog.py:136: `save_category()` uses `self.db_manager.execute_query(query, ...)` for the UPDATE statement. For UPDATE/DELETE operations, `execute_query` auto-commits and returns a cursor, but it doesn't return a meaningful rowcount in a portable way. Should use `execute_non_query` which explicitly returns the affected row count and is designed for non-SELECT operations.

[MEDIUM] src/ui/dialogs/category_form_dialog.py:144: Same issue for INSERT — uses `execute_query` instead of `execute_insert`. The newly created category ID is never retrieved or returned, so the caller cannot know which category was created.

[LOW] src/ui/dialogs/category_dialog.py:186: `on_search()` only searches by `name`: `text.lower() in cat["name"].lower()`. It does not search the `description` field, limiting search effectiveness.

### Chain 6: Batch/Lot Tracking

[MEDIUM] src/ui/dialogs/batch_dialog.py:349-380: `save_batch()` for the UPDATE path uses `self.db_manager.execute_query(query, ...)` to update the batch. This does not use `execute_non_query`, so the success/failure of the update is not properly detected. The dialog shows "تم تحديث الدفعة بنجاح" regardless of whether the update actually succeeded.

[LOW] src/ui/dialogs/batch_dialog.py:345-346: The UPDATE branch has a comment "لاحقاً سنضيف update_batch للخدمة" ("later we'll add update_batch to the service"), acknowledging this is a TODO that was never completed. The raw SQL update bypasses the service layer entirely.

### Chain 7: Low Stock Alerts

[MEDIUM] src/services/product_service_enhanced.py:818: `get_products_statistics()` truncates `avg_stock` to `int`: `"avg_stock": int(result.get("avg_stock", 0) or 0)`. The query uses `AVG(CAST(current_stock as REAL))` which returns a float. Casting to `int` loses the decimal precision, making the average stock statistic inaccurate.

[LOW] src/services/product_service_enhanced.py:504-519: `get_featured_products()` hardcodes `reserved_stock` in the SELECT without checking if the column exists via `PRAGMA table_info`, unlike `get_low_stock_products()` and `get_products_requiring_reorder()` which do check. If `reserved_stock` column doesn't exist, this query will fail.

[LOW] src/services/product_service_enhanced.py:746-753: `get_inventory_value()` for the non-reserved_stock case uses `SUM(current_stock * base_price)`. If the DB has `selling_price` instead of `base_price`, this returns 0 for total selling value. Only the reserved_stock branch is properly handled with a column-existence check.

### Cross-Cutting Issues

[HIGH] Profit margin calculation inconsistency across three locations:
  - `src/models/product.py:55`: `((selling_price - cost_price) / cost_price) * 100` → markup on cost (e.g., cost=50, sell=100 → 100%)
  - `src/ui/dialogs/product_dialog.py:1012,1768`: `((selling - cost) / selling) * 100` → margin on revenue (e.g., cost=50, sell=100 → 50%)
  - `src/ui/dialogs/product_dialog.py:1681`: `(profit / cost) * 100` → markup on cost (matches model)
  The main form's quick info panel and the profit calculator dialog show DIFFERENT formulas for "profit margin". The profit calculator (line 1681) uses markup-on-cost while the real-time display (line 1768) uses margin-on-revenue.

[MEDIUM] src/ui/dialogs/product_dialog.py:964-976: `load_stock_history()` populates the stock history tab with HARDCODED sample data (`sample_data = [["2024-01-15", ...]]`) instead of querying actual stock movements from the `stock_movements` table. Users see fake data in edit mode.

[MEDIUM] src/ui/dialogs/stock_adjustments_window.py:498-503: `show_create_adjustment_dialog()` fetches products with `SELECT id, sku, name, ...`. If the `sku` column does not exist in the products table (only added in migration 018), the query fails and the entire dialog cannot open.

[MEDIUM] src/models/product_enhanced.py:262: Enhanced `Product.current_stock` is typed as `int = 0`, but `AdjustStockDialog` uses `QDoubleSpinBox` with 3 decimal places. Stock quantities with fractional values (e.g., 1.500 kg) will be truncated to integers when stored through the enhanced product path.

[LOW] src/ui/dialogs/product_dialog.py:1724-1757: `clear_form()` resets all form fields but does NOT clear `self.current_image_path`, `self.original_image_path`, or reset the image preview widget. When using "save and new", the old product's image carries over silently to the new product.

[LOW] src/services/product_service_enhanced.py:876: `_row_to_product()` defines a local `get_value(key, default)` function that shadows the imported `get_value(row, key, default)` from `src.utils.db_helpers`. While this is intentional (it operates on an already-extracted dict), it creates confusion and makes the code harder to audit.

---

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 1 | update_product hardcodes columns not validated against schema |
| HIGH | 4 | create_product uses wrong DB method; base_price/selling_price mismatch; update_product column mismatch; profit margin inconsistency |
| MEDIUM | 13 | Silently discarded form fields; recursive closeEvent; is_deleted vs is_active mismatch; negative stock validation; execute_query for DML; hardcoded stock history; avg_stock int truncation; sku column dependency; EnhancedProduct int vs float stock; batch update bypasses service; category form DML method |
| LOW | 7 | Discarded transfer reason; eager product loading; search scope; featured_products no column check; base_price in inventory value; clear_form image leak; shadowed get_value |
| **Total** | **25** |

The most impactful systemic issue is the **update_product schema fragility** (CRITICAL): the enhanced `ProductService.update_product()` hardcodes all 22 column names including optional/migration-dependent columns (`reserved_stock`, `reorder_point`, `max_stock`, `is_discontinued`, `is_featured`, `images`, `tags`, `specifications`, `base_price`) without any `PRAGMA table_info` check, unlike `create_product()` which does check. On any database where not all migrations have been applied, product editing is completely broken. Additionally, the `base_price` vs `selling_price` naming inconsistency between the enhanced model and the standard DB schema means the enhanced update path writes to a column that may not exist.

---

# Worklog - Task 8: Customers & Suppliers Complete Cycle Deep Code Review

**Reviewer:** Automated Code Review Agent
**Date:** 2025-06-30
**Scope:** Complete customers and suppliers feature cycle
**Files traced:** customer.py, supplier.py, vendor_service.py, customer_management_dialog.py, customer_form_dialog.py, supplier_management_dialog.py, supplier_form_dialog.py, payment.py, database_manager.py, local_database_manager.py, sqlite_backend.py, sales_service.py

---

## Bug Report

### Chain 1: Customer Creation — customer_form_dialog.py → DB

[HIGH] customer_form_dialog.py:341: `save_customer()` uses `self.db_manager.execute_query()` for INSERT instead of `self.db_manager.execute_insert()`. `execute_query()` returns a list of dicts for SELECTs or a raw cursor for writes. The new customer's ID is never retrieved, so the dialog cannot confirm what ID was created. Works only because `execute_query` auto-commits and the management dialog re-fetches the full list afterward.

[MEDIUM] customer_form_dialog.py:300: `save_customer()` UPDATE path also uses `execute_query()` instead of `execute_non_query()`. The return value (a cursor) is discarded. Works due to auto-commit but is the wrong method for write operations.

[LOW] customer_form_dialog.py: No email format validation. The supplier form validates `@` in email (supplier_form_dialog.py:211) but the customer form does not. Inconsistent validation between the two nearly identical forms.

### Chain 2: Supplier Creation — supplier_form_dialog.py → DB

[HIGH] supplier_form_dialog.py:246-252: `save_supplier()` INSERT omits `credit_limit`, `current_balance`, `payment_terms`, `tax_number`, `commercial_register`, `website`, `country`. These columns get table defaults only (0.00, 'نقدي', NULL). Users have NO UI to set the supplier's credit limit or payment terms, making the credit management system unusable from the UI. The `SupplierManager.create_supplier()` (supplier.py:233) inserts all 19 fields, but the UI form only collects 7 fields.

[HIGH] supplier_form_dialog.py:252: Same `execute_query()` for INSERT bug as customer form — wrong method, no insert ID returned.

[MEDIUM] supplier_form_dialog.py:227: UPDATE path uses `execute_query()` instead of `execute_non_query()`.

### Chain 3: Customer/Supplier List Population, Search, Filter

[HIGH] customer_management_dialog.py:104: `load_customers()` query `SELECT id, name, phone, email, current_balance, is_active FROM customers ORDER BY name` does NOT filter `WHERE is_active = 1`. After soft-deleting a customer, they remain visible in the list with no visual distinction. Same bug at supplier_management_dialog.py:104.

[HIGH] supplier_management_dialog.py:104: `load_suppliers()` query `SELECT id, name, phone, email, contact_person, is_active FROM suppliers ORDER BY name` has the same missing `WHERE is_active = 1` filter. Soft-deleted suppliers persist in the list.

[MEDIUM] customer_management_dialog.py:188-191: `on_search()` filters the in-memory list using `text.lower() in c["name"].lower()`. This is a client-side filter on already-loaded data only — it does NOT query the database. If there are thousands of customers, only the initially loaded batch is searchable. Same issue at supplier_management_dialog.py:191-193.

### Chain 4: Editing/Updating

[MEDIUM] customer_form_dialog.py:250-257: `save_customer()` calls `PRAGMA table_info(customers)` on EVERY save (both create and update) to check if `phone2` column exists. This is a redundant DB round-trip — the same check is done on load (line 138). The result should be cached.

[LOW] supplier_form_dialog.py:124-128: `load_supplier()` SELECT omits `credit_limit`, `payment_terms`, `tax_number`, `commercial_register`, `website`, `country`. When editing a supplier, these fields cannot be loaded or modified even if they were set via direct DB manipulation or a different code path.

### Chain 5: Balance Tracking (Credit Limit, Outstanding Balance)

[CRITICAL] src/services/vendor_service.py:— **Supplier balance is NEVER increased when a purchase is created.** `SupplierManager.update_supplier_balance()` (supplier.py:421) exists but is never called from any purchase-related code path (purchase_service.py, sales_service.py, vendor_service.py, purchase_order_service.py). Only `PaymentManager._update_supplier_balance()` (payment.py:676) decreases the balance when a payment is made. This means `suppliers.current_balance` (outstanding debt) is always 0, making the entire supplier credit/balance tracking system non-functional.

[HIGH] src/models/customer.py:596-611: `CustomerManager.update_balance()` has a read-modify-write race condition. It reads the current balance (line 599), computes `new_balance` in Python (lines 604-608), then writes it back (line 611). Two concurrent sales or payments on the same customer will read the same stale balance, and the second write overwrites the first — a classic lost update. Should use atomic SQL: `UPDATE customers SET current_balance = current_balance + ? WHERE id = ?`. (Note: `PaymentManager._update_customer_balance()` at payment.py:661-670 correctly uses the atomic pattern, but `CustomerManager.update_balance()` does not.)

[HIGH] src/models/supplier.py:421-433: `SupplierManager.update_supplier_balance()` has the same read-modify-write race condition. Reads `supplier.current_balance`, adds `amount_change` in Python, writes back. Not atomic. (Unlike `PaymentManager._update_supplier_balance()` which correctly uses `current_balance = current_balance + ?`.)

[MEDIUM] src/models/payment.py:670,685: Both `_update_customer_balance()` and `_update_supplier_balance()` use `self.db_manager.execute_query()` for UPDATE queries instead of `execute_non_query()`. Works due to auto-commit but semantically wrong.

### Chain 6: Customer/Supplier Deletion

[HIGH] customer_management_dialog.py:209-255: `delete_customer()` bypasses `CustomerManager.delete_customer()` entirely — it does raw SQL queries. The model's `delete_customer()` (customer.py:617) checks for sales and payments and returns False if any exist, but the dialog has its own duplicate checks. The dialog also ALWAYS does soft-delete (sets `is_active = 0`) even when the customer has NO dependencies. Combined with the missing `is_active = 1` filter in `load_customers()`, deleted customers immediately reappear in the list.

[HIGH] customer_management_dialog.py:236-244: When a customer HAS dependencies, a warning dialog shows Ok|Cancel buttons. The message says "will deactivate instead of delete" but the user has no way to actually delete — even without dependencies, the code always deactivates. The dialog misleads users into thinking deletion is an option.

[MEDIUM] customer_management_dialog.py:247: Soft-delete uses `execute_query()` instead of `execute_non_query()`. Same at supplier_management_dialog.py:256.

[HIGH] supplier_management_dialog.py:212-265: `delete_supplier()` checks `products.supplier_id` and `purchases` for dependencies, but `SupplierManager.delete_supplier()` (supplier.py:403) checks `purchases` count and `purchase_items` product count via a JOIN. Different criteria: the UI prevents deletion if ANY product references the supplier, while the model only prevents deletion if there are actual purchase orders. A supplier with linked products but no purchases would be deletable via the model but blocked by the UI (or vice versa).

### Chain 7: Customer Purchase History

[INFO] No dedicated customer purchase history UI exists. `CustomerManager._enrich_with_sales_data()` (customer.py:321-350) fetches only summary aggregates (last_purchase_date, total_purchases, purchases_count). There is no method or UI to display individual sale records for a specific customer. The `get_supplier_purchases_history()` method exists for suppliers (supplier.py:196-231) but has no customer equivalent.

### Chain 8: VendorService (vendor_service.py)

[HIGH] vendor_service.py:91-94: `create_purchase_order()` uses `self.db.execute_query()` for the main INSERT and then accesses `res.lastrowid`. With `DatabaseManager` (server-side), `execute_query()` returns a cursor from inside a `with self.get_cursor() as cursor:` context manager that closes the cursor in `finally` before returning (database_manager.py:1048-1050). `res.lastrowid` on a closed cursor raises `ProgrammingError` or returns stale data. Only works with `LocalDatabaseManager` because it returns the cursor directly without a context manager wrapper.

[MEDIUM] vendor_service.py:162,170,179,250,253,256: Accesses dict keys using raw SQL expressions as keys: `row["COUNT(*)"]`, `row["AVG(julianday(delivery_date) - julianday(order_date))"]`. Works with DictRow (which uses `cursor.description` column names) but is extremely fragile — any query alias change breaks the access. Should use SQL aliases like `SELECT COUNT(*) as total_count` and access via `row["total_count"]`.

[MEDIUM] vendor_service.py:180: `lead_time_score = max(0, 100 - (avg_days * 5))` — if `avg_days` is None (which happens when `delivery_date` or `order_date` is NULL in a purchase record), `avg_days * 5` raises `TypeError: unsupported operand type(s)`. The guard at line 164 only checks `total_orders == 0` but does not guard against NULL `avg_days`.

[MEDIUM] vendor_service.py:96-104: The inner loop that inserts `purchase_order_items` uses `execute_query()` for each item INSERT. If any item INSERT fails, the already-inserted items are NOT rolled back — no transaction is used. This leaves the database in a partially inserted state.

### Chain 9: Model-Level Issues

[MEDIUM] src/models/customer.py:163-175: `CustomerManager._add_company_filter()` is defined but NEVER called from any customer method (`create_customer`, `search_customers`, `get_all_customers`, `get_customer_by_id`, `get_customer_by_phone`, `get_customers_with_balance`, `get_customers_report`). The supplier model correctly calls `_add_company_filter` in its query methods. Customer queries in a multi-company setup would return data from all companies.

[LOW] src/models/customer.py:792-846: `_row_to_customer()` is dead code — never called from any method in the file or elsewhere. All callers use `_dict_to_object()`. If ever called, the hardcoded positional indices (e.g., index 18 for `created_at`, index 19 for `updated_at`) assume a specific column order that may not match the actual `SELECT *` expansion.

[LOW] src/models/supplier.py:545-574: `_row_to_supplier()` has a legacy `len(row) == 16` special case that uses pure positional access with hardcoded indices. This path is never triggered because all callers use the enriched query (s.* + 3 subqueries = ~23 columns). If ever triggered by a non-enriched query, the column mappings would be incorrect.

[LOW] src/models/customer.py:337-340, supplier.py:218-226: Both models have non-dict tuple fallback branches using `row[0]`, `row[1]`, etc. in `_enrich_with_sales_data()` and `get_supplier_purchases_history()`. Since `fetch_one`/`fetch_all` always return DictRow (a dict subclass), these branches are dead code.

---

## Summary Table

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 1 | Supplier balance never updated on purchase creation — entire credit tracking broken |
| HIGH | 8 | Wrong DB method for INSERT/UPDATE in forms; race conditions in balance updates; inactive records shown in lists; deletion logic bypasses model; inconsistent deletion criteria; VendorService closed cursor |
| MEDIUM | 8 | execute_query for DML; missing company filter; NULL arithmetic in vendor scoring; no transaction in PO items; redundant PRAGMA calls; fragile SQL expression keys |
| LOW | 4 | Dead code paths with wrong indices; inconsistent email validation; missing fields on edit load |
| INFO | 1 | No customer purchase history UI exists |
| **Total** | **22** |

The most impactful systemic issue is the **supplier balance never increasing on purchase** (CRITICAL): `SupplierManager.update_supplier_balance()` exists but is never invoked from any purchase or purchase order creation path. Combined with the `SupplierFormDialog` not exposing credit_limit or payment_terms fields, the entire supplier credit management subsystem is non-functional from the user's perspective. The second most impactful cluster is the **balance update race condition** affecting both `CustomerManager.update_balance()` and `SupplierManager.update_supplier_balance()`, which use non-atomic read-modify-write patterns while `PaymentManager` correctly uses atomic SQL updates — indicating inconsistent patterns across the codebase.

---

# Worklog - Task 9: Reports Feature Cycle Deep Code Review

**Reviewer:** Automated Code Review Agent
**Date:** 2025-06-30
**Scope:** Complete reports feature cycle (all report types, data fetching, date filtering, export/print, chart generation)
**Files traced:** reports_window.py, advanced_reports_window.py, report_exporter.py, report_generator.py, report.py, reports.py, db_helpers.py, database_manager.py, local_database_manager.py

---

## Bug Report

### Chain 1: Reports Window → ReportExporter → Database (Primary Report Path)

[CRITICAL] report_exporter.py:471-498: Inventory status report query is a **non-f-string with unresolved f-string placeholders**. Three variables are referenced inside `{...}` braces in a regular (non-f-string) query: `{max_stock_col}`, `{supplier_select}`, `{supplier_join}`. Additionally, `max_stock_col` is **never assigned** — line 471 is a bare expression `"COALESCE(p.max_stock, 0)" if has_max_stock else "0"` that evaluates and discards the string. `supplier_join` and `supplier_select` are assigned (lines 469-470) but marked `# noqa: F811` (unused). The resulting SQL contains literal text `{max_stock_col}` and `{supplier_select}` and `{supplier_join}`, causing a SQL syntax error. **Every inventory status report generation fails unconditionally.**

[CRITICAL] report_exporter.py:449: `PRAGMA table_info(products)` results are accessed via `row[1]` (tuple index) but `fetch_all` returns `List[Dict[str, Any]]` via DictRow class. The code comment says "PRAGMA table_info returns tuples" which contradicts the actual DictRow behavior. This causes `KeyError: 1` at runtime when trying to build the `available_columns` set, falling through to the hardcoded fallback. The fallback columns may not match actual schema, causing the dynamic `max_stock_col`/`supplier_join`/`supplier_select` logic to be skipped even if the PRAGMA bug were fixed.

[CRITICAL] report_exporter.py:2062-2064, 2157-2159, 2235-2237: Three report methods (`generate_cash_flow_report`, `generate_payment_analysis_report`, `generate_payment_methods_analysis_report`) bypass the DatabaseManager API entirely by creating raw cursors via `self.db_manager.connection.cursor()` then calling `cursor.fetchall()`, which returns **raw tuples** instead of DictRow/dict objects. The code then uses `get_value(row, 'column_name')` from `db_helpers.py` which catches the `TypeError` from tuple key access and silently returns `None`/`default`. **All three reports produce data with every field set to None/0.** The date grouping, payment type classification, and amount accumulation in cash flow reports produce completely empty results.

[CRITICAL] report_exporter.py:471: Standalone expression `"COALESCE(p.max_stock, 0)" if has_max_stock else "0"` is not assigned to any variable. This is dead code that should have been `max_stock_col = "COALESCE(p.max_stock, 0)" if has_max_stock else "0"`. Combined with the non-f-string query bug, this guarantees inventory status reports are completely broken.

[CRITICAL] report_exporter.py:473: The `query` variable for inventory status is assigned a regular triple-quoted string (no `f` prefix) but contains `{max_stock_col}`, `{supplier_select}`, and `{supplier_join}` placeholders that are never interpolated. The SQL sent to the database contains literal brace-enclosed text, which is invalid SQL syntax.

### Chain 2: Report Generator (Secondary/Advanced Path)

[HIGH] report_generator.py:893-896: `generate_financial_ratios_report` references `DATE(s.sale_date)` and `s.final_amount` but the sales table likely uses `sale_date` column directly (not `s.sale_date` with alias `s`). Also references `si.profit` in sale_items (line 904) which may not be a standard column. The `sale_date` column name inconsistency between `report_generator.py` (uses `s.date`) and `report_exporter.py` (uses `s.sale_date`) indicates the two report systems query different schemas or aliases.

[HIGH] report_generator.py:947-948, 1082-1088: `generate_profitability_analysis_report` and `generate_margin_analysis_report` reference `si.total_price` and `si.profit` columns that are not standard sale_items columns (the standard is `si.total`, and profit is computed as `si.quantity * (si.unit_price - p.cost_price)`). If these columns don't exist in the actual schema, the queries will fail with SQLite errors.

[HIGH] report_exporter.py:1361: In `generate_customer_analysis_report`, the `HAVING total_purchases >= ?` clause is appended to the query **before** the `GROUP BY` clause. SQL requires HAVING after GROUP BY. The resulting SQL is syntactically invalid, causing a database error when `filters.min_amount` is set.

[HIGH] report_exporter.py:1758-1768, 1914-1925: `generate_receivables_aging_report` and `generate_payables_aging_report` probe for `due_date` column existence by calling `self.db_manager.connection.execute(test_query)` directly on the raw connection object. This bypasses connection pooling, transaction management, and error handling. If `connection` is `None` (not initialized), this crashes with `AttributeError: 'NoneType' object has no attribute 'execute'`.

[HIGH] reports_window.py:408, 1151-1163: The combo box contains a separator item "━━━ المستودعات ━━━" with `data=None`. When selected, `report_type` becomes `None`. This is passed to `ReportGenerationWorker` which calls `self.reports_service.generate_report(None, self.filters)`. The `generate_report` method compares `None == ReportType.SALES_SUMMARY` (False), falls through all conditions, and raises `ValueError("نوع التقرير غير مدعوم: None")` inside the worker thread. The error signal handler catches it, but selecting the separator item is a broken user experience — no validation prevents it.

### Chain 3: Date Range Filtering

[MEDIUM] report_exporter.py:1202-1208, 2047-2053, 2196-2202: Inconsistent date parameter formatting. `generate_payment_summary_report`, `generate_cash_flow_report`, and `generate_payment_analysis_report` pass raw `datetime` objects as SQL parameters (`params.append(filters.start_date)`), while `generate_sales_summary_report` correctly uses `filters.start_date.strftime("%Y-%m-%d")`. The raw `datetime` objects may not compare correctly with SQLite date strings depending on column types and registered adapters, leading to reports silently returning wrong date ranges or empty results.

[MEDIUM] report_exporter.py:1062-1071: `_get_monthly_financial_trend` builds the `sales_query` using fragile string replacement: `.replace("s.sale_date", "sale_date")` on date filter strings. This approach is brittle — if the column name pattern appears in unexpected contexts, it could produce wrong SQL. Additionally, both queries share the same `date_params` list, but the sales query does not join to the `s` alias, so the parameters would be consumed differently.

### Chain 4: Export/Print Functionality

[MEDIUM] report_exporter.py:819: `_export_to_csv` uses `pd.DataFrame(report_data.data)` but there is no dedicated pandas availability check. The import guard at the top sets `EXCEL_AVAILABLE = False` if either `pandas` or `openpyxl` fails. If pandas is missing, `pd` is undefined, causing `NameError` when CSV export is attempted. The `export_report` method (line 718) routes CSV to `_export_to_csv` without checking pandas availability.

[MEDIUM] reports_window.py:1429-1433: `export_report()` has a test-compatibility shim: `if isinstance(export_format, str): return True`. When the export buttons pass `ExportFormat.EXCEL` (an enum), this is fine. But if any code path passes a string format name, the method silently returns `True` without exporting anything, misleading callers into thinking export succeeded.

[LOW] reports_window.py:1498-1505: `print_current_report()` shows a placeholder message "سيتم إضافة وظيفة الطباعة قريباً" (print feature coming soon) — the feature is entirely unimplemented despite having toolbar and menu shortcuts configured.

[LOW] report_generator.py:650: `export_report_to_pdf` checks `hasattr(report, 'to_html')` and calls `report.to_html()`, but the `Report` dataclass has no `to_html()` method. The `hasattr` check returns `False`, so `str(report)` is used as HTML content. This produces a useless, unformatted PDF.

[LOW] report_generator.py:669: `export_report_to_excel` checks `hasattr(report, 'to_dataframe')` and calls `report.to_dataframe()`, but the `Report` dataclass has no `to_dataframe()` method. The check returns `False`, so the method returns `False` silently, and the user gets no error message explaining why Excel export failed.

### Chain 5: Chart Data Generation

[LOW] reports_window.py:1309-1336: `display_charts()` only implements charting for `ReportType.SALES_SUMMARY` and hardcodes Arabic keys `"المنتج"` and `"المبلغ"`. The `report_exporter.py` returns English column names like `"product_name"` and `"final_amount"`. So `item.get("المنتج")` always returns `None`, `item.get("المبلغ", 0)` always returns 0, and the pie chart shows 10 identical zero-value slices labeled "غير محدد".

[LOW] reports_window.py:1341-1368: The `display_summary()` method uses a triple-quoted string with `{report_data.title}`, `{self.start_date_edit.date()}`, etc. but the string has NO `f` prefix. The variables are never interpolated — the HTML displays literal `{report_data.title}` text. Additionally, line 1356-1358 computes `avg_invoice_value` as a bare expression `total_sales / len(report_data.data) if report_data.data else 0` but never assigns it to a variable, yet line 1364 references `avg_invoice_value` which would be `UnboundLocalError`.

[LOW] reports_window.py:917-919: The status bar time updater `self.time_timer.start(60000)` is commented out with note "معطّل لمنع التجميد" (disabled to prevent freezing). The time label is set once at init and never updates.

[LOW] reports_window.py:993-1008: `update_quick_stats()` has hardcoded zeros for `today_sales`, `today_invoices`, and `low_stock_count` with comments "يمكن جلبها من قاعدة البيانات" (can be fetched from DB). The welcome page stats always show 0.00 دج, 0, and 0.

[LOW] reports_window.py:960-985: `load_initial_data()` has all product, customer, and category loading code commented out. The combo boxes only contain the "الكل" (All) placeholder. Users cannot filter reports by specific products, customers, or categories.

[LOW] advanced_reports_window.py:86-96: `load_report_templates()`, `create_custom_report()`, `generate_report()`, `export_report()`, `schedule_report()`, and `preview_report()` are all stub methods that return dummy values or hardcoded lists without any real functionality. The window is a non-functional shell.

---

## Summary

| Severity | Count | Key Issues |
|---------|-------|-------------|
| CRITICAL | 5 | Inventory report non-f-string query; PRAGMA tuple indexing on DictRow; 3 methods use raw cursor (tuple) instead of DictRow; undefined `max_stock_col` variable; all inventory status reports broken |
| HIGH | 5 | Wrong column names in report_generator; non-standard sale_items columns; HAVING before GROUP BY; raw connection bypass; None separator crashes report generation |
| MEDIUM | 4 | Inconsistent date param formatting (datetime vs string); fragile string-replacement SQL building; CSV export missing pandas check; export string shim silently succeeds |
| LOW | 8 | Print unimplemented; PDF/Excel export produce garbage; chart uses wrong column keys; summary f-string not formatted; timer disabled; stats hardcoded zero; combos empty; advanced window is stub |
| **Total** | **22** |

The most impactful systemic issue is the **inventory status report being completely non-functional** (5 CRITICAL bugs chain together): the non-f-string query, undefined `max_stock_col` variable, and PRAGMA tuple indexing all conspire to make every inventory status report fail. The second most impactful cluster is the **three payment/cash-flow reports producing empty data** (CRITICAL): bypassing the DatabaseManager API with raw cursors means `get_value()` receives tuples instead of dicts, silently defaulting all fields to None/0. The third cluster is the **advanced_reports_window being entirely a stub shell** (LOW but worth noting): all 6 public methods return dummy values, making the window non-functional despite having a polished UI with filters, tabs, and export buttons.

---

# Worklog - Task 10-12: Settings / Reminders / Backup Deep Code Review

**Reviewer:** Automated Code Review Agent
**Date:** 2025-06-30
**Scope:** Complete settings, reminders, and backup/restore feature cycles
**Files traced:** backup_service.py, reminder_service.py, scheduler_service.py, user_service.py, user.py, notification_service.py, permission_service.py, system_management_window.py, user_management_dialog.py, company_management_window.py, permission_management_window.py, main_window.py, app_launcher.py, local_database_manager.py, database_manager.py

---

## Bug Report

### Chain 1: BACKUP — Create / List / Restore / Delete / Auto-backup

[CRITICAL] src/services/backup_service.py:22-38: Cryptography imports are inside a try/except (lines 23-32) that catches ImportError and sets `_CRYPTO_AVAILABLE = False`, but then the SAME imports are repeated UNCONDITIONALLY outside the try/except (lines 36-38). If the `cryptography` package is not installed, the try/except suppresses the error but lines 36-38 raise an unhandled `ImportError`, crashing the entire backup module on import. The `pass` on line 24 before the imports inside the try block is also suspicious dead code.

[CRITICAL] src/ui/system_management_window.py:435: `load_backups()` accesses `backup["name"]` but `BackupService.list_backups()` returns dicts with key `"backup_name"`, not `"name"`. This causes `KeyError` on every backup row, crashing the entire backup list display. The restore/delete lambda buttons on lines 467/471 also reference `backup["name"]` and will fail.

[CRITICAL] src/ui/system_management_window.py:438: `load_backups()` accesses `backup.get("date", "-")` but the backup dicts use key `"timestamp"`, not `"date"`. Every backup row shows "-" for the date column.

[CRITICAL] src/ui/system_management_window.py:453: `load_backups()` accesses `backup.get("type", "manual")` but no `"type"` field exists in the backup metadata. The description field contains the user's text (e.g. "نسخة احتياطية يدوية" or "نسخة احتياطية تلقائية - ..."), but there is no structured `type` field. All backups show "يدوي" (manual) regardless of origin.

[HIGH] src/services/backup_service.py:381-396: `delete_backup()` only checks for `.zip` and folder paths. It does NOT handle `.enc` (encrypted non-compressed) or `.zip.enc` (encrypted compressed) files. Encrypted backups cannot be deleted through this method — it always returns `False`.

[HIGH] src/ui/system_management_window.py:37-61: `BackupThread.run()` for the "restore" operation (line 54-56) calls `self.backup_service.restore_backup(**self.kwargs)` but IGNORES the return value. It always emits `finished.emit(True, ...)` even when `restore_backup` returns `{"success": False, "error": "..."}`. The user sees a success message even when restore fails.

[HIGH] src/services/backup_service.py:530-538: `disable_auto_backup()` calls `schedule.clear()` which clears ALL scheduled jobs globally, not just the backup job. If any other part of the application uses the `schedule` library, those jobs are silently destroyed.

[MEDIUM] src/services/backup_service.py:182-312: `restore_backup()` is typically called from a `BackupThread` (background QThread) but performs `self.db.connection.close()` and `self.db.initialize()` — these are NOT thread-safe. If the main thread is concurrently using the DB connection, this causes `sqlite3.ProgrammingError: closed database` or data corruption.

[MEDIUM] src/services/backup_service.py:258: During restore, `self.create_backup(description="...")` is called to save the current state. But `_log_backup` writes to `backup_history` table. After the DB is replaced (line 281), the pre-restore backup's history entry is lost since it was in the old DB.

### Chain 2: SETTINGS — Company Info / User Management / Permissions / DB Persistence

[CRITICAL] src/services/user_service.py:87,90: `_load_security_settings()` is called BEFORE `_create_security_tables()` in `__init__`. The `security_settings` table does not exist yet when the SELECT runs. The exception is caught silently (line 164), so security settings always load as defaults on first instantiation, ignoring any previously saved values.

[HIGH] src/ui/windows/main_window.py:8956: `on_notifications_interval_changed()` references `self.notifications_interval_spin` but the UI creates `self.notifications_interval_combo` (line 8783). This raises `AttributeError` when the user changes the notification check interval, crashing the handler.

[HIGH] src/ui/system_management_window.py:627: `cleanup_data()` calls `QMessageBox.getText(...)` but `QMessageBox` has no static `getText` method — that method belongs to `QInputDialog`. This will raise `AttributeError` at runtime when the user clicks "حذف السجلات القديمة".

[MIGH] src/ui/system_management_window.py:124: `show_users_tab()` sets `self.tabs.setCurrentIndex(0)` which navigates to the Backup tab (index 0), NOT the Users tab. The comment says "let's say Users is 0 for now or whatever" — this is an unresolved TODO/wrong mapping.

[MEDIUM] src/ui/system_management_window.py:904-931: `save_settings()` uses raw `cursor.execute("UPDATE system_settings SET value = ? WHERE key = ?")` for each setting. If a setting key was deleted from the table, the UPDATE silently affects 0 rows and the setting appears saved but isn't. Should use `INSERT OR REPLACE` or `UPSERT`.

[MEDIUM] src/ui/system_management_window.py:887-891: `load_settings()` uses raw `cursor.fetchall()` with `dict(cursor.fetchall())` to build `{key: value}`. While this works, it bypasses the DatabaseManager abstraction and is inconsistent with the rest of the codebase. The same pattern appears in `load_maintenance_log()` (lines 755-816) which uses `log[0]`, `log[1]`, etc. tuple indexing on raw cursor results — fragile and column-order dependent.

[MEDIUM] src/services/permission_service.py:184-195: `_init_default_roles()` creates the ADMIN role via `execute_update` and uses the returned `role_id` to insert `role_permissions`. However, `execute_update` returns `cursor.lastrowid` (from LocalDatabaseManager) or `cursor.rowcount` (from DatabaseManager). If `execute_update` returns rowcount (0 for some DB backends) instead of lastrowid, all role_permissions are inserted with `role_id=0`, breaking the entire permission system.

[LOW] src/ui/windows/permission_management_window.py:397-398: The role filter in `filter_users()` has a `TODO: تطبيق فلتر الدور` comment — the role filter is completely non-functional. Users are never filtered by role.

### Chain 3: REMINDERS — Create / Trigger / Send / Dismiss

[HIGH] src/services/reminder_service.py:91-117: `list_pending()` queries reminders with `status = 'pending'` but the `schedule_payment_reminder()` INSERT (line 68-84) does NOT set a `status` column. If the reminders table has a `status` column with a DEFAULT, this may work, but if it doesn't, the column is NULL and `status = 'pending'` never matches, so pending reminders are never found or sent.

[MEDIUM] src/services/reminder_service.py:119-175: `send_due_reminders()` has no deduplication. If the scheduler runs while a previous send is still in progress (e.g., slow email), the same reminders could be sent multiple times. The `attempts` counter is incremented but there's no check against max attempts before sending.

[MEDIUM] src/services/scheduler_service.py:23-93: `ReminderScheduler` has no `update_backup_schedule()` method, but `main_window.py:8866-8867` calls `self.reminder_scheduler.update_backup_schedule()` if it exists. This is a silent no-op due to `hasattr` check, but the intent (updating backup schedule from settings) is never implemented.

[MEDIUM] src/services/notification_service.py:360-379: `get_notifications()` uses raw `cursor.fetchall()` with tuple indexing (`row[0]`, `row[1]`, etc.) instead of the DatabaseManager's `fetch_all()` method. This is fragile and column-order dependent. Any schema change (adding/reordering columns) breaks this method. The same issue affects `get_unread_count()` (line 476), `check_inventory_alerts()` (lines 492-493), `check_payment_alerts()` (lines 524-525, 548-549), and `get_statistics()` (lines 596-625).

[LOW] src/services/reminder_service.py:177-186: `cancel_reminder()` sets `status='cancelled'` but there is no `dismiss_reminder()` or `delete_reminder()` method. The UI has no way to delete or dismiss individual reminders — they can only be cancelled (which is a status change, not deletion).

---

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 5 | Crypto import crash; backup list KeyError on wrong key ("name" vs "backup_name"); wrong date key ("date" vs "timestamp"); missing type field; security settings loaded before table creation |
| HIGH | 6 | Encrypted backup deletion impossible; restore always emits success; schedule.clear() kills all jobs; notification interval AttributeError; QMessageBox.getText crash; reminders never match pending status |
| MEDIUM | 7 | Thread-unsafe DB close/reopen; pre-restore backup history lost; save_settings silent no-op on missing keys; raw cursor tuple indexing (2 locations); execute_update return value ambiguity; no reminder dedup; update_backup_schedule missing |
| LOW | 2 | Role filter not implemented; no delete/dismiss reminder |
| **Total** | **20** |

The most impactful bug cluster is in the **backup list display** (system_management_window.py lines 435-467): three wrong dict keys (`"name"` → `"backup_name"`, `"date"` → `"timestamp"`, missing `"type"`) make the entire backup management tab crash on load. The second most critical cluster is the **cryptography import structure** (backup_service.py:22-38) which makes the backup service completely non-importable when the cryptography package is absent, despite having a try/except intended to handle that case. The third critical issue is the **user_service initialization order** that silently drops security settings on first run.

--- Task ID: 13a

## Sales Cycle Bug Fixes

### Bug 1: Double commit in create_sale() — CRITICAL
**File:** `src/models/sale.py:488`
**Problem:** `SaleManager.create_sale()` called `connection.commit()` inside the method, but its caller `SalesService.create_sale()` wraps the call in `self.db_manager.transaction()`. The transaction context manager does its own commit on success. The inner commit breaks atomicity — if steps after the inner commit fail (e.g., inventory update, accounting entry), the already-committed sale data cannot be rolled back.
**Fix:** Removed `connection.commit()` from line 488. The rollback at line 502 (now ~504) remains as safety net. The transaction context's commit handles the final commit.

### Bug 2: Soft delete uses English status value — CRITICAL
**File:** `src/models/sale.py:1904-1908`
**Problem:** `delete_sale(soft_delete=True)` set `status = 'cancelled'` (English), but the DB schema and `SaleStatus` enum store Arabic values (e.g., `'ملغية'`). This meant soft-deleted sales would never match any status filter/query. Also, `is_deleted` was never set to 1.
**Fix:** Changed query to `UPDATE sales SET status = 'ملغية', is_deleted = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?`

### Bug 3: SaleItem.discount_amount access — NO FIX NEEDED
**File:** `src/ui/dialogs/sales_dialog.py:1684`
**Finding:** `SaleItem` (sale.py:134-136) already has a `discount_amount` property that returns `self.discount`. The access at line 1684 (`item.discount_amount`) is valid. No code change required.

### Bug 4: Missing SaleManager.add_sale_item() — HIGH
**File:** `src/services/sales_service.py:767`
**Problem:** `SalesService.add_sale_item()` called `self.sale_manager.add_sale_item(item)` but `SaleManager` only had the private `_create_sale_item()` method. This would raise `AttributeError` at runtime.
**Fix:** Added public `add_sale_item(self, item: SaleItem)` method to `SaleManager` (sale.py:823-825) that delegates to `self._create_sale_item(item)`.

### Bug 5: Status/payment filter maps English values — HIGH
**File:** `src/ui/windows/main_window.py:5127-5145`
**Problem:** The sales list filter mapped Arabic combo box text to English values (e.g., `'ملغية'` → `'cancelled'`, `'نقدي'` → `'cash'`), but the DB stores Arabic values. The `SalesDataLoaderThread` passes these directly into `WHERE s.status = ?` / `WHERE s.payment_method = ?`, so the English values would never match any rows — all filtered queries returned empty results.
**Fix:** Replaced the English-mapping dicts with validation against known Arabic values. The combo box Arabic text is now passed directly to the SQL query after validating it's a known status/method value.

--- Task ID: 13b

### Bug 1: payment_service.py report methods use Arabic enum values in SQL WHERE clauses — CRITICAL
**Files:** `src/services/payment_service.py`
**Problem:** All 6 report methods (`get_payment_summary`, `get_cash_flow_report`, `get_payment_trends_analysis`, `get_payment_forecast`, `get_payment_performance_kpis`, `get_period_comparison_analysis`) passed `PaymentStatus.COMPLETED.value` ("مكتمل") and `PaymentType.*.value` (Arabic) as SQL parameters. Since `create_payment()` normalizes values to English before DB insertion, these queries matched zero rows.
**Fix:** Replaced all `PaymentStatus.COMPLETED.value` → `'completed'`, `PaymentType.CUSTOMER_PAYMENT.value` → `'customer_payment'`, `PaymentType.SUPPLIER_PAYMENT.value` → `'supplier_payment'` in SQL parameters and Python result comparisons across all 6 report methods (20 parameter substitutions + 4 Python comparison fixes).

### Bug 2: payment.py `_row_to_payment` uses raw tuple indexing
**File:** `src/models/payment.py` line 691
**Problem:** `_row_to_payment()` used `row[0]`, `row[1]`, etc. and could crash on string values (e.g., `Decimal(str(row[10]))` when `row[10]` is a string). Defaults also used Arabic enum values.
**Fix:** Added `isinstance(row, dict)` early return to `_row_to_payment_dict()` (the modern path). For the tuple fallback, wrapped all `Decimal()` conversions in safe helper functions and changed defaults from Arabic enum values to English-normalized strings (`'customer_payment'`, `'cash'`, `'pending'`).

### Bug 3: payment_dialog.py `payment.entity_id` AttributeError
**File:** `src/ui/dialogs/payment_dialog.py` lines 679-686
**Problem:** `payment.entity_id` was accessed on a `Payment` dataclass which has no `entity_id` attribute (only `customer_id` and `supplier_id`). Also `payment.payment_type` was compared against Arabic `PaymentType.CUSTOMER_PAYMENT.value` but DB stores English.
**Fix:** Replaced `payment.entity_id` with `payment.customer_id or payment.supplier_id`. Changed type comparison from `PaymentType.CUSTOMER_PAYMENT.value` to `'customer_payment'`.

### Bug 4: payment_dashboard.py chart data uses wrong dict keys
**File:** `src/ui/windows/payment_dashboard.py`
**Problem:** Dashboard chart methods expected flat/b incorrectly-keyed structures that didn't match the service response shapes:
- `update_kpis`: expected flat `kpis['total_amount']` but service returns `kpis['summary']['total_amount']`
- `update_trends_chart`: expected `trends_data['periods']` but service returns `trends_data['trends_data']` (nested by period→type)
- `update_forecast_chart`: expected `forecast_data['forecasts']` but service returns `forecast_data['predictions']` (dict of type→list)
- `update_comparison_chart`: expected `comparison_data['previous_period']['total_amount']` but service nests under `.data`
**Fix:** Updated all 4 methods to read from the correct nested keys, with fallback to the old flat format for backward compatibility.
--- Task ID: 13c

**Date:** $(date -u +'%Y-%m-%d %H:%M:%S UTC')
**Summary:** Fixed 3 CRITICAL bugs in the returns cycle.

### Bug 1 — INSERT schema mismatch (return_service.py)

**Problem:** `create_return()` inserted 32 columns into `return_invoices` and 16 columns into `return_items`, but the actual DB tables (created in `database_manager.py:751-772`) only have 6 and 5 columns respectively:
- `return_invoices`: id, original_invoice_id, return_date, reason, total_refund_amount, status
- `return_items`: id, return_id, product_id, quantity, refund_price

**Fix:** Rewrote both INSERT statements in `create_return()` to match the actual schema. Also fixed the same mismatch in `update_return()` (UPDATE + re-INSERT of items) which had identical column count errors.

Field mapping:
| Model field | DB column |
|---|---|
| original_sale_id | original_invoice_id |
| return_reason (enum→str) | reason |
| total_amount (float) | total_refund_amount |
| status (enum→str) | status |
| return_date | return_date |
| quantity_returned | quantity |
| unit_price | refund_price |

### Bug 2 — cursor.description staleness (return_service.py:459-478)

**Problem:** In `get_all_returns()`, the outer loop read `cursor.description` on every iteration. The inner `SELECT * FROM return_items` on the same cursor overwrote `cursor.description`, so on the 2nd+ iteration of the outer loop the invoice row was zipped with return_items column names — corrupting data.

**Fix:** Capture `invoice_columns` once before the loop and use a separate `item_cursor` for the inner SELECT.

### Bug 3 — Dead code: SaleModel.process_return() (sale.py:1840-1885)

**Problem:** `SaleModel.process_return()` inserts into the `sales` table with a `RET-` prefix, completely bypassing the dedicated `return_invoices`/`return_items` tables managed by `ReturnService`. Grep confirmed it is NOT called from any production code (only a legacy unit test references it).

**Fix:** Added a detailed deprecation docstring directing callers to `ReturnService.create_return()`. Body retained for test backward-compat.

### Additional notes
- `get_all_returns()` filters on `return_type`, `customer_id`, `supplier_id` reference columns that don't exist in the current schema. Added a NOTE comment; a future migration is needed if rich filtering is required.
- `generate_return_number()` queries `return_number` column which doesn't exist in the actual schema — will need a schema migration or fallback.

--- Task ID: 13d

**Scope:** Fix 5 CRITICAL bugs in purchase/order cycle.

### Bug 1 — `purchase_order_service.py:249` — UPDATE references non-existent columns
**Problem:** `update_purchase_order` SET clause includes `related_invoice_id` and `invoice_matched`, which are not in the base `purchase_orders` DDL. The `ensure_match_columns()` method exists but was never called before the UPDATE, causing an operational error on databases that haven't been migrated.
**Fix:** Added `self.ensure_match_columns()` call at the top of `update_purchase_order()`, before the SQL query. This uses the existing ALTER TABLE logic to add the columns lazily if missing.

### Bug 2 — `purchase_order_service.py:296-301` — DELETE+INSERT orphans receiving_items FKs
**Problem:** Editing a PO deleted ALL `purchase_order_items` rows and re-inserted them with new auto-increment IDs. This broke `receiving_items.po_item_id` foreign keys, since those pointed to the old (now-deleted) item IDs.
**Fix:** Replaced DELETE+INSERT with a new `_sync_po_items()` method that:
- Fetches existing DB items and identifies which have linked `receiving_items` (protected)
- UPDATEs existing items in-place (preserving their IDs)
- INSERTs only genuinely new items
- DELETEs only removed items that have no receiving_items linked
Added a new `_update_po_item()` helper method for the UPDATE SQL.

### Bug 3 — `purchase_order_dialog.py:414,777` — Lambda closure captures signal arg instead of row
**Problem:** `lambda r=row: self._on_product_changed(r)` appears to capture `row` via default argument, but the `currentIndexChanged(int)` signal always passes one positional argument. Python binds the signal's index to `r`, overriding the default — so `_on_product_changed` receives the combo box index instead of the table row number.
**Fix:** Changed to `lambda val, r=row: self._on_product_changed(r)` on both lines 414 and 777. The `val` parameter consumes the signal argument, allowing `r` to use its default value `row`.

### Bug 4 — `purchase_order_service.py:835-843` — SUM(total_amount) on table without that column
**Problem:** 3-way match queried `SELECT COALESCE(SUM(total_amount), 0) FROM receiving_notes`, but `receiving_notes` has no `total_amount` column (only metadata fields). This would either raise an error or return NULL/0.
**Fix:** Replaced with a 3-table JOIN: `receiving_items ri JOIN receiving_notes rn JOIN purchase_order_items poi`, computing `SUM(ri.quantity_received * poi.unit_price)` to derive the received amount from actual item data.

### Bug 5 — `purchase_orders_window.py:656-658` — `_update_table_with_pos` was empty no-op
**Problem:** The status/priority filter combo called `_filter_pos()` → `get_all_purchase_orders(status=..., priority=...)` → `_update_table_with_pos(pos)`, but that method was an empty stub with only a comment. Filtering did nothing.
**Fix:** Implemented `_update_table_with_pos()` with the same table-population logic as `_load_purchase_orders()` — clears the table, iterates POs, inserts rows with proper formatting (status colors, priority colors, overdue highlighting, receipt percentages), and updates statistics labels.

### Files modified
- `src/services/purchase_order_service.py` (Bugs 1, 2, 4)
- `src/ui/dialogs/purchase_order_dialog.py` (Bug 3)
- `src/ui/windows/purchase_orders_window.py` (Bug 5)

### Verification
- All 3 files pass `ast.parse()` syntax check.

--- Task ID: 13e

## CRITICAL Bug Fixes - Backup/Returns/Other

### Bug 1: backup_service.py — Unconditional crypto imports defeat try/except
**File:** `src/services/backup_service.py`
**Problem:** Lines 33-38 unconditionally re-imported `cryptography.fernet.Fernet`, `hashes`, and `PBKDF2HMAC` outside the try/except block. If the `cryptography` package was not installed, the module would fail to import at all, making even non-encrypted backups impossible.
**Fix:**
- Removed the duplicate unconditional imports (lines 33-38)
- Moved `from base64 import urlsafe_b64decode, urlsafe_b64encode` into the standard import block (it has no optional dependency)
- Removed the empty `pass` statement inside the try block
- Added `self._fernet = None` initialization in `__init__` (was missing, would cause `AttributeError` in encryption guard checks)

### Bug 2: system_management_window.py — Wrong backup dict keys causing KeyError
**File:** `src/ui/system_management_window.py`
**Problem:** `list_backups()` returns dicts with keys `backup_name`, `timestamp`, `file_size` — but the UI code used `backup["name"]` (KeyError), `backup.get("date")` (returns "-"), and `backup.get("type")` (non-existent field). The lambda callbacks for restore/delete buttons also used `backup["name"]`.
**Fix:**
- Line 435: `backup["name"]` → `backup["backup_name"]`
- Line 438: `backup.get("date", "-")` → `backup.get("timestamp", "-")`
- Line 453: `backup.get("type", "manual")` → infer type from description field ("تلقائي"/"automatic" keyword)
- Lines 467, 471: Lambda `backup["name"]` → `backup["backup_name"]`

### Bug 3: reminder_service.py — INSERT missing status='pending'
**File:** `src/services/reminder_service.py`
**Problem:** `schedule_payment_reminder()` INSERT omitted the `status` column. While the DB has `DEFAULT 'pending'`, explicit setting is required for reliability across DB backends and clarity.
**Fix:** Added `status` to the INSERT column list and `'pending'` to the VALUES tuple.

### Bug 4: payment_service.py — Arabic .value in Python if/elif comparisons
**File:** `src/services/payment_service.py`
**Finding:** No Python if/elif comparisons use `PaymentStatus.COMPLETED.value` or `PaymentMethod.CASH.value`. All if/elif comparisons in report methods already use English strings (e.g., `payment_type == 'customer_payment'`). No changes needed.
**Note:** SQL parameter bindings at lines 639, 695, 805 still pass `PaymentStatus.COMPLETED.value` (Arabic "مكتمل") — these may need separate attention if the DB was migrated to English status values.

### Bug 5: purchase_order_service.py — Supplier balance never updated on PO receipt
**File:** `src/services/purchase_order_service.py`
**Problem:** `receive_shipment()` updated inventory, batches, and accounting entries, but never called `SupplierManager.update_supplier_balance()`. The supplier's `current_balance` (debt) stayed at 0 even after receiving goods.
**Fix:** Added a call to `SupplierManager.update_supplier_balance(supplier_id, po_total)` inside `receive_shipment()`, after the accounting entry and before COMMIT. The PO's total amount is added to the supplier's current balance, increasing their debt. Wrapped in try/except to avoid breaking the transaction on failure.

### Files modified
- `src/services/backup_service.py`
- `src/ui/system_management_window.py`
- `src/services/reminder_service.py`
- `src/services/purchase_order_service.py`

### Verification
- All 4 files pass `ast.parse()` syntax check.

--- Task ID: 13f

# Fix CRITICAL reports cycle bugs

## Summary
Fixed 4 confirmed bugs in `src/services/report_exporter.py`. One reported bug (si.total_price) was a false alarm after schema verification.

## Bug 1 + Bug 3: Inventory status report (lines 442-498)
**File:** `src/services/report_exporter.py` — `generate_inventory_status_report()`

**Root cause (5 chained issues):**
1. Line 449: `row[1]` on DictRow from `fetch_all("PRAGMA table_info(products)")` — fragile integer index
2. Line 471: Expression `"COALESCE(p.max_stock, 0)" if has_max_stock else "0"` was a bare expression, never assigned to `max_stock_col`
3. Lines 473-498: Query was a plain string `"""..."""`, not an f-string, so `{max_stock_col}`, `{supplier_select}`, `{supplier_join}` were literal brace text in SQL
4. Lines 469-470: `# noqa: F841` comments indicated the variables were known-unused

**Fix:**
- Changed `row[1]` → `row['name']` (DictRow key for PRAGMA table_info 'name' column)
- Assigned the max_stock expression to `max_stock_col = "COALESCE(p.max_stock, 0)" if has_max_stock else "0"`
- Converted query to f-string (`f"""..."""`) so `{max_stock_col}`, `{supplier_select}`, `{supplier_join}` are interpolated
- Removed `# noqa: F841` comments since variables are now used

## Bug 2: Raw cursor.fetchall() returning tuples in 3 payment/cash-flow reports
**File:** `src/services/report_exporter.py`

**Locations:**
- Line 2062 (cash flow daily report)
- Line 2157 (payment analysis by type/method)
- Line 2235 (payment method distribution)

**Root cause:** All three used `self.db_manager.connection.cursor(); cursor.execute(...); cursor.fetchall()` which returns raw `tuple` objects. The downstream `get_value(row, 'column_name')` calls would silently return `None` (default) for every column since tuples don't support string keys.

**Fix:** Replaced each 3-line block with `self.db_manager.execute_query(query, tuple(params), exclude_deleted=False)` which returns `DictRow` (dict subclass) objects. Used `exclude_deleted=False` to avoid automatic is_deleted injection into already-complex queries.

## Bug 4: si.total_price column name
**File:** `src/services/report_exporter.py` (and `report_generator.py`)

**Finding:** Verified the actual `sale_items` table schema in `src/core/local_database_manager.py:475-494`. The table DOES have a `total_price DECIMAL(10,2) NOT NULL` column. Therefore `si.total_price` is the correct column name. **No fix needed** — this was a false alarm.

## Bug 5: HAVING before GROUP BY
**File:** `src/services/report_exporter.py` — `generate_customer_analysis_report()`

**Root cause:** Line 1358 appended `HAVING total_purchases >= ?` before line 1361 appended `GROUP BY ...`. SQL requires GROUP BY before HAVING.

**Fix:** Reordered so GROUP BY comes first, then HAVING, then ORDER BY.

## Files modified
- `src/services/report_exporter.py`

## Verification
- File passes `ast.parse()` syntax check.

--- Task ID: 14a

**Date:** 2025-07-20
**Scope:** Fix 5 HIGH severity login/logout cycle bugs

## Bug 1 + 2: Session never terminated on logout + timers not stopped
**Files:** `main.py`
**Root cause:** `handle_logout()` and `cleanup()` called `self.user_service.logout_user(self.current_user.id)` passing an `int` user_id instead of the `str` session_id that `logout_user()` expects. Also, `session_monitor_timer` and `activity_timer` were never stopped in `handle_logout()`.
**Fix:**
- Added `self.current_session = None` initialization in `__init__` (line 368).
- Stored `self.current_session = session` in `show_mandatory_login_dialog()` after successful login (line 624).
- Rewrote `handle_logout()` to: (a) stop and nullify both timers first, (b) call `logout_user(self.current_session.session_id)` with the correct str session_id, (c) fallback to `terminate_all_sessions(user_id)` if session is missing, (d) nullify `self.current_session`.
- Rewrote `cleanup()` session termination to use `self.current_session.session_id` with a closure-captured variable (`sid=session_id`), with fallback to `terminate_all_sessions`.

## Bug 3: _load_security_settings() called before _create_security_tables()
**File:** `src/services/user_service.py`
**Root cause:** On first run, `security_settings` table doesn't exist yet when `_load_security_settings()` runs the SELECT. The query fails silently and all security settings stay at hardcoded defaults forever.
**Fix:** Swapped the call order — `_create_security_tables()` now runs before `_load_security_settings()` (lines 86-90).

## Bug 4: Duplicate incompatible CREATE TABLE login_attempts
**Files:** `src/services/user_service.py`, `src/services/security_service.py`
**Root cause:** Two `CREATE TABLE IF NOT EXISTS login_attempts` with different schemas — user_service had (id, username, ip_address, timestamp, success, failure_reason, created_at) while security_service had (id, username, ip_address, user_agent, success, created_at). Whichever ran first won, and the loser's INSERT would fail (missing `user_agent` column in user_service schema, missing `failure_reason`/`timestamp` in security_service schema).
**Fix:**
- Added `user_agent TEXT` column to user_service.py's unified schema (now has all 8 columns).
- Removed the duplicate `CREATE TABLE login_attempts` from security_service.py `_ensure_tables()`, replaced with a comment explaining the table is managed by UserService.

## Bug 5: 2FA silently bypassed if table missing
**File:** `src/ui/dialogs/login_dialog.py`
**Root cause:** The `except Exception: needs_2fa = False` at line 829 silently swallowed any error (including missing `user_2fa` table), allowing login without 2FA when it was enabled.
**Fix:** Replaced the bare except with a handler that: (a) checks for `sqlite3.OperationalError` with "no such table" message, (b) shows a `QMessageBox.warning` to the user explaining that 2FA was bypassed due to a missing table, (c) logs the error at ERROR level, (d) for other exceptions, logs at WARNING level.

## Files changed
- `main.py` — handle_logout, cleanup, __init__, show_mandatory_login_dialog
- `src/services/user_service.py` — __init__ reordering, unified login_attempts schema
- `src/services/security_service.py` — removed duplicate login_attempts CREATE TABLE
- `src/ui/dialogs/login_dialog.py` — 2FA table-missing warning

--- Task ID: 14b

## HIGH Severity Product/Inventory Bug Fixes

**Date:** 2025-07-20
**Scope:** Products CRUD cycle — service layer, repository, and UI dialog

### Bug 1+2: update_product() hardcoded 22 columns + base_price/selling_price mismatch
**File:** `src/services/product_service_enhanced.py` (was lines 208-261)
**Problem:** `update_product()` had a static SQL string with 22 column names. If any column was missing from the actual DB schema (e.g., migration not yet applied), the entire UPDATE would fail. Additionally, it only wrote to `base_price`, but migration 015 adds a `selling_price` column — some DBs have both, some only one.
**Fix:** Replaced the hardcoded UPDATE with a dynamic approach: build a `col_map` dict, query `PRAGMA table_info(products)` to get existing columns, and only include columns that exist. Both `base_price` and `selling_price` are added to the map; the PRAGMA filter ensures only extant columns are included.

### Bug 3: create_product() uses execute_query instead of execute_insert
**File:** `src/services/product_service_enhanced.py` (was line 99)
**Problem:** `create_product()` called `self.db_manager.execute_query()` for INSERT, then separately called `get_last_insert_id()`. `execute_query` is designed for SELECTs (returns `List[Dict]`); using it for INSERT relies on a legacy code-path that returns a cursor. `execute_insert` is purpose-built for INSERTs and directly returns `lastrowid`.
**Fix:** Changed to `self.db_manager.execute_insert(query, tuple(insert_vals))` which returns the new row ID directly, removing the fragile `try/except get_last_insert_id()` pattern.

### Bug 4: ProductRepository uses is_deleted = 0 but products table uses is_active
**File:** `src/repositories/product_repository.py` (lines 31, 48, 68, 75, 96)
**Problem:** Five queries used `is_deleted = 0` as a soft-delete filter, but the products table (defined in `migrations/001_create_enhanced_tables.sql`) uses `is_active` for soft-delete — there is no `is_deleted` column. These queries would raise `OperationalError: no such column: is_deleted` at runtime.
**Fix:** Changed all five occurrences of `is_deleted = 0` to `is_active = 1`. Lines 68 and 75 already had `AND is_active = 1`, so the duplicate `AND is_deleted = 0` was simply removed, leaving a single correct filter.

### Bug 5: Product dialog save paths silently discard UI-collected fields
**File:** `src/ui/dialogs/product_dialog.py` (lines 1201, 1319)
**Problem:** `collect_form_data()` (line 1040) collects `supplier_id` among other fields, but the two EnhancedProduct constructor calls (edit path line 1201, create path line 1319) did not pass `supplier_id` to the model. The value was silently dropped, meaning supplier assignments made in the UI were never persisted.
**Fix:** Added `supplier_id=data.get("supplier_id")` to both EnhancedProduct constructor calls. The legacy Product model does not have a `supplier_id` field, so the legacy paths were left unchanged (those paths are only used when the enhanced service is unavailable).

### Files changed
- `src/services/product_service_enhanced.py` — dynamic update_product, execute_insert in create_product
- `src/repositories/product_repository.py` — is_deleted→is_active filter correction (5 sites)
- `src/ui/dialogs/product_dialog.py` — supplier_id passed to EnhancedProduct in 2 save paths

--- Task ID: 14c

### Bug 1: Non-atomic update_balance() in customer.py (race condition)
**File:** `src/models/customer.py:596`
**Problem:** `update_balance()` performed a read-then-write (fetch customer, compute new_balance in Python, UPDATE with absolute value). Under concurrent requests two threads could read the same balance, each compute independently, and one overwrite the other.
**Fix:** Replaced with atomic SQL: `UPDATE customers SET current_balance = current_balance + ? (or - ?) WHERE id = ?`. Removed the redundant `get_customer_by_id()` call.

### Bug 2: Non-atomic update_supplier_balance() in supplier.py (race condition)
**File:** `src/models/supplier.py:421`
**Problem:** Same read-modify-write race condition as customer.py.
**Fix:** Replaced with atomic SQL: `UPDATE suppliers SET current_balance = current_balance + ? WHERE id = ?`. The `amount_change` parameter already carries the correct sign, so a single `+` suffices.

### Bug 3: Customer list shows soft-deleted records
**File:** `src/ui/dialogs/customer_management_dialog.py:104`
**Problem:** Query lacked `WHERE is_active = 1`, so soft-deleted customers (is_active=0) appeared in the management list.
**Fix:** Added `WHERE is_active = 1` to the SELECT query.

### Bug 4: Supplier list shows soft-deleted records
**File:** `src/ui/dialogs/supplier_management_dialog.py:104`
**Problem:** Same missing soft-delete filter as bug 3.
**Fix:** Added `WHERE is_active = 1` to the SELECT query.

### Bug 5: Raw cursor tuple indexing in notification_service.py
**File:** `src/services/notification_service.py:360-379`
**Problem:** `get_notifications()` used raw `cursor.execute()` + `cursor.fetchall()` with positional indexing (row[0], row[1], …). Since `fetch_one`/`fetch_all` return `Dict[str, Any]` via `DictRow`, this was fragile and inconsistent with the rest of the codebase.
**Fix:** Replaced raw cursor usage with `self.db.fetch_all(query, tuple(params))` and switched all positional accesses to dict-key accesses (e.g. `row["id"]`, `row["title"]`). Also removed the now-unused `cursor = self.db.connection.cursor()` line.

### Bug 6: Arabic PaymentType enum values passed as SQL parameters
**File:** `src/services/payment_service.py` (lines 248, 335, 462, 765)
**Problem:** `PaymentType.CUSTOMER_PAYMENT.value` resolves to `"دفعة عميل"` (Arabic) and `PaymentType.SUPPLIER_PAYMENT.value` to `"دفعة مورد"` (Arabic). The database and comparison queries expect English strings `'customer_payment'` / `'supplier_payment'`. This caused payment type lookups and comparisons to silently fail.
**Fix:** Replaced all 4 occurrences with hardcoded English strings `'customer_payment'` and `'supplier_payment'`.

### Bug 7: Wrong widget name in main_window.py notifications handler
**File:** `src/ui/windows/main_window.py:8947`
**Problem:** `on_notifications_interval_changed()` referenced `self.notifications_interval_spin.value()` but the widget is a `QComboBox` named `self.notifications_interval_combo`. This would raise `AttributeError` at runtime.
**Fix:** Changed to `self.notifications_interval_combo.currentData()` which correctly reads the minute-value stored as user data in the combo box items.

### Files changed
- `src/models/customer.py` — atomic update_balance
- `src/models/supplier.py` — atomic update_supplier_balance
- `src/ui/dialogs/customer_management_dialog.py` — is_active filter
- `src/ui/dialogs/supplier_management_dialog.py` — is_active filter
- `src/services/notification_service.py` — fetch_all + dict access
- `src/services/payment_service.py` — English payment type strings
- `src/ui/windows/main_window.py` — correct combo box widget reference

--- Task ID: 1
**Audit: Crash-Point Analysis of Main Entry → Login → MainWindow Loading**
**Scope:** main.py, src/ui/windows/main_window.py, src/ui/dialogs/login_dialog.py
**Method:** Full line-by-line trace from `if __name__ == '__main__'` through splash → DB init → login → MainWindow.__init__ → setup_ui → dashboard load. Every potential unhandled exception, None-dereference, wrong-type, and missing-key access was checked.

============================================================
CRASH-POINTS FOUND
============================================================

[CRASH-1] main_window.py:5231 — `_on_sales_data_loaded`: unconditional `import pandas as pd` OUTSIDE the try/except block.
  Why: If pandas is not installed, `ImportError` is raised before the try block at line 5233. The signal handler runs on the GUI thread; the exception propagates to the Qt event loop and terminates the application. The module-level `PANDAS_AVAILABLE` guard (line 114) is not consulted here.
  Impact: App crash when sales tab data loads and pandas is missing.

[CRASH-2] main_window.py:5478-5480 — `refresh_purchases_data`: `f"{purchase.get('total_amount', 0):,.2f}"` and same for `paid_amount`, `remaining_amount`.
  Why: `.get('total_amount', 0)` returns `None` when the key EXISTS but its value is `NULL` in the database. `dict.get()` only uses the default when the key is MISSING. Then `f"{None:,.2f}"` raises `TypeError`. The `purchase_service.list_purchases()` can return rows where these columns are NULL (e.g., draft purchases).
  Impact: `TypeError` crash when viewing purchases with NULL amounts.

[CRASH-3] main_window.py:3493-3498 — `update_dashboard_activities_table`: DUPLICATE except clauses.
  Why: Line 3493 has `except Exception as e:` and line 3497 has `except (KeyError, ValueError, TypeError, AttributeError) as e:`. In Python, the second except is unreachable code because `Exception` already catches everything. More critically, the second except block at line 3497-3504 accesses `self.dashboard_activities_table` and calls `table.setRowCount(1)` / `table.setItem(0, 0, info_item)` — but at this point the table's `clearSpans()` at line 3477 and `setRowCount(len(activities))` at line 3478 may have already succeeded for SOME rows before the exception. The second except handler then sets row count to 1, but the first except handler at line 3493-3495 logs and exits silently — meaning neither handler properly cleans up partial state. While this is a logic bug rather than a hard crash (both excepts handle the error), the dead code indicates a merge/rebase error that could mask real failures.
  Impact: Silent data corruption of the activities table on partial failure. Not a hard crash, but a data-integrity issue.

[CRASH-4] main_window.py:3290 — `_populate_dashboard_analytics`: `customer_row["id"]` on line 3290 (standalone expression with no assignment, looks like a debug leftover) followed by `customer_row["name"]` at 3291.
  Why: If `data["customers"]` contains a dict that lacks the `"id"` or `"name"` key (e.g., if the SQL query schema changes or a JOIN fails), `KeyError` is raised. The outer try/except at line 3359 catches `(KeyError, ValueError, TypeError, AttributeError)`, so this won't crash the app — it will silently skip the update. However, if the exception is NOT one of those four types (e.g., `RuntimeError` from a deleted widget), it WILL propagate. Same applies to lines 3324-3327 for `product_row["id"]`, `product_row["name"]`, etc.
  Impact: Low — caught by except, but fragile. A `RuntimeError` from Qt widget deletion would bypass the narrow except.

[CRASH-5] main_window.py:2755 — `_populate_dashboard_data`: `top_insight["message"]`.
  Why: `top_insight` comes from `ai_service.get_proactive_insights()`. If the AI service returns a dict without a `"message"` key, `KeyError` is raised. This IS inside the outer try/except (line 2805 catches `Exception`), so it won't crash the app. However, it will skip the entire dashboard data population including the financial KPI update below it (lines 2810-2835).
  Impact: Medium — not a hard crash, but a silent data-loss bug. If AI insights fail, the entire `_populate_dashboard_data` short-circuits and financial KPIs are never updated.

[CRASH-6] main_window.py:2746-2748 — `_populate_dashboard_data`: `AIPredictionService(self.db_manager)` instantiated on every dashboard data load.
  Why: Every time dashboard data is loaded (including auto-refresh every 60 seconds), a NEW `AIPredictionService` is created. If the constructor fails (e.g., missing model file, broken DB connection), the exception is caught at line 2805, but it causes the same short-circuit as CRASH-5 — financial KPIs never update.
  Impact: Medium — same silent data-loss pattern as CRASH-5.

[CRASH-7] main_window.py:5231 + 5235 — `_on_sales_data_loaded`: no `PANDAS_AVAILABLE` guard.
  Why: Even though pandas IS imported at line 5231 (which itself is CRASH-1), the method at line 5235 checks `isinstance(data, pd.DataFrame)`. If the `SalesDataLoaderThread` at line 5181 emits data as a non-DataFrame, non-dict type, the method falls through to the else branch at line 5243-5248 and silently returns. This is not a crash, but the method can never handle dict data from `DataLoaderWorker` because `SalesDataLoaderThread` is always used instead (line 5181 replaces the worker created at line 5176 — the first `DataLoaderWorker` at line 5176 is created then immediately discarded).
  Impact: Dead code at lines 5139-5176 (the `load_sales()` closure and first `DataLoaderWorker` are never used). Not a crash but a code smell indicating potential logic confusion.

[CRASH-8] main_window.py:612 — `__init__` → `self.logger.debug(f"Status timer initialization skipped: {e}")` when `self.logger` is None.
  Why: `self.logger` is passed as a parameter to `MainWindow.__init__`. If `None` is passed (unlikely but possible), then `self.logger.debug(...)` at line 612 raises `AttributeError`. However, this is inside `except (AttributeError, RuntimeError)` which catches `AttributeError`, so it would be silently swallowed... but the `self.logger.debug()` call itself would raise `AttributeError` AGAIN before logging, creating an infinite recursion... actually no, because the except catches it. But the debug message is lost.
  Impact: Low — caught by except, but indicates missing None guard.

[CRASH-9] main_window.py:685-689 — `init_services` → `PaymentService(self.db_manager, self.logger)` when PaymentService import fails silently.
  Why: Line 686: `self.payment_service = PaymentService(self.db_manager, self.logger)`. If the `PaymentService` import at line 681 fails (caught at line 688), `self.payment_service` remains `None`. Later at line 784 in `show_main_window`, `self.payment_service` (which is `None`) is passed to `MainWindow`. Inside MainWindow, `self.payment_service` is used at line 633 to set `self._passed_payment_service = None`, and then at line 684-689, if `not self.payment_service`, a NEW `PaymentService` is created. If this second import ALSO fails, `self.payment_service` remains `None`. This is handled, but if any code later calls `self.payment_service.some_method()` without a None check, it crashes.
  Impact: Low — most callers check for None, but not all.

[CRASH-10] main_window.py:2320 — `refresh_dashboard_stats`: `conn.execute(query_stats)` uses raw `self.db_manager.connection.execute()` when `self.db_manager.connection` exists.
  Why: This bypasses the `execute_query()` method which returns `List[Dict]` and instead gets a raw `cursor.fetchone()` which returns a tuple. The code at line 2331 correctly indexes the tuple as `row[0]`, `row[1]`, etc. However, if the query returns NO rows (e.g., empty tables), `row` is `None` and line 2331 `row[0]` raises `TypeError: 'NoneType' object is not subscriptable`. This IS guarded by line 2326 `if not row: return`, so it's safe.
  Impact: None — properly guarded. No crash.

[CRASH-11] login_dialog.py:221 — `SecurityService(user_service.db)` — fragile attribute access.
  Why: `user_service.db` is set in `UserService.__init__` at line 75. If `user_service` is ever passed as a raw `DatabaseManager` instead of a `UserService` instance (as in the standalone test at line 992), `user_service.db` raises `AttributeError`. In the main application flow this is safe because `main.py:597` passes `self.user_service` which is always a `UserService`. But the standalone test at line 992 will crash.
  Impact: Standalone test crash only. Main flow is safe.

[CRASH-12] main_window.py:9733 — `update_statusbar_metrics`: `last_check.strftime('%H:%Mf')` — likely a typo.
  Why: The format string `'%H:%Mf'` is invalid. It should probably be `'%H:%M:%S'` or `'%H:%M:%S.%f'`. The `%Mf` format specifier doesn't exist in Python's strftime. This raises `ValueError`. However, this is inside a try/except at line 9730-9735, so it's caught.
  Impact: None — caught by except. But the tooltip will never be set.

[CRASH-13] main_window.py:1643 — `create_dashboard_tab`: `SmartAssistantWidget` created TWICE.
  Why: Line 791 in `init_services` creates `self.smart_assistant_widget = SmartAssistantWidget(self)`. Then line 1643 in `create_dashboard_tab` creates it AGAIN: `self.smart_assistant_widget = SmartAssistantWidget(self)`, replacing the first one. The first widget (from `init_services`) loses its parent reference and becomes a leaked QWidget. The signal `command_received` from the first widget at line 793 is connected to `handle_ai_command`, but after replacement, this connection points to the OLD widget. The NEW widget at line 1645 connects to `handle_ai_command` (redundantly). If the old widget receives any signals before garbage collection, it could cause issues. Not a hard crash but a resource leak.
  Impact: Memory leak + potential signal routing confusion.

============================================================
SUMMARY
============================================================

| # | Severity | File:Line | Issue |
|---|----------|-----------|-------|
| 1 | **CRITICAL** | main_window.py:5231 | `import pandas` outside try/except in signal handler |
| 2 | **HIGH** | main_window.py:5478 | `None:,.2f` TypeError when purchase amount is NULL |
| 3 | LOW | main_window.py:3493 | Duplicate except clause — dead code |
| 4 | LOW | main_window.py:3290 | Narrow except catches KeyError but not RuntimeError |
| 5 | MEDIUM | main_window.py:2755 | AI insight KeyError short-circuits entire dashboard update |
| 6 | MEDIUM | main_window.py:2746 | AI service instantiation failure short-circuits dashboard |
| 7 | LOW | main_window.py:5176 | Dead code — DataLoaderWorker immediately replaced |
| 8 | LOW | main_window.py:612 | Missing None guard on self.logger in except handler |
| 9 | LOW | main_window.py:685 | PaymentService None propagation |
| 10 | OK | main_window.py:2320 | Properly guarded |
| 11 | LOW | login_dialog.py:221 | Standalone test only — user_service.db attr access |
| 12 | OK | main_window.py:9733 | Caught by except (but typo in strftime) |
| 13 | LOW | main_window.py:1643 | SmartAssistantWidget created twice — memory leak |

**Critical path verified SAFE:**
- main.py `if __name__ == '__main__'` → `main()` → `InventoryManagementApp.__init__` → `run()` → splash → DB init worker → `on_init_completed` → `initialize_services` → `show_mandatory_login_dialog` → `LoginDialog` → `handle_login` → `authenticate_user` → `on_login_completed` → `show_main_window` → `MainWindow.__init__` → `init_services` → `setup_ui` → `switch_page('dashboard')` → `create_dashboard_tab` → `refresh_dashboard_stats`
- None-dereference on `fetch_one()` results: All critical paths either check for None or use `.get()` with defaults.
- Signal emission with wrong args: `DataLoaderWorker.data_loaded` emits `object`, `error_occurred` emits `str` — both correctly typed.
- Timer callbacks: `_status_timer` (5s), `stability_timer` (2min), `dashboard_refresh_timer` (60s) — all guarded with try/except.


--- Task ID: 2

# Crash-Point Audit — All Dialog Files

**Auditor:** Automated Crash-Point Audit Agent  
**Date:** 2025-06-30  
**Scope:** 6 dialog files — every line that can crash the application  
**Context:** `fetch_one` returns `Dict[str,Any] | None`; `.get('key')` returns None if key missing; `int(None)`, `float(None)`, `Decimal(None)` all raise TypeError; `None.strftime(...)` raises AttributeError; `None <= 0` raises TypeError.

---

## FILE 1: src/ui/dialogs/payment_dialog.py

[CRASH] payment_dialog.py:141: `self.apply_prefill_data()` — Method **does not exist** anywhere in the class hierarchy (BaseDialog, PaymentDialog). Called unconditionally in `__init__`. **Every instantiation of PaymentDialog crashes with `AttributeError`.** This is a guaranteed, unconditional crash.

[CRASH] payment_dialog.py:530: `f"{inv} (متبقي: {rem:.2f})"` — `rem` comes from `r["remaining_amount"]` (line 528). If the `sales` table has `remaining_amount = NULL`, `rem` is None, and the `:.2f` format spec raises `TypeError`.

---

## FILE 2: src/ui/dialogs/sales_dialog.py

[CRASH] sales_dialog.py:995: `int(product_data["current_stock"])` — `product_data["current_stock"]` is set from `product.current_stock` (line 888). The Product model's `__post_init__` only converts `current_stock` if `isinstance(value, (int, float, str))`; if the DB column is NULL, the field stays None. `int(None)` raises `TypeError`.

[CRASH] sales_dialog.py:1081: `if item["stock"] <= 0:` — `item["stock"]` is set from `product.current_stock` via `load_sale_items` (line 1671: `stock = product.current_stock if product else 0`). If `product` is not None but `product.current_stock` is None, `stock` is None, and `None <= 0` raises `TypeError`.

[CRASH] sales_dialog.py:1187: `self.table.item(row, 4).setText(...)` — If `self.table.item(row, 4)` returns None (e.g. cell was cleared or row index is stale after concurrent modification), `.setText()` raises `AttributeError: 'NoneType' object has no attribute 'setText'`.

[CRASH] sales_dialog.py:1037: `self.table.scrollToItem(self.table.item(row, 1))` — If `self.table.item(row, 1)` returns None, `scrollToItem(None)` raises `TypeError` in PySide6.

---

## FILE 3: src/ui/dialogs/purchase_order_dialog.py

[CRASH] purchase_order_dialog.py:565: `self.items_table.cellWidget(row, 2).setValue(float(item.quantity_ordered))` — `item` is a `PurchaseOrderItem`. Its `__post_init__` only converts decimal fields if `isinstance(value, (int, float, str))`. If the DB returns NULL, the field stays None. `float(None)` raises `TypeError`. Same pattern on lines 566 (`item.unit_price`), 567 (`item.discount_percentage`), 568 (`item.tax_percentage`).

[CRASH] purchase_order_dialog.py:571: `self.discount_spin.setValue(float(self.po.discount_amount))` — Same root cause: `PurchaseOrder.__post_init__` skips None values. If `discount_amount` is NULL in the DB, `float(None)` crashes. Same on lines 572 (`tax_amount`), 573 (`shipping_cost`).

[CRASH] purchase_order_dialog.py:424: `self.items_table.item(row, 1).setText(product_data["code"] or "")` — If `self.items_table.item(row, 1)` is None (cell not yet set or was cleared), `.setText()` raises `AttributeError`.

[CRASH] purchase_order_dialog.py:451-452: `self.items_table.item(row, 6).setText(...)` and `self.items_table.item(row, 7).setText(...)` — If cells at column 6 or 7 are None (e.g. during initial `_add_item` before `render_table_row` equivalent completes), `.setText()` raises `AttributeError`.

[CRASH] purchase_order_dialog.py:739: `min_stock = float(product_data.get("min_stock", 0))` — `.get()` returns 0 only if the key is **missing**. If the key exists but its value is None (DB NULL), `float(None)` crashes. Same on line 740 (`current_stock`) and line 751 (`cost_price`).

---

## FILE 4: src/ui/dialogs/product_dialog.py

**No guaranteed crashes found.** All 4 save paths (enhanced/legacy × create/update) guard against None returns from services. `collect_form_data()` reads from Qt widgets (spin boxes, text fields) which always return non-None values. `populate_form()` uses `getattr` with fallbacks for optional fields. The only risk is type mismatches if model constructors receive unexpected types, but these are caught by try/except blocks.

---

## FILE 5: src/ui/dialogs/customer_management_dialog.py

**No guaranteed crashes found.** `load_customers()` correctly guards `balance` with `or 0` (line 124). `delete_customer()` checks `if sales_result:` and `if payments_result:` before accessing dict keys. `on_search()` accesses `c["name"]` and `c["phone"]` which are always set from the query (with `or ""` fallbacks).

---

## FILE 6: src/ui/dialogs/supplier_management_dialog.py

**No guaranteed crashes found.** `delete_supplier()` uses a ternary that correctly handles None from `fetch_one`: `isinstance(count_result, dict)` guards the dict branch, and `count_result[0] if count_result else 0` guards the tuple/None branch. `load_suppliers()` uses `.get()` with empty-string fallbacks. `on_search()` follows the same safe pattern.

---

## SUMMARY

| File | Crash Count | Severity |
|------|------------|----------|
| payment_dialog.py | 2 | **CRITICAL** (line 141 blocks ALL usage) |
| sales_dialog.py | 4 | HIGH (triggered by NULL DB values) |
| purchase_order_dialog.py | 6 | HIGH (triggered by NULL DB values + missing cells) |
| product_dialog.py | 0 | — |
| customer_management_dialog.py | 0 | — |
| supplier_management_dialog.py | 0 | — |
| **TOTAL** | **12** | |

### Root Cause Pattern
The dominant crash pattern is: **dataclass `__post_init__` methods that only convert types when `isinstance(value, (int, float, str))`, leaving DB-sourced None values unconverted.** This affects Product, PurchaseOrderItem, and PurchaseOrder models. When dialog code later calls `int()`, `float()`, or uses comparison operators on these None fields, Python raises TypeError.

### Priority Fix Order
1. **payment_dialog.py:141** — Add `apply_prefill_data()` method or remove the call. Blocks all payment dialog usage.
2. **purchase_order_dialog.py:565-568, 571-573** — Guard `float()` calls with `or 0` / `or 0.0`.
3. **sales_dialog.py:995** — Guard `int()` with `or 0`.
4. **sales_dialog.py:1081** — Guard stock comparison with `or 0`.
5. **purchase_order_dialog.py:739-751** — Guard `.get()` returns against None values.
6. **Model layer** — Fix `__post_init__` in Product, PurchaseOrderItem, PurchaseOrder to convert None → default (e.g., `if value is None: value = default` before isinstance check).
--- Task ID: 3
# Crash-Point Audit - Service Layer

**Auditor:** Automated Crash-Point Audit Agent
**Date:** 2025-06-30
**Scope:** All service files (sales, payment, return, purchase_order, product_enhanced)
**Mode:** REPORT ONLY - no fixes applied

---

## 1. src/services/sales_service.py

[CRASH] sales_service.py:60: `row.get("invoice_number")` crashes with `AttributeError` if `fetch_one` returns a raw tuple instead of dict. `_generate_invoice_number` does not guard against non-dict rows.

[CRASH] sales_service.py:407: `Decimal(str(row["quantity"]))` - if any row in `_get_top_selling_products` has a NULL `quantity`, `str(None)` produces `"None"`, then `Decimal("None")` raises `InvalidOperation`. Low risk but no guard.

[CRASH] sales_service.py:437: `Decimal(str(row["total_purchases"]))` in `_get_top_customers` - if `SUM(s.final_amount)` returns None (LEFT JOIN with NULL customer_id for walk-in sales), `Decimal(str(None))` crashes. The `SUM` is missing COALESCE. **HIGH risk crash** on walk-in-only periods.

---

## 2. src/services/payment_service.py

[CRASH] payment_service.py:231-232: `sale_row["remaining_amount"]` - if `sale_row` is a raw tuple, this raises `TypeError`. The `isinstance(sale_row, dict)` check on line 233 runs AFTER the crash. **HIGH risk.**

[CRASH] payment_service.py:312,517: `self.db_manager.connection.cursor()` in fallback - if connection is None, raises `AttributeError`. **MEDIUM risk.**

[CRASH] payment_service.py:649: `Decimal(str(row.get("available_credit")))` in `get_accounts_receivable` - if `credit_limit` is NULL, `available_credit` is NULL, `Decimal(str(None))` crashes. Missing `or 0`. **HIGH risk.**

[CRASH] payment_service.py:705: Same NULL `available_credit` crash in `get_accounts_payable`. **HIGH risk.**

[CRASH] payment_service.py:652,709: `date.fromisoformat(row.get("last_payment_date"))` - if value is a datetime string with time component, raises `ValueError`. **MEDIUM risk.**

[CRASH] payment_service.py:889-890: `Decimal(str(row.get("total_amount")))` in `get_payment_summary` - if `SUM(amount_in_base_currency)` returns None (empty period), `str(None)` = `"None"`, crashes. **MEDIUM risk.**

[CRASH] payment_service.py:1087: `Decimal(str(row["daily_amount"]))` in `get_cash_flow_report` - same NULL aggregate risk. **MEDIUM risk.**

[CRASH] payment_service.py:1179-1183: `Decimal(str(row["avg_amount"]))` and `min_amount`/`max_amount` in `get_payment_trends_analysis` - if AVG/MIN/MAX returns None (single row with NULL values), crashes. **MEDIUM risk.**

[CRASH] payment_service.py:1364: `Decimal(str(row.get("avg_amount", 0)))` in `get_period_comparison_analysis` - `.get(key, default)` returns None if the key exists with value NULL. Then `Decimal(str(None))` crashes. **HIGH risk.**

[CRASH] payment_service.py:1593-1596: Same NULL aggregate `.get(key, default)` pattern in `get_payment_performance_kpis` - `avg_amount`, `min_amount`, `max_amount` all vulnerable. **HIGH risk.**

**Verification: English-value fix is CORRECT.** All 6 report methods use `status = 'completed'` and classify by `payment_type` values `'customer_payment'`/`'supplier_payment'` (lines 902-904, 1097-1102, 1191-1194). No Arabic-value crash paths remain.

---

## 3. src/services/return_service.py

[CRASH] return_service.py:93-117: `create_return` INSERT does NOT include the `return_number` column, even though it is generated at line 80. If the schema has `return_number` as NOT NULL, crashes with `IntegrityError`. **HIGH risk.**

[CRASH] return_service.py:148,269: `self.db.connection.rollback()` - if connection is None, crashes with `AttributeError`. **MEDIUM risk.**

[CRASH] return_service.py:303-317: `get_all_returns` filters by `return_type`, `customer_id`, `supplier_id` columns that do NOT exist in the current schema. If any caller passes these filters, the SQL crashes. Caught by try/except, returns []. **MEDIUM risk (silent data loss).**

[CRASH] return_service.py:479-524: `get_return_statistics` queries reference non-existent columns (`return_type`, `return_reason`, `refund_amount`). Caught by try/except, returns {}. **MEDIUM risk (silent failure).**

---

## 4. src/services/purchase_order_service.py

[CRASH] purchase_order_service.py:68-70: `result[0].get("po_number")` in `generate_po_number` - if `execute_query` returns tuples, `.get()` crashes. **MEDIUM risk.**

[CRASH] purchase_order_service.py:661: Same tuple-vs-dict risk in `_generate_receiving_number`. **MEDIUM risk.**

[CRASH] purchase_order_service.py:964: `max(po_amount, received_amount, invoice_amount, 1.0)` in `three_way_match` - if `po.total_amount` is None, `max()` crashes with `TypeError`. **HIGH risk.**

[CRASH] purchase_order_service.py:670-673,777-780: Manual `BEGIN TRANSACTION`/`COMMIT`/`ROLLBACK` pattern. If `execute_update` auto-commits (SQLite default), the rollback is useless and receiving notes are left orphaned after partial failure. **Data integrity risk.**

---

## 5. src/services/product_service_enhanced.py

[CRASH] product_service_enhanced.py:83: `existing_cols = [row.get('name', '') for row in cols_info]` in `create_product` - if PRAGMA `fetch_all` returns tuples, `row.get()` crashes. **HIGH risk** (7 locations: lines 83, 251, 315, 396, 470, 747, 794).

[CRASH] product_service_enhanced.py:99: `self.db_manager.execute_insert(query, ...)` return value assumed to be int. If it returns a cursor or None, downstream code using `product.id` as integer crashes. **MEDIUM risk.**

[CRASH] product_service_enhanced.py:517-521: `get_featured_products` hardcodes `reserved_stock` in SELECT without checking schema. Unlike `get_low_stock_products` and `get_products_requiring_reorder` which check for the column, this method does NOT. Crashes with `OperationalError` if column missing. **HIGH risk.**

---

## Summary Table

| # | File:Line | Crash | Severity |
|---|-----------|-------|----------|
| 1 | payment_service.py:231-232 | Dict access on tuple row before isinstance check | HIGH |
| 2 | payment_service.py:649,705 | Decimal(str(None)) from NULL credit_limit | HIGH |
| 3 | payment_service.py:889-890 | Decimal(str(None)) from NULL SUM aggregate | MEDIUM |
| 4 | payment_service.py:1364 | .get(key,default) returns None when key exists with NULL value | HIGH |
| 5 | payment_service.py:1593-1596 | Same NULL aggregate .get pattern in KPIs | HIGH |
| 6 | product_service_enhanced.py:83,251,315,396,470,747,794 | PRAGMA row.get() crashes on tuple rows (7 locations) | HIGH |
| 7 | product_service_enhanced.py:517-521 | get_featured_products hardcodes reserved_stock without schema check | HIGH |
| 8 | purchase_order_service.py:964 | max() with None from po.total_amount in three_way_match | HIGH |
| 9 | sales_service.py:437 | SUM() can be NULL for walk-in sales (missing COALESCE) | HIGH |
| 10 | return_service.py:93-117 | return_number generated but not inserted; NOT NULL crash | HIGH |
| 11 | payment_service.py:312,517 | connection.cursor() when connection is None | MEDIUM |
| 12 | payment_service.py:652,709 | date.fromisoformat on non-ISO date strings | MEDIUM |
| 13 | purchase_order_service.py:68-70,661 | .get() on tuple rows in number generators | MEDIUM |
| 14 | product_service_enhanced.py:99 | execute_insert return type assumed int | MEDIUM |
| 15 | return_service.py:479-524 | Statistics query references non-existent columns | MEDIUM |

## Next Actions (Priority Order)

1. Add `COALESCE` to all SUM/AVG/MIN/MAX aggregates in payment_service.py.
2. Replace `Decimal(str(row.get("x", 0)))` with `Decimal(str(row.get("x") or 0))` throughout payment_service.py.
3. Guard PRAGMA parsing: use `row.get('name','') if isinstance(row,dict) else row[1]` at 7 locations in product_service_enhanced.py.
4. Add reserved_stock column check to `get_featured_products` in product_service_enhanced.py.
5. Include `return_number` in INSERT in return_service.py `create_return`.
6. Guard `max()` in purchase_order_service.py `three_way_match` against None values.
7. Fix `sale_row["remaining_amount"]` access pattern in payment_service.py lines 231-232.
8. Add COALESCE to `_get_top_customers` in sales_service.py line 423.

--- Task ID: 4

# Crash-Point Audit — All Model Files

**Scope:** payment.py, sale.py, customer.py, supplier.py, product.py, return_invoice.py  
**Root cause pattern:** `dict.get('key', default)` returns `None` (NOT `default`) when the key **exists** with a SQL NULL value. Code then passes `None` to `Decimal(str(...))` or `float(...)` which raises `InvalidOperation` / `TypeError`.  
**Note:** Crashes inside try/except are tagged [CRASH-SILENT] — the exception is swallowed, the function returns `None`/`[]`, and the caller receives no object. This causes downstream `None`-dereference crashes or silent data loss.

---

## 1. src/models/payment.py

**_row_to_payment (line 691):** isinstance guard is **correct** — routes `dict` → `_row_to_payment_dict`, everything else → tuple fallback. The tuple fallback uses `safe_decimal(idx)` and `safe_date_at(idx)` which explicitly check `row[idx] is not None`. **Verified OK.**

**_row_to_payment_dict (line 764):** Uses `safe_decimal(value)` (checks `if value is None: return None`) followed by `or Decimal("0")`. This pattern is **safe** — `None or Decimal("0")` evaluates to `Decimal("0")`. Lines 801, 803, 804 are all safe.

[DATA-CORRUPTION] payment.py:802 — `row_dict.get("currency", "DZD")` when DB NULL → returns `None` (not `"DZD"`). Sets `currency=None` on the Payment object. Not a direct crash, but downstream code calling `.upper()` or string ops on `currency` will crash.

[DATA-CORRUPTION] payment.py:797-800 — Same `.get(key, default)` pattern for `payment_number`, `payment_type`, `payment_method`, `status`. NULL in any of these → field set to `None` instead of the intended default.

[DATA-CORRUPTION] payment.py:808 — `safe_date(row_dict.get("payment_date"))` returns `None` for NULL. `payment_date` field has no `or` fallback, so it stays `None`. `__post_init__` does not reset it. Downstream `.isoformat()` calls will crash.

**create_payment (line 250):** Well-defended with `safe_float()`, try-except, and fallback value_map. **No direct crash.**

---

## 2. src/models/sale.py — HIGHEST CRASH DENSITY

**_row_to_sale (line 1090):** The `gv(k, i, d)` helper uses `row.get(k, d)` for dicts. When key exists with NULL, returns `None` (not `d`). The second branch `hasattr(row, "keys")` (for sqlite3.Row) does `row[k]` which also returns `None` on NULL without falling back to `d`.

[CRASH] sale.py:1117-1118 — `Decimal(str(gv("total_amount", 3, 0)))` → NULL → `Decimal(str(None))` → `decimal.InvalidOperation`
[CRASH] sale.py:1120-1121 — `Decimal(str(gv("discount_amount", 4, 0)))` → same
[CRASH] sale.py:1123-1124 — `Decimal(str(gv("discount_percentage", 18, 0)))` → same
[CRASH] sale.py:1126-1127 — `Decimal(str(gv("tax_amount", 19, 0)))` → same
[CRASH] sale.py:1129-1130 — `Decimal(str(gv("tax_percentage", 20, 0)))` → same
[CRASH] sale.py:1132-1133 — `Decimal(str(gv("final_amount", 5, 0)))` → same
[CRASH] sale.py:1135-1136 — `Decimal(str(gv("paid_amount", 21, 0)))` → same
[CRASH] sale.py:1138-1139 — `Decimal(str(gv("remaining_amount", 22, 0)))` → same
[CRASH] sale.py:1148-1149 — `Decimal(str(gv("exchange_rate", 24, 1.0)))` → same

**else-branch (row_len < 25, line 1163):**
[CRASH] sale.py:1173-1174 — `Decimal(str(gv("total_amount", 3, 0)))` → same NULL pattern
[CRASH] sale.py:1176-1177 — `Decimal(str(gv("discount_amount", 4, 0)))` → same
[CRASH] sale.py:1179-1180 — `Decimal(str(gv("final_amount", 5, 0)))` → same
[CRASH] sale.py:1192-1193 — `Decimal(str(gv("paid_amount", paid_idx, 0)))` → same
[CRASH] sale.py:1195-1196 — `Decimal(str(gv("remaining_amount", remaining_idx, 0)))` → same

**Protected (correct pattern):** sale.py:1157-1160 — `subtotal` uses `if gv(...) is not None else None` guard. **Safe.**

**_row_to_sale_item (line 1222):**
[CRASH] sale.py:1239 — `float(gv("quantity", 4, 0))` → NULL → `float(None)` → `TypeError`
[CRASH] sale.py:1240 — `Decimal(str(gv("unit_price", 5, 0)))` → NULL → `decimal.InvalidOperation`
[CRASH] sale.py:1241 — `Decimal(str(gv("total_price", 6, 0)))` → same
[CRASH] sale.py:1242 — `Decimal(str(gv("cost_price", 7, 0)))` → same
[CRASH] sale.py:1243 — `Decimal(str(gv("profit", 8, 0)))` → same
[CRASH] sale.py:1244 — `Decimal(str(gv("discount", 10, 0)))` → same
[CRASH] sale.py:1245 — `Decimal(str(gv("tax_amount", 11, 0)))` → same

**_row_to_sale_dict (line 1566):**
[CRASH] sale.py:1580-1581 — `float(Decimal(str(gv("total_amount", 3, 0))))` → NULL → `decimal.InvalidOperation`

**_create_sale_item (line 689):**
[CRASH-SILENT] sale.py:699 — `Decimal(str(cost_row.get("cost_price", 0)))` → if `cost_price` is NULL in products table, `cost_row.get("cost_price", 0)` returns `None` → `Decimal(str(None))` → `InvalidOperation`. Caught by except, returns `None`. Caller gets `None` for the sale item ID — silent data loss.

**_create_sale_item_in_transaction (line 763):**
[CRASH-SILENT] sale.py:776 — `Decimal(str(cost_row[0]))` → if `cost_price` is NULL, `cost_row[0]` is `None` → `Decimal(str(None))` → `InvalidOperation`. Caught by except, returns `None`.

**update_sale / _do_update_sale (lines 1297, 1431):**
[CRASH-SILENT] sale.py:1369,1370,1371,1372,1373,1374,1375,1376,1391 — `float(sale.total_amount)` etc. If `sale` object was constructed with None Decimal fields (unlikely given _row_to_sale would crash first), these would raise `TypeError`. Currently protected by the fact that _row_to_sale crashes before creating the object, but if a Sale is manually constructed with None values, these lines crash.
[CRASH-SILENT] sale.py:1456-1463,1478 — Same pattern in `_do_update_sale`.

---

## 3. src/models/customer.py

**_row_to_customer (line 785):** `get_val(key, idx, default)` uses `row.get(key, default)` — same NULL-trap.

[CRASH-SILENT] customer.py:808 — `Decimal(str(get_val("credit_limit", 10, 0)))` → NULL → `Decimal(str(None))` → `InvalidOperation`. Caught by except at line 836, returns `None`. Entire Customer object is lost.
[CRASH-SILENT] customer.py:809 — `Decimal(str(get_val("current_balance", 11, 0)))` → same pattern.

**Protected (correct `or` pattern):**
- customer.py:833 — `Decimal(str(get_val("total_purchases", 29) or 0))` — `None or 0` → `0`. **Safe.**
- customer.py:834 — `int(get_val("purchases_count", 30) or 0)` — **Safe.**
- customer.py:819 — `Decimal(str(get_val(...) or 0))` — **Safe.**

**create_customer (line 352):**
[CRASH-SILENT] customer.py:364 — `float(customer.credit_limit)` — if credit_limit is `None` (possible if Customer was constructed with explicit None), crashes. Wrapped in try-except.
[CRASH-SILENT] customer.py:365 — `float(customer.current_balance)` — same.

**update_balance (line 596):** Atomic SQL. Takes `float` parameter, not from DB row. **Safe.**

---

## 4. src/models/supplier.py

**_row_to_supplier (line 541):**

**Tuple path (line 549):** Uses `or 0` pattern. **Safe:**
- supplier.py:562 — `Decimal(str(row[11] or 0))` — **Safe.**
- supplier.py:563 — `Decimal(str(row[12] or 0))` — **Safe.**
- supplier.py:568 — `Decimal(str(row[14] or 0))` — **Safe.**
- supplier.py:569 — `int(row[15] or 0)` — **Safe.**

**Dict path (line 579):**
[CRASH-SILENT] supplier.py:594 — `Decimal(str(get_val("credit_limit", 14, 0)))` → NULL → `Decimal(str(None))` → `InvalidOperation`. Caught by except at line 606, returns `None`.
[CRASH-SILENT] supplier.py:595 — `Decimal(str(get_val("current_balance", 15, 0)))` → same.

**Protected:** supplier.py:603 — `Decimal(str(get_val("total_purchases", 22) or 0))` — **Safe.**

**create_supplier (line 233):**
[CRASH-SILENT] supplier.py:262 — `float(supplier.credit_limit)` — if None, crashes. try-except.
[CRASH-SILENT] supplier.py:263 — `float(supplier.current_balance)` — same.

**update_supplier_balance (line 421):** Atomic SQL. **Safe.**

---

## 5. src/models/product.py

**_row_to_product (line 436):**

[CRASH-SILENT] product.py:455 — `Decimal(str(get_val("cost_price", 6, 0)))` → NULL → `Decimal(str(None))` → `InvalidOperation`. Caught by except at line 470, returns `None`.
[CRASH-SILENT] product.py:456 — `Decimal(str(get_val("selling_price", 7, 0)))` → same.
[CRASH-SILENT] product.py:457 — `Decimal(str(get_val("wholesale_price", 8, 0)))` → same.
[CRASH-SILENT] product.py:458 — `Decimal(str(get_val("vip_price", 9, 0)))` → same.
[CRASH-SILENT] product.py:461 — `float(get_val("current_stock", 12, 0))` → NULL → `float(None)` → `TypeError`. Same except block.

**create_product (line 162):**
[CRASH-SILENT] product.py:187 — `float(product.cost_price)` — if None, crashes. try-except.
[CRASH-SILENT] product.py:188 — `float(product.selling_price)` — same.
[CRASH-SILENT] product.py:189 — `float(product.wholesale_price)` — same.
[CRASH-SILENT] product.py:190 — `float(product.vip_price)` — same.
[CRASH-SILENT] product.py:193 — `float(product.current_stock)` — same.

---

## 6. src/models/return_invoice.py

**No `_row_to_return` function exists.** The ReturnManager returns raw dicts from `list_returns()` (line 529). The `from_dict` class methods pass values through to `__post_init__` which only converts `isinstance(value, (int, float, str))` — None values pass through unconverted.

[DATA-CORRUPTION] return_invoice.py:234-235 — `__post_init__` skips None values for Decimal fields. If `from_dict` receives a dict with NULL from DB, fields like `total_amount` remain `None`. Later `to_dict()` at line 407 calls `float(self.total_amount)` → `TypeError`.

[CRASH] return_invoice.py:134-139 — `ReturnItem.to_dict()`: `float(self.quantity_returned)`, `float(self.unit_price)`, etc. If any field is `None`, crashes.

[CRASH] return_invoice.py:407-418 — `ReturnInvoice.to_dict()`: `float(self.subtotal)`, `float(self.discount_amount)`, `float(self.total_amount)`, `float(self.refund_amount)`, `float(self.credit_note_amount)`. If any is `None`, crashes.

---

## Summary

| File | Direct [CRASH] | Silent [CRASH-SILENT] | Data Corruption | Root Cause |
|------|----------------|----------------------|-----------------|-------------|
| payment.py | 0 | 0 | 4 | `.get(key, default)` returns None on NULL |
| sale.py | **16** | 3 | 0 | `gv()` / `Decimal(str(None))` / `float(None)` |
| customer.py | 0 | 4 | 0 | `get_val()` / `Decimal(str(None))` |
| supplier.py | 0 | 2 | 0 | `get_val()` / `Decimal(str(None))` |
| product.py | 0 | 10 | 0 | `get_val()` / `Decimal(str(None))` / `float(None)` |
| return_invoice.py | 2 | 0 | 1 | `to_dict()` / `float(None)` on None fields |
| **TOTAL** | **18** | **19** | **5** | |

## Fix Pattern

The universal fix for the `gv`/`get_val` NULL problem:
```python
# BROKEN — default is ignored when key exists with NULL:
Decimal(str(gv("amount", 3, 0)))

# FIX OPTION A — `or` fallback (None coalescing):
Decimal(str(gv("amount", 3, 0) or 0))

# FIX OPTION B — safe helper like payment.py:
def safe_decimal(value):
    if value is None:
        return Decimal("0")
    return Decimal(str(value))

# FIX OPTION C — COALESCE in SQL:
SELECT COALESCE(amount, 0) as amount FROM sales
```

--- Task ID: 5a

## Fix NULL-Handling Crashes in Model _row_to_* Methods

**Date:** 2025-07-01
**Scope:** 5 model files — sale.py, return_invoice.py, product.py, customer.py, supplier.py

### Root Cause
`dict.get('key', default)` returns `None` (not `default`!) when the key exists with a SQL NULL value. When `None` reaches `Decimal(str(None))` it raises `InvalidOperation`; when it reaches `float(None)` or `int(None)` it raises `TypeError`.

### Changes Made

#### 1. `src/models/sale.py` — 3 `gv()` helper functions fixed
- **`_row_to_sale` gv (line ~1094):** Changed `row.get(k, d)` → `row.get(k, d) or d` for dict path; added `val if val is not None else d` for tuple/keys paths. Covers 16 Decimal/float conversion sites.
- **`_row_to_sale_item` gv (line ~1231):** Same `or d` / `is not None` pattern.
- **`_row_to_sale_dict` gv (line ~1574):** Same pattern.

#### 2. `src/models/return_invoice.py` — float(None) in to_dict() + __post_init__
- **ReturnItem.to_dict():** Added `or 0` to all 6 `float(self.*)` calls (quantity_returned, quantity_original, unit_price, discount_amount, tax_amount, total_amount).
- **ReturnInvoice.to_dict():** Added `or 0` to all 6 `float(self.*)` calls (subtotal, discount_amount, tax_amount, total_amount, refund_amount, credit_note_amount).
- **ReturnItem.__post_init__:** Added `if value is None: setattr(..., Decimal("0"))` before the isinstance check.
- **ReturnInvoice.__post_init__:** Same None guard for decimal_fields loop.

#### 3. `src/models/product.py` — _row_to_product + __post_init__
- **get_val helper:** Changed `row.get(key, default)` → `row.get(key, default) or default`; added `val if val is not None else default` for tuple path.
- **Product.__post_init__:** Added `if value is None: setattr(..., Decimal("0.00"))` and `if self.current_stock is None: self.current_stock = 0.0`.

#### 4. `src/models/customer.py` — _row_to_customer + to_dict()
- **get_val helper:** Same `or default` / `is not None` pattern.
- **Customer.to_dict():** Added `or 0` to 4 float() calls (credit_limit, current_balance, total_purchases, available_credit).

#### 5. `src/models/supplier.py` — _row_to_supplier + __post_init__ + to_dict()
- **get_val helper:** Same `or default` / `is not None` pattern.
- **Supplier.__post_init__:** Added `if value is None: setattr(..., Decimal("0.00"))` guard.
- **Supplier.to_dict():** Added `or 0` to 4 float() calls (credit_limit, current_balance, total_purchases, available_credit).

### Verification
All 5 files pass `ast.parse()` — syntax is valid.

--- Task ID: 5b: Fix crash points in dialog files ---
Date: 2026-09-01

## payment_dialog.py
- **L141**: Created `apply_prefill_data()` method (was missing, causing AttributeError). Method safely sets entity_combo index and amount_spinbox from `prefill_entity_id`/`prefill_amount` with best-effort try/except.
- **L530**: `rem` (remaining_amount) from DB could be None → `{rem:.2f}` crash. Fixed: `{rem or 0:,.2f}`.

## sales_dialog.py
- **L887**: `float(product.selling_price)` → `float(product.selling_price or 0)` — ORM field can be NULL.
- **L995**: `int(product_data["current_stock"])` → `int(product_data.get("current_stock") or 0)` — DB NULL crashes int().
- **L1037**: `scrollToItem(self.table.item(row,1))` on None cell → added `_scroll_item` None guard.
- **L1081**: `if item["stock"] <= 0` when stock is None → `if (item["stock"] or 0) <= 0`.
- **L1187**: `self.table.item(row,4).setText(...)` on None → added `_qty_cell` None guard.
- **L1198**: `self.table.item(row,5).setText(...)` on None → added `_price_cell` None guard.

## purchase_order_dialog.py
- **L424**: `self.items_table.item(row,1).setText(...)` on None → added `_code_cell` None guard.
- **L451-452**: `self.items_table.item(row,6/7).setText(...)` on None → added `_subtotal_cell`/`_net_cell` None guards.
- **L565-568**: `float(item.quantity_ordered/unit_price/discount_percentage/tax_percentage)` → added `or 0` to all 4.
- **L571-573**: `float(self.po.discount_amount/tax_amount/shipping_cost)` → added `or 0` to all 3.
- **L739-740**: `float(product_data.get("min_stock/current_stock", 0))` → changed to `or 0` (handles explicit None from DB).
- **L751**: `float(product_data.get("cost_price", 0))` → changed to `or 0`.

Total fixes: 18 crash points addressed across 3 files.

--- Task ID: 5c

**Fix crash points in service files: NULL aggregates, div-by-zero, missing columns**

### payment_service.py (20 fixes)
- **L231-235**: `sale_row["remaining_amount"]` could be NULL → added `or 0` before `Decimal(str(...))`.
- **L649**: `Decimal(str(row.get("available_credit")))` → added `or 0` to prevent `Decimal(str(None))`.
- **L705**: Same fix for `available_credit` in `get_accounts_payable`.
- **L833-834**: `Decimal(str(r.get("amount"/"paid_amount")))` → added `or 0`.
- **L890**: `Decimal(str(row.get("total_amount")))` → added `or 0`.
- **L1087**: `Decimal(str(row["daily_amount"]))` → added `or 0`.
- **L1180-1183**: All 4 aggregates in trends report (`total_amount`, `avg_amount`, `min_amount`, `max_amount`) → added `or 0`.
- **L1253**: `Decimal(str(row["monthly_amount"]))` → added `or 0`.
- **L1364-1365**: Changed `.get("key", 0)` to `.get("key") or 0` (default is bypassed when key exists with NULL).
- **L1593-1596**: Same pattern fix for all 4 aggregates in KPI report.

### sales_service.py (3 fixes)
- **L391-392**: `SUM(si.quantity)` and `SUM(si.total_price)` → wrapped in `COALESCE(..., 0)`.
- **L423**: `SUM(s.final_amount) AS total_purchases` → wrapped in `COALESCE(..., 0)`.
- **L437**: `Decimal(str(row["total_purchases"]))` → added `or 0` as defense-in-depth.

### purchase_order_service.py (4 fixes)
- **L68**: Added `isinstance(result[0], dict)` guard before `.get("po_number")` for tuple-row safety.
- **L659**: Same `isinstance` guard for `.get("receiving_number")`.
- **L931**: `float(po.total_amount)` → `float(po.total_amount or 0)` to handle NULL.
- **L964**: `max(po_amount, received_amount, invoice_amount, 1.0)` → filtered None values first: `max([a for a in (...) if a is not None]) if amounts else 1.0`.

### return_service.py + database_manager.py (3 fixes)
- **return_service.py L100-103**: Added `return_number` to INSERT columns and values (was generated but never inserted).
- **database_manager.py L751**: Added `return_number TEXT UNIQUE` column to `return_invoices` CREATE TABLE.
- **database_manager.py L763-770**: Added ALTER TABLE migration to add `return_number` column for existing databases.

### product_service_enhanced.py (8 fixes)
- **New helper `_get_pragma_columns(table)`**: Safely extracts column names from PRAGMA table_info, handling both dict and tuple row formats.
- **L82-83, L250-251**: Replaced manual `row.get('name', '')` PRAGMA parsing with `_get_pragma_columns()`.
- **L314-315, L395-396, L469-470, L746-747, L793-794**: Replaced all 5 remaining PRAGMA patterns with helper call.
- **L527-551 (`get_featured_products`)**: Wrapped hardcoded `reserved_stock` column in SELECT with schema check (`_get_pragma_columns`) to avoid crash when column doesn't exist.

Total: 38 crash points addressed across 6 files.

--- Task ID: 5d
**Scope:** Crash points in main_window.py and login_dialog.py
**Date:** 2025-07-01

### main_window.py (7 fixes)

1. **L5231 – `import pandas as pd` outside try/except in `_on_sales_data_loaded`**
   - Moved `import pandas as pd` inside the existing `try:` block. Previously, if pandas was not installed, the `ImportError` would propagate uncaught before reaching the `try` guard.

2. **L5478-5480 – `purchase.get('total_amount', 0)` returns `None` when DB column is NULL**
   - Changed `purchase.get('total_amount', 0)` → `purchase.get('total_amount') or 0` (and same for `paid_amount`, `remaining_amount`). The `.get()` default only fires when the key is absent; a key present with `None` value passes through and crashes `f"{None:,.2f}"`.
   - Also fixed identical pattern at **L5752/5754** (`r.get("balance", 0)` in float() sum) and **L5881/5886** (`row.get("amount", row.get("total", 0))` in float()).

3. **L2755 – `top_insight['message']` KeyError short-circuits dashboard**
   - Changed `top_insight["message"]` → `top_insight.get("message", "")` so a missing key shows empty text instead of crashing.

4. **L2746-2749 – `AIPredictionService` instantiated every dashboard refresh, failure kills dashboard**
   - Wrapped the `AIPredictionService(self.db_manager)` + `get_proactive_insights()` in its own `try/except`. On failure, `insights` defaults to `[]` so the dashboard renders normally.

5. **L9733 – Typo `'%H:%Mf'` in strftime**
   - Changed to `'%H:%M:%S'`. The `f` after `M` was a typo (not a valid directive); it would raise `ValueError` on every statusbar refresh.

6. **L612, L626 – `self.logger` used inside `except` but may be `None`**
   - Added `if self.logger:` guard before `.debug(...)` calls in two `except` blocks during `__init__`.

### login_dialog.py (1 fix)

7. **L221 – `SecurityService(user_service.db)` crashes in standalone test**
   - Wrapped in `try/except`; sets `self.security_service = None` on failure so the dialog still loads.

**Verification:** Both files pass `python -m py_compile` cleanly.
