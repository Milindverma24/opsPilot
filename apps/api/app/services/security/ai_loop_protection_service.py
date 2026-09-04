"""
Phase 14 — AI Runaway Loop & Circuit Breaker Protection.
Guarantees continuous 24/7 AI employees do not enter infinite recursive loops,
cyclic event triggers, or runaway cost consumption.
"""
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone


MAX_TOOL_CALLS_PER_RUN = 12
MAX_WORKFLOW_DEPTH = 8
MAX_CIRCUIT_BREAKER_FAILURES = 3


class AILoopProtectionService:
    """
    Enforces operational boundaries and detects circular tool/workflow triggers.
    """

    @classmethod
    def check_tool_call_limit(cls, current_call_count: int) -> Tuple[bool, Optional[str]]:
        if current_call_count >= MAX_TOOL_CALLS_PER_RUN:
            return False, f"Runaway loop detected: tool call limit ({MAX_TOOL_CALLS_PER_RUN}) exceeded for run."
        return True, None

    @classmethod
    def check_workflow_depth(cls, current_depth: int) -> Tuple[bool, Optional[str]]:
        if current_depth >= MAX_WORKFLOW_DEPTH:
            return False, f"Recursive workflow limit ({MAX_WORKFLOW_DEPTH}) exceeded."
        return True, None

    @classmethod
    def detect_duplicate_cycle(cls, executed_actions: List[Dict[str, Any]], next_action: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Detects if the AI is proposing the exact same tool with identical inputs 3+ times in a row.
        """
        if len(executed_actions) < 2:
            return True, None

        next_tool = next_action.get("tool_name")
        next_input = next_action.get("input_data", {})

        consecutive_matches = 0
        for act in reversed(executed_actions):
            if act.get("tool_name") == next_tool and act.get("input_data") == next_input:
                consecutive_matches += 1
            else:
                break

        if consecutive_matches >= 2:
            return False, f"Runaway loop detected: repetitive cycle for tool '{next_tool}' with identical arguments."

        return True, None
