"""
Phase 14 — PII Redaction Service.
Sanitizes sensitive identifiers (emails, phone numbers, payment cards, credentials,
government IDs) across logs, memories, and model contexts.
"""
import re
from typing import Any, Dict, List, Union


class PIIRedactionService:
    """
    Production PII detection and masking service.
    Ensures personal data minimization across logs, memory, and LLM prompts.
    """

    # Email pattern
    EMAIL_PATTERN = re.compile(r"\b([a-zA-Z0-9_.+-])[a-zA-Z0-9_.+-]*@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b")

    # Indian & International phone numbers
    PHONE_PATTERN = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")

    # Payment cards (13 to 19 digits, with or without dashes/spaces)
    CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{1,7}\b")

    # Indian PAN Card (5 letters, 4 digits, 1 letter)
    PAN_PATTERN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b")

    # Indian Aadhaar Number (12 digits, often formatted in 3 groups of 4)
    AADHAAR_PATTERN = re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b")

    # Bearer Tokens & JWT
    JWT_PATTERN = re.compile(r"Bearer\s+eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+")
    API_KEY_PATTERN = re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"]?([A-Za-z0-9-_]{16,})['\"]?")

    @classmethod
    def redact_text(cls, text: str) -> str:
        if not text or not isinstance(text, str):
            return text

        # 1. Redact JWT & Bearer tokens
        redacted = cls.JWT_PATTERN.sub("Bearer [REDACTED_JWT]", text)

        # 2. Redact inline API keys
        redacted = cls.API_KEY_PATTERN.sub(r"\1: [REDACTED_KEY]", redacted)

        # 3. Redact Payment Cards (keep last 4 digits)
        def mask_card(match):
            raw = match.group(0).replace("-", "").replace(" ", "")
            if len(raw) >= 13 and len(raw) <= 19:
                return f"****-****-****-{raw[-4:]}"
            return match.group(0)

        redacted = cls.CARD_PATTERN.sub(mask_card, redacted)

        # 4. Redact Emails (j***@example.com)
        redacted = cls.EMAIL_PATTERN.sub(r"\1***@\2", redacted)

        # 5. Redact Phones (keep last 4)
        def mask_phone(match):
            digits = re.sub(r"\D", "", match.group(0))
            if len(digits) >= 10:
                return f"******{digits[-4:]}"
            return match.group(0)

        redacted = cls.PHONE_PATTERN.sub(mask_phone, redacted)

        # 6. Redact PAN
        redacted = cls.PAN_PATTERN.sub("[REDACTED_PAN]", redacted)

        # 7. Redact Aadhaar
        redacted = cls.AADHAAR_PATTERN.sub("****-****-[REDACTED]", redacted)

        return redacted

    @classmethod
    def redact_dict(cls, data: Union[Dict[str, Any], List[Any], Any]) -> Any:
        """Recursively traverses dictionaries and lists to mask sensitive PII and values."""
        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                lower_k = str(k).lower()
                # If key explicitly indicates a secret or sensitive token
                if any(sec in lower_k for sec in ["password", "secret", "access_token", "refresh_token", "api_key", "jwt"]):
                    new_dict[k] = "[REDACTED_CREDENTIAL]"
                elif any(sec in lower_k for sec in ["card_number", "cvv", "credit_card"]):
                    new_dict[k] = "****-****-****-XXXX"
                else:
                    new_dict[k] = cls.redact_dict(v)
            return new_dict
        elif isinstance(data, list):
            return [cls.redact_dict(item) for item in data]
        elif isinstance(data, str):
            return cls.redact_text(data)
        return data
