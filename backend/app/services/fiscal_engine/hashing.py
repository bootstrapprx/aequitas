"""
Hashing utilities for deterministic tax run identification.
"""
import hashlib
import json
from datetime import date
from uuid import UUID
from typing import Any, Dict, List
from decimal import Decimal


def _serialize_value(obj: Any) -> Any:
    """Serialize Python objects to JSON-compatible types."""
    if isinstance(obj, (date, UUID)):
        return str(obj)
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: _serialize_value(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_value(item) for item in obj]
    return obj


def compute_inputs_hash(
    company_id: UUID,
    period_start: date,
    period_end: date,
    trial_balance_snapshot: List[Dict[str, Any]],
    profile: Dict[str, Any],
    ruleset_version: str
) -> str:
    """
    Compute a deterministic SHA-256 hash of all inputs to a tax run.

    This ensures that the same inputs always produce the same hash,
    allowing for deterministic recalculation and caching.

    Args:
        company_id: Company UUID
        period_start: Period start date
        period_end: Period end date
        trial_balance_snapshot: List of account balances
        profile: Entity tax profile dictionary
        ruleset_version: Version of the ruleset being used

    Returns:
        SHA-256 hash as hexadecimal string
    """
    # Build a canonical representation of all inputs
    inputs = {
        "company_id": str(company_id),
        "period_start": str(period_start),
        "period_end": str(period_end),
        "trial_balance": _serialize_value(trial_balance_snapshot),
        "profile": _serialize_value(profile),
        "ruleset_version": ruleset_version,
    }

    # Convert to JSON with sorted keys for determinism
    canonical_json = json.dumps(inputs, sort_keys=True, separators=(',', ':'))

    # Compute SHA-256 hash
    hash_obj = hashlib.sha256(canonical_json.encode('utf-8'))
    return hash_obj.hexdigest()
