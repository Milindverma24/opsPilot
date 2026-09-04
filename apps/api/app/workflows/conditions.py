"""
Safe Condition Evaluator — Phase 9.

Evaluates deterministic workflow branching conditions WITHOUT eval() or arbitrary Python execution.
Supports structured condition trees and path navigation into context/data dictionaries.

Supported Operators:
- ==, !=, >, >=, <, <=
- IN, NOT_IN
- EXISTS
- AND, OR
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Union


def resolve_path(data: Dict[str, Any], path: str) -> Any:
    """
    Safely resolve a dotted or nested path in data.
    e.g. 'order.total', 'steps.1.output.amount', 'context.customer.is_eligible'
    """
    if not path or not isinstance(data, dict):
        return None

    parts = path.split(".")
    current = data

    for part in parts:
        if current is None:
            return None
        if isinstance(current, dict):
            if part in current:
                current = current[part]
            else:
                # Try integer key or case-insensitive
                found = False
                for k, v in current.items():
                    if str(k) == part:
                        current = v
                        found = True
                        break
                if not found:
                    return None
        elif isinstance(current, (list, tuple)):
            try:
                idx = int(part)
                if 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return None
            except ValueError:
                return None
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            return None

    return current


def _coerce_type(val: Any, target_val: Any) -> tuple[Any, Any]:
    """Coerce types for numeric and boolean comparison."""
    if val is None or target_val is None:
        return val, target_val

    # Boolean coercion
    if isinstance(target_val, bool):
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes"), target_val
        return bool(val), target_val
    if isinstance(val, bool):
        if isinstance(target_val, str):
            return val, target_val.lower() in ("true", "1", "yes")
        return val, bool(target_val)

    # Number coercion
    if isinstance(target_val, (int, float)):
        try:
            return float(val), float(target_val)
        except (ValueError, TypeError):
            return val, target_val
    if isinstance(val, (int, float)):
        try:
            return float(val), float(target_val)
        except (ValueError, TypeError):
            return val, target_val

    # String comparison
    if isinstance(val, str) and isinstance(target_val, str):
        return val.strip().lower(), target_val.strip().lower()
    return str(val), str(target_val)


def evaluate_atomic_condition(actual: Any, operator: str, expected: Any) -> bool:
    """Evaluate a single atomic comparison operator."""
    op = operator.upper().strip()

    if op == "EXISTS":
        return actual is not None

    if op in ("==", "EQ"):
        a, b = _coerce_type(actual, expected)
        return a == b

    if op in ("!=", "NEQ"):
        a, b = _coerce_type(actual, expected)
        return a != b

    # Numeric comparisons
    if op in (">", "GT"):
        a, b = _coerce_type(actual, expected)
        if a is None or b is None:
            return False
        try:
            return float(a) > float(b)
        except (ValueError, TypeError):
            return False

    if op in (">=", "GTE"):
        a, b = _coerce_type(actual, expected)
        if a is None or b is None:
            return False
        try:
            return float(a) >= float(b)
        except (ValueError, TypeError):
            return False

    if op in ("<", "LT"):
        a, b = _coerce_type(actual, expected)
        if a is None or b is None:
            return False
        try:
            return float(a) < float(b)
        except (ValueError, TypeError):
            return False

    if op in ("<=", "LTE"):
        a, b = _coerce_type(actual, expected)
        if a is None or b is None:
            return False
        try:
            return float(a) <= float(b)
        except (ValueError, TypeError):
            return False

    # Collection membership
    if op == "IN":
        if isinstance(expected, (list, tuple, set)):
            return actual in expected or any(evaluate_atomic_condition(actual, "==", item) for item in expected)
        if isinstance(expected, str):
            return str(actual) in expected
        return False

    if op in ("NOT_IN", "NOT IN"):
        return not evaluate_atomic_condition(actual, "IN", expected)

    return False


def _parse_expression_string(expr_str: str) -> Optional[Dict[str, Any]]:
    """
    Safely parse simple expression strings without eval:
    e.g. 'refund_amount <= 5000' -> {'field': 'refund_amount', 'operator': '<=', 'value': 5000}
    """
    pattern = r"^([a-zA-Z0-9_\.]+)\s*(==|!=|>=|<=|>|<|IN|NOT_IN|EXISTS)\s*(.*)$"
    match = re.match(pattern, expr_str.strip(), re.IGNORECASE)
    if not match:
        return None

    field = match.group(1).strip()
    op = match.group(2).strip().upper()
    val_raw = match.group(3).strip()

    if op == "EXISTS":
        return {"field": field, "operator": "EXISTS", "value": None}

    # Parse literal value
    if val_raw.lower() == "true":
        val = True
    elif val_raw.lower() == "false":
        val = False
    elif val_raw.lower() == "null" or val_raw.lower() == "none":
        val = None
    elif (val_raw.startswith("'") and val_raw.endswith("'")) or (val_raw.startswith('"') and val_raw.endswith('"')):
        val = val_raw[1:-1]
    else:
        try:
            val = int(val_raw) if "." not in val_raw else float(val_raw)
        except ValueError:
            val = val_raw

    return {"field": field, "operator": op, "value": val}


class ConditionEvaluator:
    """
    Deterministic condition evaluator.
    Works against structured dict trees and parsed strings.
    """

    @classmethod
    def evaluate(cls, condition: Union[Dict[str, Any], str, List[Any]], context: Dict[str, Any]) -> bool:
        """
        Evaluate a condition specification against context.
        Returns True or False deterministically.
        """
        if not condition:
            return True

        # String expression
        if isinstance(condition, str):
            # Check for simple AND / OR split
            if " AND " in condition:
                parts = condition.split(" AND ")
                return all(cls.evaluate(p.strip(), context) for p in parts)
            if " OR " in condition:
                parts = condition.split(" OR ")
                return any(cls.evaluate(p.strip(), context) for p in parts)

            parsed = _parse_expression_string(condition)
            if not parsed:
                return False
            condition = parsed

        # List of conditions (implicit AND)
        if isinstance(condition, list):
            return all(cls.evaluate(c, context) for c in condition)

        if not isinstance(condition, dict):
            return False

        # Boolean combinators: AND / OR
        if "operator" in condition and condition["operator"].upper() in ("AND", "OR"):
            combinator = condition["operator"].upper()
            sub_conditions = condition.get("conditions", [])
            if not sub_conditions:
                return True
            if combinator == "AND":
                return all(cls.evaluate(c, context) for c in sub_conditions)
            else:
                return any(cls.evaluate(c, context) for c in sub_conditions)

        if "AND" in condition:
            return all(cls.evaluate(c, context) for c in condition["AND"])
        if "OR" in condition:
            return any(cls.evaluate(c, context) for c in condition["OR"])

        # Single atomic condition
        field = condition.get("field") or condition.get("path")
        op = condition.get("operator", "==")
        expected = condition.get("value")

        if not field:
            return True

        actual = resolve_path(context, field)
        return evaluate_atomic_condition(actual, op, expected)
