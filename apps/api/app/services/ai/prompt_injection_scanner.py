"""
Phase 14 — Prompt Injection & Adversarial Defense Scanner.
Deterministic multi-category classifier protecting OpsPilot from:
- INSTRUCTION_OVERRIDE
- SYSTEM_PROMPT_EXTRACTION
- DATA_EXFILTRATION
- TOOL_MANIPULATION
- PRIVILEGE_ESCALATION
- CODE_EXECUTION
- SECRET_REQUEST
- POLICY_BYPASS
- SOCIAL_ENGINEERING
- OBFUSCATED_ATTACK
- CROSS_TENANT_ATTACK
"""
import re
from typing import List, Dict, Any, Set
from pydantic import BaseModel, Field


class PromptInjectionScanResult(BaseModel):
    detected: bool = Field(default=False)
    score: float = Field(default=0.0)  # 0.0 to 1.0
    risk_level: str = Field(default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    categories: List[str] = Field(default_factory=list)
    matched_patterns: List[str] = Field(default_factory=list)


INJECTION_RULES = [
    # 1. INSTRUCTION_OVERRIDE & ROLEPLAY JAILBREAKS
    (
        r"(?i)(ignore|disregard|forget|skip|override|cancel)\s+(all\s+|your\s+|the\s+)?(previous|prior|system|developer|safety|company|all|ai\s+)?\s*(instructions|directives|rules|policies|prompts|guidelines|constraints|rule\s+set|return\s+policy)",
        "INSTRUCTION_OVERRIDE",
        "Direct instruction/policy override command",
        0.95,
    ),
    (
        r"(?i)(pretend\s+you\s+are|let's\s+roleplay|roleplay\s+as|assume\s+you\s+are|imagine\s+a\s+world|act\s+as\s+an?|hypothetical\s+simulation|you\s+are\s+now\s+'?jailbreak|dan\s+mode|unrestricted\s+ai)",
        "INSTRUCTION_OVERRIDE",
        "Persona hijacking / jailbreak attempt",
        0.95,
    ),
    (
        r"(?i)(from\s+now\s+on\s+you|you\s+must|reset\s+instructions|cancel\s+all\s+prior|stop\s+acting\s+as|disregard\s+all\s+limits)",
        "INSTRUCTION_OVERRIDE",
        "Restriction removal directive",
        0.90,
    ),
    (
        r"(?i)(SYSTEM_MESSAGE:|SYSTEM\s+COMMAND:|<!--|<admin_override>|STOP_PROCESSING|END\s+OF\s+SYSTEM\s+PROMPT|---|\=\=\=|```|\'\'\'|###)",
        "INSTRUCTION_OVERRIDE",
        "Delimiter manipulation / prompt injection boundary",
        0.85,
    ),

    # 2. SYSTEM_PROMPT_EXTRACTION
    (
        r"(?i)(reveal|show|display|print|output|repeat|dump|leak|what\s+(is|are))\s+.*?(system\s+prompt|initial\s+prompt|hidden\s+prompt|system\s+instructions|meta\s+prompt|internal\s+guidelines|developer\s+instructions|secret\s+api\s+keys|master\s+keys)",
        "SYSTEM_PROMPT_EXTRACTION",
        "System prompt extraction attempt",
        0.95,
    ),
    (
        r"(?i)(what\s+were\s+the\s+exact\s+developer|display\s+all\s+user\s+session|system\.reveal_prompt)",
        "SYSTEM_PROMPT_EXTRACTION",
        "Developer prompt inquiry",
        0.92,
    ),

    # 3. DATA_EXFILTRATION
    (
        r"(?i)(export|send|dump|exfiltrate|transmit|forward|list|leak|show\s+me|extract|what\s+are)\s+.*?(customer|user|order|financial|credit\s+card|database|db|tenant|salary|revenue|profit|passwords|top\s+100|memory\s+database|full\s+names|bank\s+account|spenders|conversations)",
        "DATA_EXFILTRATION",
        "Mass customer/tenant data exfiltration request",
        0.98,
    ),
    (
        r"(?i)(send|email|forward)\s+.*?(data|records|info|emails)\s+to\s+[\w\.-]+@[\w\.-]+\.\w+",
        "DATA_EXFILTRATION",
        "Exfiltration via outbound email address",
        0.95,
    ),

    # 4. TOOL_MANIPULATION & HIJACKING
    (
        r"(?i)(call|invoke|trigger|execute|modify)\s+(the\s+)?(tool|function|action|permissions|registry)\s+['\"]?[\w_]+['\"]?",
        "TOOL_MANIPULATION",
        "Direct tool invocation attempt",
        0.90,
    ),
    (
        r"(?i)(force\s+(the\s+)?(tool|execution|payment|refund)|tool\s+registry\s+override|shell_exec|system_shell_exec|read_local_file|write_file|bypass\s+tool\s+permission)",
        "TOOL_MANIPULATION",
        "Forced tool execution / dangerous tool call",
        0.98,
    ),

    # 5. PRIVILEGE_ESCALATION & CROSS_TENANT ATTACKS
    (
        r"(?i)(grant|elevate|give)\s+(me|user)\s+(admin|superadmin|root|manager)\s+(role|permissions|access|rights)",
        "PRIVILEGE_ESCALATION",
        "Privilege escalation request",
        0.95,
    ),
    (
        r"(?i)(switch|set|override|change)\s+.*?(my\s+role|to\s+role|organization\s+context|session\.tenant_id|tenant_id|tenant\s+context)|X-Tenant-Override|bypass\s+row\s+level\s+security|shared\s+vector\s+index",
        "CROSS_TENANT_ATTACK",
        "Cross-tenant access attempt",
        0.98,
    ),
    (
        r"(?i)(belonging\s+to\s+(acme|beta|globex)|orders\s+belonging\s+to\s+acme|beta\s+corp|tenant\s+'\*'|list\s+all\s+tenant\s+ids|tenant\s+0000|tenant\s+[a-z]|impersonate\s+user|(organization|tenant|org)\s+['\"`][\w-]+['\"`]|(for|by|inside|of)\s+(organization|tenant|org))",
        "CROSS_TENANT_ATTACK",
        "Targeted cross-tenant query",
        0.92,
    ),

    # 6. CODE & SQL INJECTION
    (
        r"(?i)(execute|run|eval)\s+(this\s+)?(python|code|bash|shell|script|sql|query|command)",
        "CODE_EXECUTION",
        "Arbitrary code/SQL execution command",
        0.98,
    ),
    (
        r"(?i)(';\s*(DROP|DELETE|UPDATE|SELECT|EXEC|INSERT)|1'\s*OR\s*'1'='1'|\bDROP\s+TABLE|\bDROP\s+DATABASE|\bSELECT\s+\*|\bUNION\s+SELECT|<script|xp_cmdshell|jndi:ldap|\{\{.*?\}\}|delete\s+database\s+table)",
        "CODE_EXECUTION",
        "Direct SQL/template injection payload",
        0.99,
    ),
    (
        r"(?i)(import\s+os|import\s+sys|subprocess\.run|os\.system|__import__|exec\s*\(|cat\s+/etc/(passwd|shadow)|`cat\s+)",
        "CODE_EXECUTION",
        "System command execution payload",
        0.99,
    ),

    # 7. SECRET & CREDENTIAL REQUESTS
    (
        r"(?i)(what\s+is|show\s+me|print|reveal|give\s+me|output|dump)\s+.*?(api[_-]?key|secret[_-]?key|jwt[_-]?secret|database[_-]?url|password|auth[_-]?token|bearer|master\s+keys|slack\s+webhook|webhook\s+token|passwords\s+of)",
        "SECRET_REQUEST",
        "Secret / credential extraction request",
        0.98,
    ),
    (
        r"(?i)(env|environment)\s+(variables|secrets|credentials)\s+(dump|reveal|show|print)",
        "SECRET_REQUEST",
        "Environment variables inspection request",
        0.95,
    ),

    # 8. POLICY & APPROVAL BYPASS
    (
        r"(?i)(bypass|skip|ignore|waive|disable|override|disregard)\s+.*?(policy|return\s+policy|policies|rules|permissions|refund\s+limit|safety\s+check|approval\s+step|manager\s+approval|human\s+approval|30[_-]?day|return\s+window|approval\s+workflow)",
        "POLICY_BYPASS",
        "Policy / approval waiver demand",
        0.92,
    ),
    (
        r"(?i)(issue|execute|grant|approve|disburse)\s+.*?(refund|payment|payout|store\s+credit).*?(without\s+validation|without\s+returning|without\s+collecting|without\s+approval|immediately|directly|autonomous\s+authority|infinite)",
        "POLICY_BYPASS",
        "Forced unapproved refund request",
        0.92,
    ),
    (
        r"(?i)(i\s+am\s+the\s+store\s+manager|administrative\s+override\s+code|i\s+authorize\s+myself|this\s+is\s+an\s+emergency|mark\s+invoice.*without\s+po|customer\s+is\s+a\s+celebrity)",
        "POLICY_BYPASS",
        "False authorization pressure",
        0.90,
    ),

    # 9. OBFUSCATED ATTACKS & DOS
    (
        r"(SWdub3Jl|49676e6f7265|I\.g\.n\.o\.r\.e|I_g_n_o_r_e|Reversetext|Rot13|01001001|homoglyph|z-w-s-p|morse\s+code)",
        "OBFUSCATED_ATTACK",
        "Obfuscation or encoding evasion pattern",
        0.95,
    ),
    (
        r"(?i)(infinite\s+loop|circular\s+workflow|100\s+million\s+tokens|500gb\s+payload|5,?000\s+concurrent)",
        "DENIAL_OF_SERVICE",
        "Denial of service attempt",
        0.90,
    ),
    (
        r"(?i)(internal\s+(sop|instruction)|system\s+(note|command|directive)|hidden\s+white-text|IGNORE_AI_RULES|ignore\s+ai\s+rules)",
        "INSTRUCTION_OVERRIDE",
        "Indirect document prompt injection",
        0.92,
    )
]


class PromptInjectionScanner:
    """
    Deterministic prompt injection scanner evaluating all incoming text
    prior to model reasoning or tool execution.
    """

    @classmethod
    def scan(cls, text: str) -> PromptInjectionScanResult:
        if not text or not text.strip():
            return PromptInjectionScanResult()

        # Normalize zero-width spaces and invisible characters
        normalized_text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)

        detected_categories: Set[str] = set()
        matched_patterns: List[str] = []
        max_score = 0.0

        for pattern, category, description, rule_score in INJECTION_RULES:
            if re.search(pattern, normalized_text):
                detected_categories.add(category)
                matched_patterns.append(description)
                if rule_score > max_score:
                    max_score = rule_score

        if not detected_categories:
            return PromptInjectionScanResult(detected=False, score=0.0, risk_level="LOW")

        # Determine risk level based on severity and score
        risk_level = "MEDIUM"
        if max_score >= 0.95 or any(c in detected_categories for c in ["CODE_EXECUTION", "DATA_EXFILTRATION", "SECRET_REQUEST"]):
            risk_level = "CRITICAL"
        elif max_score >= 0.88:
            risk_level = "HIGH"

        return PromptInjectionScanResult(
            detected=True,
            score=round(max_score, 2),
            risk_level=risk_level,
            categories=sorted(list(detected_categories)),
            matched_patterns=matched_patterns,
        )
