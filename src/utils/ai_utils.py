import copy
from collections import defaultdict
from typing import Any, Dict, List


def aggregate_daily_sales(sales_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """تجميع المبيعات يومياً"""
    daily_totals = defaultdict(float)
    for sale in sales_data:
        date_str = str(sale.get("sale_date", "")).split(" ")[0]
        if date_str:
            daily_totals[date_str] += float(sale.get("total_amount", 0.0))
    return dict(daily_totals)


def substitute_variables(params: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
    """استبدال المتغيرات في المعلمات"""
    params_copy = copy.deepcopy(params)

    def _replace_in_value(value):
        if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
            var_name = value[2:-2].strip()
            return variables.get(var_name, value)
        elif isinstance(value, dict):
            for k, v in value.items():
                value[k] = _replace_in_value(v)
            return value
        elif isinstance(value, list):
            return [_replace_in_value(item) for item in value]
        return value

    for k, v in params_copy.items():
        params_copy[k] = _replace_in_value(v)

    return params_copy
