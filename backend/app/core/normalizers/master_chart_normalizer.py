"""
Master Chart Normalizer
Normalizes master chart account names and descriptions
Enforces Bob's OCD-level capitalization requirements
"""

import re
from typing import List


class MasterChartNormalizer:
    """
    Normalizes master chart account names
    Enforces consistent capitalization and formatting
    """

    # Exception words (lowercase in title case unless first word)
    EXCEPTION_WORDS = {
        "of", "and", "the", "in", "on", "at", "to", "for", "with",
        "by", "from", "as", "or", "but", "a", "an"
    }

    # Always capitalize these (acronyms and special terms)
    ALWAYS_CAPS = {
        "GAAP", "US-GAAP", "IRS", "FASB", "SEC", "US", "USA",
        "AP", "AR", "COGS", "SG&A", "R&D", "IT", "HR", "PR",
        "CEO", "CFO", "CTO", "LLC", "Inc", "Corp", "Co",
        "VAT", "GST", "HST", "PST",  # Taxes
        "P&L", "COA", "GL", "SL"  # Accounting acronyms
    }

    # Always lowercase (unless first word)
    ALWAYS_LOWER = {
        "vs", "via"
    }

    def __init__(self):
        """Initialize normalizer"""
        pass

    def normalize_account_name(self, name: str) -> str:
        """
        Apply capitalization rules to account name

        Rules:
        1. Title case by default
        2. Exception words lowercase (unless first word)
        3. Acronyms always uppercase
        4. Preserve special punctuation (/, -, &, etc.)

        Args:
            name: Raw account name

        Returns:
            Normalized account name
        """
        if not name:
            return ""

        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name.strip())

        # Split into words, preserving punctuation
        words = name.split()
        normalized_words = []

        for i, word in enumerate(words):
            # Skip empty words
            if not word:
                continue

            # Check if it's an always-caps word (exact match, case-insensitive)
            if word.upper() in self.ALWAYS_CAPS or word in self.ALWAYS_CAPS:
                # Find the matching format from ALWAYS_CAPS
                matching = [ac for ac in self.ALWAYS_CAPS if ac.upper() == word.upper()]
                if matching:
                    normalized_words.append(matching[0])
                else:
                    normalized_words.append(word.upper())
                continue

            # First word always capitalized
            if i == 0:
                normalized_words.append(self._capitalize_word(word))
                continue

            # Check if it's an exception word (lowercase unless first)
            if word.lower() in self.EXCEPTION_WORDS:
                normalized_words.append(word.lower())
                continue

            # Check if it's always lowercase
            if word.lower() in self.ALWAYS_LOWER:
                normalized_words.append(word.lower())
                continue

            # Normal title case
            normalized_words.append(self._capitalize_word(word))

        return " ".join(normalized_words)

    def normalize_description(self, description: str) -> str:
        """
        Normalize long description

        Rules:
        1. Sentence case (first letter capitalized)
        2. Trim whitespace
        3. Ensure ends with period
        4. Consistent spacing

        Args:
            description: Raw description

        Returns:
            Normalized description
        """
        if not description:
            return ""

        # Trim and normalize whitespace
        description = re.sub(r'\s+', ' ', description.strip())

        # Ensure sentence case (first letter capitalized)
        if description:
            description = description[0].upper() + description[1:]

        # Ensure ends with period (if it's a complete sentence)
        if description and not description[-1] in ['.', '!', '?', ':', ';']:
            description += '.'

        return description

    def normalize_code(self, code: str) -> str:
        """
        Normalize account code format

        Rules:
        1. Remove whitespace
        2. Consistent format (no leading/trailing dots)

        Args:
            code: Raw account code

        Returns:
            Normalized code
        """
        if not code:
            return ""

        # Remove whitespace
        code = code.strip().replace(" ", "")

        # Remove leading/trailing dots
        code = code.strip(".")

        return code

    def normalize_category(self, category: str) -> str:
        """
        Normalize category name

        Args:
            category: Raw category name

        Returns:
            Normalized category name
        """
        if not category:
            return ""

        # Common category mappings
        category_map = {
            "assets": "Asset",
            "asset": "Asset",
            "liabilities": "Liability",
            "liability": "Liability",
            "equity": "Equity",
            "equities": "Equity",
            "revenue": "Revenue",
            "revenues": "Revenue",
            "income": "Revenue",
            "expense": "Expense",
            "expenses": "Expense",
            "cost of goods sold": "Cost of Goods Sold",
            "cogs": "Cost of Goods Sold",
            "other income": "Other Income",
            "other expense": "Other Expense",
        }

        category_lower = category.lower().strip()
        return category_map.get(category_lower, self.normalize_account_name(category))

    def normalize_fs_mapping(self, fs_mapping: str) -> str:
        """
        Normalize financial statement mapping

        Args:
            fs_mapping: Raw FS mapping

        Returns:
            Normalized FS mapping
        """
        if not fs_mapping:
            return "Not Applicable"

        # Common mappings
        fs_map = {
            "balance sheet": "Balance Sheet",
            "bs": "Balance Sheet",
            "income statement": "Income Statement",
            "is": "Income Statement",
            "p&l": "Income Statement",
            "profit and loss": "Income Statement",
            "not applicable": "Not Applicable",
            "na": "Not Applicable",
            "n/a": "Not Applicable",
        }

        fs_lower = fs_mapping.lower().strip()
        return fs_map.get(fs_lower, fs_mapping)

    def normalize_normal_balance(self, normal_balance: str) -> str:
        """
        Normalize normal balance

        Args:
            normal_balance: Raw normal balance

        Returns:
            Normalized normal balance (Debit or Credit)
        """
        if not normal_balance:
            return ""

        balance_map = {
            "debit": "Debit",
            "dr": "Debit",
            "d": "Debit",
            "credit": "Credit",
            "cr": "Credit",
            "c": "Credit",
        }

        balance_lower = normal_balance.lower().strip()
        return balance_map.get(balance_lower, normal_balance)

    def _capitalize_word(self, word: str) -> str:
        """
        Capitalize a single word intelligently
        Handles hyphenated words and possessives

        Args:
            word: Single word

        Returns:
            Capitalized word
        """
        if not word:
            return ""

        # Handle hyphenated words (e.g., "Self-Employment")
        if "-" in word:
            parts = word.split("-")
            return "-".join([part.capitalize() for part in parts])

        # Handle possessives (e.g., "Owner's")
        if "'" in word:
            parts = word.split("'")
            return "'".join([parts[0].capitalize()] + parts[1:])

        # Normal capitalize
        return word.capitalize()

    def normalize_account_data(self, account_data: dict) -> dict:
        """
        Normalize all fields in an account dictionary

        Args:
            account_data: Dictionary containing account fields

        Returns:
            Dictionary with normalized fields
        """
        normalized = account_data.copy()

        # Normalize each field if present
        if "account_name" in normalized:
            normalized["account_name"] = self.normalize_account_name(normalized["account_name"])

        if "long_description" in normalized:
            normalized["long_description"] = self.normalize_description(normalized["long_description"])

        if "description" in normalized:
            normalized["description"] = self.normalize_description(normalized["description"])

        if "code" in normalized:
            normalized["code"] = self.normalize_code(normalized["code"])

        if "category" in normalized:
            normalized["category"] = self.normalize_category(normalized["category"])

        if "fs_mapping" in normalized:
            normalized["fs_mapping"] = self.normalize_fs_mapping(normalized["fs_mapping"])

        if "normal_balance" in normalized:
            normalized["normal_balance"] = self.normalize_normal_balance(normalized["normal_balance"])

        return normalized
