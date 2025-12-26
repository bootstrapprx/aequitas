"""
Dexter Tone Enforcement Layer

Ensures all Dexter messages conform to Canon IV tone requirements.

Authority: Canon IV - Intelligence (Zone C) is advisory, never authoritative.

CRITICAL RULES:
- No imperative language ("you should", "you must")
- No urgency ("urgent", "critical", "immediately")
- No authority claims ("I recommend", "I fixed")
- Advisory only ("I noticed", "you may want to")
"""

import re
from typing import Dict, Optional, List
from enum import Enum


class ToneViolationType(str, Enum):
    """Types of tone violations."""
    IMPERATIVE = "imperative"  # "You should", "You must"
    URGENCY = "urgency"  # "Urgent", "Critical"
    AUTHORITY = "authority"  # "I recommend", "I fixed"
    COERCION = "coercion"  # "You need to", "Required"
    AUTO_ACTION = "auto_action"  # "I posted", "I created"


class DexterToneViolation(Exception):
    """
    Raised when Dexter message violates tone requirements.

    This is a violation of Canon IV.
    """
    def __init__(self, violation_type: ToneViolationType, phrase: str, message: str):
        self.violation_type = violation_type
        self.phrase = phrase
        super().__init__(
            f"CANON VIOLATION: Dexter message contains forbidden {violation_type} phrase: '{phrase}'. "
            f"Message: {message}"
        )


class DexterToneEnforcer:
    """
    Enforces Canon IV tone requirements on all Dexter messages.

    All messages must pass validation before being shown to user.

    Usage:
        enforcer = DexterToneEnforcer()
        message = "I noticed you frequently post to AWS Hosting."

        # Validate (raises DexterToneViolation if invalid)
        enforcer.validate(message)

        # Or check without exception
        is_valid, violations = enforcer.check(message)
    """

    # Forbidden phrases by category
    FORBIDDEN_IMPERATIVE = [
        r'\byou should\b',
        r'\byou must\b',
        r'\byou need to\b',
        r'\bdo this\b',
        r'\bmake sure\b',
        r'\bensure that\b',
        r'\bplease do\b',
    ]

    FORBIDDEN_URGENCY = [
        r'\burgent\b',
        r'\bcritical\b',
        r'\bimmediately\b',
        r'\bright now\b',
        r'\bas soon as possible\b',
        r'\basap\b',
        r'\baction required\b',
        r'\bfix this now\b',
    ]

    FORBIDDEN_AUTHORITY = [
        r'\bi recommend\b',
        r'\bi suggest\b',
        r'\byou ought to\b',
        r'\bthis is required\b',
        r'\bthis is mandatory\b',
        r'\byou are required\b',
    ]

    FORBIDDEN_COERCION = [
        r'\bor else\b',
        r'\bor risk\b',
        r'\botherwise\b.*\bfail',
        r'\bmust.*or',
        r'\brequired.*compliance\b',
    ]

    FORBIDDEN_AUTO_ACTION = [
        r'\bi (posted|created|updated|deleted|modified)\b',
        r'\bi have (posted|created|updated|deleted|modified)\b',
        r'\bi\'ve (posted|created|updated|deleted|modified)\b',
        r'\bauto[- ]?(posted|created|updated)\b',
        r'\bautomatically (posted|created|updated)\b',
    ]

    # Approved advisory phrases
    APPROVED_ADVISORY = [
        r'\bi noticed\b',
        r'\byou may want to\b',
        r'\bhave you considered\b',
        r'\bthis may indicate\b',
        r'\bthis could suggest\b',
        r'\bwould you like\b',
        r'\boptional\b',
        r'\bdismiss\b',
    ]

    def __init__(self):
        """Initialize tone enforcer."""
        pass

    def validate(self, message: str) -> None:
        """
        Validate message tone (raises exception if invalid).

        Args:
            message: Dexter message to validate

        Raises:
            DexterToneViolation: If message violates tone requirements
        """
        is_valid, violations = self.check(message)

        if not is_valid:
            # Raise first violation
            violation = violations[0]
            raise DexterToneViolation(
                violation_type=violation["type"],
                phrase=violation["phrase"],
                message=message
            )

    def check(self, message: str) -> tuple[bool, List[Dict]]:
        """
        Check message tone (returns violations without exception).

        Args:
            message: Dexter message to check

        Returns:
            (is_valid, violations)
            - is_valid: True if message passes all checks
            - violations: List of violation details

        Example:
            is_valid, violations = enforcer.check("You should post this now.")
            # is_valid = False
            # violations = [
            #     {"type": "imperative", "phrase": "you should", "index": 0},
            #     {"type": "urgency", "phrase": "now", "index": 25}
            # ]
        """
        violations = []
        message_lower = message.lower()

        # Check imperative phrases
        for pattern in self.FORBIDDEN_IMPERATIVE:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                violations.append({
                    "type": ToneViolationType.IMPERATIVE,
                    "phrase": match.group(0),
                    "index": match.start(),
                    "pattern": pattern
                })

        # Check urgency phrases
        for pattern in self.FORBIDDEN_URGENCY:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                violations.append({
                    "type": ToneViolationType.URGENCY,
                    "phrase": match.group(0),
                    "index": match.start(),
                    "pattern": pattern
                })

        # Check authority phrases
        for pattern in self.FORBIDDEN_AUTHORITY:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                violations.append({
                    "type": ToneViolationType.AUTHORITY,
                    "phrase": match.group(0),
                    "index": match.start(),
                    "pattern": pattern
                })

        # Check coercion phrases
        for pattern in self.FORBIDDEN_COERCION:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                violations.append({
                    "type": ToneViolationType.COERCION,
                    "phrase": match.group(0),
                    "index": match.start(),
                    "pattern": pattern
                })

        # Check auto-action phrases (CRITICAL)
        for pattern in self.FORBIDDEN_AUTO_ACTION:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                violations.append({
                    "type": ToneViolationType.AUTO_ACTION,
                    "phrase": match.group(0),
                    "index": match.start(),
                    "pattern": pattern
                })

        is_valid = len(violations) == 0
        return is_valid, violations

    def format_insight(
        self,
        observation: str,
        context: Optional[str] = None,
        action_label: Optional[str] = None
    ) -> str:
        """
        Format an insight using approved tone template.

        Args:
            observation: What Dexter noticed (factual statement)
            context: Why it might matter (optional)
            action_label: Optional action button text

        Returns:
            Formatted message (validated)

        Example:
            message = enforcer.format_insight(
                observation="You frequently post to 'AWS Hosting'",
                context="This may indicate a subscription expense",
                action_label="Create Template"
            )
            # Returns:
            # "I noticed you frequently post to 'AWS Hosting'.
            #  This may indicate a subscription expense.
            #  [Create Template] [Dismiss]"
        """
        parts = []

        # Start with advisory phrase
        parts.append(f"I noticed {observation}.")

        # Add context if provided
        if context:
            parts.append(f"{context}.")

        # Add optional action
        if action_label:
            parts.append(f"[{action_label}] [Dismiss]")
        else:
            parts.append("[Dismiss]")

        message = " ".join(parts)

        # Validate before returning
        self.validate(message)

        return message

    def sanitize(self, message: str) -> str:
        """
        Attempt to sanitize a message by replacing forbidden phrases.

        This is a best-effort approach. Manual review is recommended.

        Args:
            message: Message to sanitize

        Returns:
            Sanitized message (may still fail validation)

        Example:
            original = "You should post this entry now."
            sanitized = enforcer.sanitize(original)
            # Returns: "You may want to review this entry."
        """
        sanitized = message

        # Replace imperative with advisory
        replacements = {
            r'\byou should\b': 'you may want to',
            r'\byou must\b': 'you may want to',
            r'\byou need to\b': 'you may want to',
            r'\bdo this\b': 'consider this',
            r'\bmake sure\b': 'you may want to verify',
            r'\bensure that\b': 'verify that',
        }

        for pattern, replacement in replacements.items():
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        # Remove urgency
        urgency_removals = [
            r'\s*immediately\b',
            r'\s*right now\b',
            r'\s*as soon as possible\b',
            r'\s*urgent:?\s*',
            r'\s*critical:?\s*',
        ]

        for pattern in urgency_removals:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

        # Replace authority with observation
        sanitized = re.sub(r'\bi recommend\b', 'I noticed', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'\bi suggest\b', 'you may want to', sanitized, flags=re.IGNORECASE)

        return sanitized.strip()


# ============================================================================
# GLOBAL ENFORCER INSTANCE
# ============================================================================

tone_enforcer = DexterToneEnforcer()


# ============================================================================
# APPROVED MESSAGE TEMPLATES
# ============================================================================

APPROVED_TEMPLATES = {
    "recurring_pattern": (
        "I noticed you frequently post to '{account_name}' with description '{description}'. "
        "This may indicate a recurring expense. "
        "Would you like to create a template for this? "
        "[Create Template] [Dismiss]"
    ),

    "anomaly": (
        "I noticed '{account_name}' has an entry for {amount} on {date}, "
        "which is significantly different from your average of {avg_amount}. "
        "This may be expected, or it could indicate an entry error. "
        "[Review Entry] [Dismiss]"
    ),

    "missing_entry": (
        "I noticed you typically post '{description}' entries around the {day_of_month} of each month. "
        "I haven't seen one this month yet. "
        "This is just a reminder in case it was overlooked. "
        "[Create Entry] [Dismiss]"
    ),

    "account_usage": (
        "I noticed '{account_name}' has been used {count} times this period. "
        "This is your most frequently used account. "
        "[View Report] [Dismiss]"
    ),

    "balance_trend": (
        "I noticed '{account_name}' balance has been {trend} for {periods} consecutive periods. "
        "Current balance: {current_balance}. "
        "This may indicate {interpretation}. "
        "[View Trend] [Dismiss]"
    )
}


def format_approved_message(template_name: str, **kwargs) -> str:
    """
    Format a message using approved template.

    Args:
        template_name: Name of approved template
        **kwargs: Template variables

    Returns:
        Formatted and validated message

    Raises:
        DexterToneViolation: If formatted message violates tone

    Example:
        message = format_approved_message(
            "recurring_pattern",
            account_name="AWS Hosting",
            description="AWS monthly charge",
        )
    """
    if template_name not in APPROVED_TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}")

    template = APPROVED_TEMPLATES[template_name]
    message = template.format(**kwargs)

    # Validate
    tone_enforcer.validate(message)

    return message
