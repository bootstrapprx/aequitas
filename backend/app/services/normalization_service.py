from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Dict, Any, List, Optional, Tuple
from app.db.models.dexter_audit import NormalizationAudit
from app.db.models.enums import OnboardingStatus
import re
import pycountry

class NormalizationService:
    """
    Service for normalizing user input and logging to audit trail.
    CANONICAL REFERENCE: NORMALIZATION_CANON.md v1.0
    """

    def log_normalization(
        self,
        db: Session,
        entity_type: str,
        entity_id: str,
        field_name: str,
        user_input: str,
        suggested_value: str,
        final_value: str,
        normalization_type: str,
        confidence_score: float,
        user_accepted: bool
    ) -> NormalizationAudit:
        """
        Log a normalization event to the audit table.
        Defined in NORMALIZATION_CANON.md §6.2
        """
        audit_entry = NormalizationAudit(
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            user_input=user_input,
            suggested_value=suggested_value,
            final_value=final_value,
            normalization_type=normalization_type,
            confidence_score=confidence_score,
            user_accepted_suggestion=user_accepted
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry

    def normalize_company_name(self, name: str) -> Tuple[str, float, List[str]]:
        """
        Normalize company name with capitalization and suffix standardization.
        Returns: (normalized_name, confidence, changes_list)
        """
        original = name
        changes = []
        confidence = 1.0
        
        # 1. Whitespace Normalization (§5.1)
        cleaned = " ".join(name.strip().split())
        if cleaned != original:
            changes.append("Normalized whitespace")
        
        # 2. Capitalization (§2.1)
        # Apply title case to words, but respect known suffixes
        # This is a simplified heuristic; a real implementation might use a library or NER
        # Heuristic: Title Case everything first
        title_cased = cleaned.title()
        
        # Exceptions: Prepositions (of, and, the) lowercase if not first
        # We can implement a basic stop-word lowercaser
        words = title_cased.split()
        processed_words = []
        stop_words = {"Of", "And", "The", "For", "By", "To", "In", "On", "At"}
        
        for i, word in enumerate(words):
            if i > 0 and word in stop_words:
                processed_words.append(word.lower())
            else:
                processed_words.append(word)
        
        capitalized = " ".join(processed_words)
        
        if capitalized != cleaned:
             changes.append("Standardized capitalization")
        
        # 3. Suffix Normalization (§2.2)
        # We need to detect suffixes at the end
        # Mapping from CANON §2.2
        suffix_map = {
            "llc": "LLC", "l.l.c.": "LLC", "llc.": "LLC",
            "inc": "Inc.", "inc.": "Inc.", "incorporated": "Inc.",
            "corp": "Corp.", "corp.": "Corp.", "corporation": "Corp.",
            "ltd": "Ltd.", "ltd.": "Ltd.", "limited": "Ltd.",
            "lp": "LP", "l.p.": "LP",
            "pc": "PC", "p.c.": "PC",
            "llp": "LLP", "l.l.p.": "LLP"
        }
        
        # Check the last word(s)
        # Handle cases like "Acme Services, llc" -> remove comma
        normalized_suffix = capitalized
        
        # Strip trailing comma if present before checking suffix
        if normalized_suffix.endswith(','):
             normalized_suffix = normalized_suffix[:-1].strip()
        
        # Split again
        parts = normalized_suffix.split()
        if parts:
            last_token = parts[-1]
            last_token_lower = last_token.lower()
            
            # Remove trailing dot for lookup if needed, but some map keys have dots
            # Heuristic attempt: exact match
            if last_token_lower in suffix_map:
                parts[-1] = suffix_map[last_token_lower]
                changes.append(f"Normalized suffix '{last_token}' to '{parts[-1]}'")
                confidence = 0.95
            elif last_token_lower.rstrip('.') in suffix_map:
                 # matches "inc" from "Inc."
                 target = suffix_map[last_token_lower.rstrip('.')]
                 parts[-1] = target
                 changes.append(f"Normalized suffix '{last_token}' to '{parts[-1]}'")
                 confidence = 0.95
        
        final_normalization = " ".join(parts)
        
        # Re-attach comma if it was not part of the suffix logic? 
        # Actually standard says "Acme Services LLC" (no comma). 
        # If original had comma "Acme Services, LLC", we likely want to remove it per §2.1 example
        if "," in capitalized and "," not in final_normalization:
             changes.append("Removed unnecessary punctuation")

        # Adjust confidence for complex cases
        if not changes:
            confidence = 1.0 # No change needed
            
        return final_normalization, confidence, changes

    def normalize_country_code(self, input_str: str) -> Optional[Tuple[str, float]]:
        """
        Convert country name/code to ISO 3166-1 alpha-2.
        Returns: (code, confidence) or None
        """
        input_str = input_str.strip()
        
        # Try exact match on alpha-2
        if pycountry.countries.get(alpha_2=input_str.upper()):
            return input_str.upper(), 1.0
            
        # Try exact match on alpha-3
        c = pycountry.countries.get(alpha_3=input_str.upper())
        if c:
            return c.alpha_2, 1.0
            
        # Try search by name
        try:
            matches = pycountry.countries.search_fuzzy(input_str)
            if matches:
                # Top match
                best = matches[0]
                return best.alpha_2, 0.9 # Fuzzy match
        except LookupError:
            pass
            
        return None

    def normalize_currency_code(self, input_str: str) -> Optional[Tuple[str, float]]:
        """
        Convert currency name/symbol to ISO 4217.
        Returns: (code, confidence)
        """
        input_str = input_str.strip()
        
        # Try exact code
        if pycountry.currencies.get(alpha_3=input_str.upper()):
            return input_str.upper(), 1.0
            
        # Try name/symbol mapping (simplified)
        # pycountry.currencies doesn't support fuzzy search easily, might need custom map for symbols
        common_symbols = {
            "$": "USD", "£": "GBP", "€": "EUR", "¥": "JPY",
            "US Dollar": "USD", "Euro": "EUR"
        }
        
        if input_str in common_symbols:
            return common_symbols[input_str], 0.98
            
        # Simple name lookup
        try:
             # This is not robust in pycountry, assuming manual or simple lookup
             # For now return None if not standard
             pass
        except:
            pass
            
        return None

    def classify_economic_activity(self, description: str) -> List[Tuple[str, float]]:
        """
        Extract activity category from natural language.
        Returns list of (Category, Confidence).
        Placeholder for heuristic/LLM implementation.
        """
        # Simple keyword matching for MVP
        description_lower = description.lower()
        
        mapping = {
            "software": "Technology",
            "consulting": "Services",
            "real estate": "Real Estate",
            "restaurant": "Hospitality",
            "medical": "Healthcare",
            "store": "Commerce",
            "shop": "Commerce"
        }
        
        matches = []
        for key, cat in mapping.items():
            if key in description_lower:
                matches.append((cat, 0.85))
        
        if not matches:
             return [("Services", 0.5)] # Default
             
        return sorted(matches, key=lambda x: x[1], reverse=True)

normalization_service = NormalizationService()


class QBOAccountNormalizationService:
    """
    Deterministic normalization for staging QBO accounts.

    Scope:
    - Trim/standardize strings
    - Canonicalize account type/subtype into coarse categories
    - Do NOT infer accounting semantics beyond simple category mapping
    """

    TYPE_MAP = {
        "asset": "ASSET",
        "liability": "LIABILITY",
        "equity": "EQUITY",
        "income": "REVENUE",
        "revenue": "REVENUE",
        "expense": "EXPENSE",
        "cogs": "COGS",
    }

    def normalize_account(self, staging_row) -> Dict[str, Any]:
        """
        Normalize a staging row into a neutral payload.
        """
        name = (staging_row.name or "").strip()
        account_type = (staging_row.account_type or "").strip()
        account_subtype = (staging_row.account_subtype or "").strip()
        currency = (staging_row.currency or "").strip().upper() or "USD"

        canonical_category = self._map_category(account_type, account_subtype)

        normalized = {
            "source_account_id": staging_row.source_account_id,
            "name": name,
            "account_type": account_type,
            "account_subtype": account_subtype,
            "canonical_category": canonical_category,
            "active": bool(staging_row.active),
            "currency": currency,
        }
        return normalized

    def _map_category(self, account_type: str, account_subtype: str) -> Optional[str]:
        lowered = account_type.lower()
        subtype_lower = account_subtype.lower()

        for key, value in self.TYPE_MAP.items():
            if key in lowered or key in subtype_lower:
                return value
        return None
