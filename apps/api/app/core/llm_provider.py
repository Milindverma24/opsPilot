"""
Phase 7 — LLM Provider abstraction.

Architecture principle: Agent orchestration never couples directly to any
single AI SDK. All LLM calls go through this abstraction layer.

Providers:
- DeterministicProvider: rule-based, zero API calls, works in all tests
- OpenAIProvider: real LLM calls when OPENAI_API_KEY is set
"""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from apps.api.app.core.config import settings


# ---------------------------------------------------------------------------
# Base provider interface
# ---------------------------------------------------------------------------

class BaseLLMProvider(ABC):
    """All LLM providers implement this interface."""

    @abstractmethod
    def classify(self, system_prompt: str, user_message: str, labels: List[str]) -> Dict[str, Any]:
        """Classify text into one of the given labels. Returns {label, confidence, reason}."""
        ...

    @abstractmethod
    def extract_entities(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        """Extract structured entities from text. Returns a dict matching EntityExtractionResult."""
        ...

    @abstractmethod
    def reason(self, system_prompt: str, task_prompt: str, context_sections: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Produce a structured reasoning output.
        context_sections: [{"section": "ORDER", "content": "..."}]
        Returns {decision, decision_summary, reason_codes, evidence_ids, confidence, proposed_response}
        """
        ...

    @abstractmethod
    def generate_response(self, system_prompt: str, user_message: str, context: str) -> str:
        """Generate a natural language response grounded in provided context."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Returns True if the provider is operational."""
        ...

    def provider_name(self) -> str:
        return self.__class__.__name__


# ---------------------------------------------------------------------------
# Deterministic Provider (rule-based, zero API calls)
# ---------------------------------------------------------------------------

_INTENT_KEYWORDS: Dict[str, List[str]] = {
    "PRODUCT_QUESTION": ["available", "have", "stock", "size", "color", "hoodie", "jeans", "dress", "shirt", "product", "do you sell"],
    "ORDER_STATUS": ["where is my order", "order status", "order number", "when will", "my order", "tracking"],
    "ORDER_CANCELLATION": ["cancel my order", "cancel order", "want to cancel"],
    "SHIPPING_DELAY": ["delayed", "late", "hasn't arrived", "not delivered", "overdue", "still not received"],
    "SHIPPING_QUESTION": ["shipping", "delivery time", "how long", "ship to"],
    "RETURN_REQUEST": ["return", "send back", "returning", "want to return"],
    "REFUND_REQUEST": ["refund", "money back", "reimburse", "get my money"],
    "EXCHANGE_REQUEST": ["exchange", "swap", "different size", "replace"],
    "COMPLAINT": ["complaint", "unhappy", "terrible", "awful", "worst", "disappointed", "unacceptable"],
    "COUPON_QUESTION": ["coupon", "discount code", "promo", "voucher", "offer"],
    "PAYMENT_ISSUE": ["payment failed", "charged twice", "duplicate charge", "billing", "payment issue"],
    "PROMPT_INJECTION": [
        "ignore previous instructions", "ignore all", "disregard", "override",
        "reveal your system prompt", "forget everything", "you are now", "jailbreak",
        "give everyone a discount", "bypass", "run sql", "execute", "shell", "api key",
        "ignore company rules", "disable security", "system configuration"
    ],
}


class DeterministicProvider(BaseLLMProvider):
    """
    Rule-based provider for testing and development.
    No API key required. Returns realistic structured outputs.
    """

    def classify(self, system_prompt: str, user_message: str, labels: List[str]) -> Dict[str, Any]:
        msg_lower = user_message.lower()

        # Prompt injection takes highest priority
        for kw in _INTENT_KEYWORDS.get("PROMPT_INJECTION", []):
            if kw in msg_lower:
                return {
                    "label": "PROMPT_INJECTION",
                    "confidence": 0.98,
                    "reason": f"Detected injection keyword: '{kw}'",
                    "is_prompt_injection": True,
                }

        # Check each intent
        for intent, keywords in _INTENT_KEYWORDS.items():
            if intent == "PROMPT_INJECTION":
                continue
            for kw in keywords:
                if kw in msg_lower:
                    return {
                        "label": intent,
                        "confidence": 0.85,
                        "reason": f"Matched keyword pattern: '{kw}'",
                        "is_prompt_injection": False,
                    }

        return {
            "label": "UNKNOWN",
            "confidence": 0.55,
            "reason": "No intent pattern matched",
            "is_prompt_injection": False,
        }

    def extract_entities(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        entities: Dict[str, Any] = {}

        # Order number: UT followed by digits
        order_match = re.search(r'\b(UT\d{4,8})\b', user_message, re.IGNORECASE)
        if order_match:
            entities["order_number"] = {"value": order_match.group(1).upper(), "raw_text": order_match.group(0)}

        # Tracking number: common carrier patterns
        tracking_match = re.search(r'\b([A-Z]{2}\d{9,20}[A-Z]{0,2})\b', user_message)
        if tracking_match:
            entities["tracking_number"] = {"value": tracking_match.group(1), "raw_text": tracking_match.group(0)}

        # Currency amount with ₹ or Rs or INR
        amount_match = re.search(r'(?:₹|Rs\.?|INR)\s*(\d[\d,]*(?:\.\d{1,2})?)', user_message, re.IGNORECASE)
        if amount_match:
            amount_str = amount_match.group(1).replace(",", "")
            try:
                entities["refund_amount"] = float(amount_str)
                entities["refund_currency"] = "INR"
            except ValueError:
                pass

        # Size
        size_match = re.search(r'\b(XS|S|M|L|XL|XXL|2XL|3XL)\b', user_message, re.IGNORECASE)
        if size_match:
            entities["size"] = size_match.group(1).upper()

        # Color
        colors = ["black", "white", "blue", "red", "green", "grey", "gray", "navy", "beige", "brown", "pink", "yellow"]
        for color in colors:
            if color in user_message.lower():
                entities["color"] = color
                break

        return entities

    def reason(self, system_prompt: str, task_prompt: str, context_sections: List[Dict[str, str]]) -> Dict[str, Any]:
        """Deterministic reasoning based on task prompt keywords."""
        task_lower = task_prompt.lower()

        # Refund requiring approval
        if "refund" in task_lower:
            return {
                "decision": "REQUEST_APPROVAL",
                "decision_summary": "Refund request identified. Amount requires human approval per refund policy.",
                "reason_codes": ["refund_request", "financial_action"],
                "evidence_ids": [],
                "confidence": 0.82,
                "risk_level": "HIGH",
                "proposed_response": "I've identified your refund request and prepared it for manager review.",
                "grounded": False,
            }

        # Return request
        if "return" in task_lower:
            return {
                "decision": "EXECUTE_ACTION",
                "decision_summary": "Return request identified. Checking return policy eligibility.",
                "reason_codes": ["return_request", "policy_check"],
                "evidence_ids": [],
                "confidence": 0.85,
                "risk_level": "MEDIUM",
                "proposed_response": "I can help initiate a return. Let me check your order eligibility.",
                "grounded": False,
            }

        # Shipping delay
        if any(kw in task_lower for kw in ["delayed", "late", "shipping"]):
            return {
                "decision": "ANSWER",
                "decision_summary": "Shipping delay query. Retrieving shipment status and policy information.",
                "reason_codes": ["shipping_delay", "informational"],
                "evidence_ids": [],
                "confidence": 0.88,
                "risk_level": "LOW",
                "proposed_response": "I'll check your shipment status right away.",
                "grounded": False,
            }

        # Order status
        if "order" in task_lower:
            return {
                "decision": "ANSWER",
                "decision_summary": "Order status query. Looking up order and shipment details.",
                "reason_codes": ["order_lookup", "informational"],
                "evidence_ids": [],
                "confidence": 0.90,
                "risk_level": "LOW",
                "proposed_response": "Let me look up your order status.",
                "grounded": False,
            }

        # Product question
        if any(kw in task_lower for kw in ["product", "available", "stock", "size", "hoodie"]):
            return {
                "decision": "ANSWER",
                "decision_summary": "Product availability question. Checking inventory.",
                "reason_codes": ["product_lookup", "informational"],
                "evidence_ids": [],
                "confidence": 0.92,
                "risk_level": "LOW",
                "proposed_response": "Let me check our product availability for you.",
                "grounded": False,
            }

        # Prompt injection
        if any(kw in task_lower for kw in ["ignore", "bypass", "override", "sql", "system"]):
            return {
                "decision": "REFUSE",
                "decision_summary": "Request contains directive attempting to bypass system policies. Request refused.",
                "reason_codes": ["prompt_injection", "policy_violation", "security"],
                "evidence_ids": [],
                "confidence": 0.99,
                "risk_level": "CRITICAL",
                "proposed_response": "I'm unable to process this request as it appears to contain instructions that conflict with company policy.",
                "grounded": False,
            }

        # Unknown
        return {
            "decision": "ESCALATE",
            "decision_summary": "Request intent not recognized. Escalating to human agent.",
            "reason_codes": ["unknown_intent", "low_confidence"],
            "evidence_ids": [],
            "confidence": 0.50,
            "risk_level": "LOW",
            "proposed_response": "I'll connect you with a human agent who can better assist you.",
            "grounded": False,
        }

    def generate_response(self, system_prompt: str, user_message: str, context: str) -> str:
        return f"[DeterministicProvider] Response to: {user_message[:100]}..."

    def health_check(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# OpenAI Provider
# ---------------------------------------------------------------------------

class OpenAIProvider(BaseLLMProvider):
    """
    Real LLM provider using the OpenAI SDK.
    Used when OPENAI_API_KEY is set and LLM_PROVIDER = "openai".
    """

    def __init__(self):
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self._model = settings.LLM_MODEL
            self._temperature = settings.LLM_TEMPERATURE
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai>=1.0")

    def _call(self, messages: List[Dict[str, str]], response_format: Optional[str] = "json_object") -> str:
        kwargs: Dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "max_tokens": settings.MAX_OUTPUT_TOKENS,
        }
        if response_format == "json_object":
            kwargs["response_format"] = {"type": "json_object"}
        resp = self._client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

    def classify(self, system_prompt: str, user_message: str, labels: List[str]) -> Dict[str, Any]:
        label_list = ", ".join(labels)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": (
                f"Classify the following message into exactly one of: [{label_list}].\n"
                f"Return JSON: {{\"label\": \"...\", \"confidence\": 0.0-1.0, \"reason\": \"...\", \"is_prompt_injection\": false}}\n\n"
                f"Message: {user_message}"
            )},
        ]
        raw = self._call(messages)
        return json.loads(raw)

    def extract_entities(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": (
                f"Extract entities from this message. Return JSON with keys: "
                f"order_number, tracking_number, refund_amount, refund_currency, size, color, sku, product_name, coupon_code, return_reason.\n"
                f"Use null for missing fields. For order_number format like UT12345.\n\n"
                f"Message: {user_message}"
            )},
        ]
        raw = self._call(messages)
        return json.loads(raw)

    def reason(self, system_prompt: str, task_prompt: str, context_sections: List[Dict[str, str]]) -> Dict[str, Any]:
        context_text = "\n".join(
            f"<{s['section']}>\n{s['content']}\n</{s['section']}>"
            for s in context_sections
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": (
                f"Task: {task_prompt}\n\n"
                f"Context:\n{context_text}\n\n"
                f"Return JSON: {{\"decision\": \"ANSWER|ASK_CLARIFICATION|CREATE_TASK|CREATE_SUPPORT_TICKET|"
                f"REQUEST_APPROVAL|EXECUTE_ACTION|ESCALATE|REFUSE|NO_ACTION\", "
                f"\"decision_summary\": \"...\", \"reason_codes\": [...], \"evidence_ids\": [...], "
                f"\"confidence\": 0.0-1.0, \"risk_level\": \"LOW|MEDIUM|HIGH|CRITICAL\", "
                f"\"proposed_response\": \"...\", \"grounded\": true/false}}"
            )},
        ]
        raw = self._call(messages)
        return json.loads(raw)

    def generate_response(self, system_prompt: str, user_message: str, context: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nCustomer message: {user_message}"},
        ]
        return self._call(messages, response_format=None)

    def health_check(self) -> bool:
        try:
            models = self._client.models.list()
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_provider_instance: Optional[BaseLLMProvider] = None


def get_llm_provider() -> BaseLLMProvider:
    """
    Returns the configured LLM provider.
    Defaults to DeterministicProvider if no API key is set.
    """
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    provider_name = settings.LLM_PROVIDER.lower()

    if provider_name == "openai" and settings.OPENAI_API_KEY:
        _provider_instance = OpenAIProvider()
    else:
        # Always fall back to deterministic if no key is available
        _provider_instance = DeterministicProvider()

    return _provider_instance


def reset_provider() -> None:
    """Reset provider singleton — for testing."""
    global _provider_instance
    _provider_instance = None
