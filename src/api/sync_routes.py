from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException

from src.api.routes import get_current_user, get_db_manager
from src.core.database_manager import DatabaseManager

sync_router = APIRouter(tags=["Sync"])


@sync_router.get("/handshake")
async def handshake(last_synced: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """
    Returns the current server time to synchronize clocks.
    """
    return {"server_time": datetime.now().isoformat(), "status": "ready"}


@sync_router.get("/delta")
async def get_delta(
    last_synced: str,
    db_manager: DatabaseManager = Depends(get_db_manager),
    current_user: dict = Depends(get_current_user),
):
    """
    Returns records changed since `last_synced`.
    Focuses on critical tables: products, customers, sales.
    """
    try:
        since_dt = datetime.fromisoformat(last_synced)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format")

    changes = {"items": []}

    tables = ["products", "customers", "sales"]

    for table in tables:
        # Construct query carefully to prevent SQL injection (table names are hardcoded above)
        query = f"SELECT * FROM {table} WHERE updated_at > ? OR created_at > ?"
        rows = db_manager.fetch_all(query, (since_dt, since_dt))

        # Helper to convert Row to dict
        columns = []  # noqa: F841
        if rows:
            # Basic column recovery if Row object supports keys or similar,
            # otherwise we might need descriptions.
            # Assuming db_manager.fetch_all returns sqlite3.Row-like or list of tuples.
            # For robustness with our DatabaseManager, let's look at `fetch_all`.
            # It returns list of tuples usually if using sqlite3 directly without row_factory,
            # or Row objects if configured.
            # Let's try to get columns using Pragma or similar if needed,
            # but DatabaseManager usually handles connections.
            # Let's assume we map explicitly or use a helper.
            # For MVP integration using existing patterns is safest.
            pass

        # For now, let's assume direct dict conversion isn't trivial without column names.
        # We can use a simpler approach: get column names first for the table.
        col_query = f"PRAGMA table_info({table})"
        col_info = db_manager.fetch_all(col_query)
        col_names = [c[1] for c in col_info]  # index 1 is name

        for row in rows:
            # Map row values to column names
            row_dict = dict(zip(col_names, row))
            changes["items"].append({"table_name": table, "data": row_dict})

    return changes


@sync_router.post("/push")
async def push_changes(
    payload: Dict[str, Any] = Body(...),
    db_manager: DatabaseManager = Depends(get_db_manager),
    current_user: dict = Depends(get_current_user),
):
    """
    Receives a batch of changes from the client and applies them.
    Expected payload: {"table_name": "...", "items": [...]}
    """
    table_name = payload.get("table_name")
    items = payload.get("items", [])

    if table_name not in ["products", "customers", "sales"]:
        raise HTTPException(status_code=400, detail=f"Table {table_name} not supported for push")

    # Get column names for validation/construction
    col_query = f"PRAGMA table_info({table_name})"
    col_info = db_manager.fetch_all(col_query)
    valid_columns = {c[1] for c in col_info}

    acknowledged_ids = []

    for item in items:
        # Remove 'id' if present to avoid PK conflicts on insert?
        # Or use it for UPDATE.
        # Strategy: Upsert based on ID if present, else Insert.
        # But mobile often generates temporary IDs.
        # For this phase, we assume the backend is the source of truth for IDs
        # OR mobile sends IDs if they match backend IDs (updates).

        record_id = item.get("id")

        # Clean item keys
        clean_item = {k: v for k, v in item.items() if k in valid_columns}
        clean_item["updated_at"] = datetime.now()  # Force server timestamp

        if record_id:
            # Try UPDATE
            set_clause = ", ".join([f"{k} = ?" for k in clean_item.keys() if k != "id"])
            values = [clean_item[k] for k in clean_item.keys() if k != "id"]
            values.append(record_id)

            query = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"
            db_manager.execute_non_query(query, tuple(values))
            acknowledged_ids.append(record_id)
        else:
            # INSERT
            # Remove id from insert if it's None to let DB autoincrement
            if "id" in clean_item:
                del clean_item["id"]

            clean_item["created_at"] = datetime.now()

            cols = ", ".join(clean_item.keys())
            placeholders = ", ".join(["?"] * len(clean_item))
            values = list(clean_item.values())

            query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
            new_id = db_manager.execute_insert(query, tuple(values))
            if new_id:
                acknowledged_ids.append(new_id)  # Note: Client needs to handle ID mapping if it sent temp ID

    return {"acknowledged_ids": acknowledged_ids}
