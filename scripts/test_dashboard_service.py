#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import date, timedelta
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.database_manager import DatabaseManager
from src.services.dashboard_service import DashboardService


def main():
    db = DatabaseManager()
    db.initialize()

    svc = DashboardService(db)
    end = date.today()
    start = end - timedelta(days=6)

    data = svc.load_dashboard(start, end)

    # Prepare a simple serializable summary
    out = {
        'period': [str(start), str(end)],
        'kpis_count': len(data.kpis),
        'sales_series_points': len(data.sales_series[0].points) if data.sales_series else 0,
        'top_products_count': len(data.top_products),
        'active_customers': data.active_customers,
        'active_suppliers': data.active_suppliers,
    }

    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
