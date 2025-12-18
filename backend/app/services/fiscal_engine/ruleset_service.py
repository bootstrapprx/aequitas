"""
Service for managing tax rulesets.
"""
import uuid
from sqlalchemy.orm import Session
from typing import Optional
from app.db.models.tax_ruleset import TaxRuleset


class RulesetService:
    """Service for creating and retrieving tax rulesets."""

    def __init__(self, db: Session):
        self.db = db

    def get_active_ruleset(self, version: str, scope: str = "PASS_THROUGH_BASE") -> Optional[TaxRuleset]:
        """
        Get the active ruleset for a specific version and scope.

        Args:
            version: Ruleset version (e.g., "2025.1")
            scope: Ruleset scope (default: "PASS_THROUGH_BASE")

        Returns:
            TaxRuleset or None if not found
        """
        return self.db.query(TaxRuleset).filter(
            TaxRuleset.version == version,
            TaxRuleset.scope == scope,
            TaxRuleset.status == "ACTIVE"
        ).first()

    def create_ruleset(
        self,
        version: str,
        scope: str = "PASS_THROUGH_BASE",
        jurisdiction: Optional[str] = None,
        rules: Optional[list] = None
    ) -> TaxRuleset:
        """
        Create a new tax ruleset.

        Args:
            version: Ruleset version
            scope: Ruleset scope
            jurisdiction: Optional jurisdiction (e.g., "US", "CA")
            rules: List of rule definitions

        Returns:
            Created TaxRuleset
        """
        ruleset = TaxRuleset(
            id=uuid.uuid4(),
            version=version,
            scope=scope,
            jurisdiction=jurisdiction,
            status="ACTIVE",
            rules=rules or []
        )

        self.db.add(ruleset)
        self.db.commit()
        self.db.refresh(ruleset)

        return ruleset

    def seed_default_ruleset(self, version: str = "2025.1") -> TaxRuleset:
        """
        Seed the default ruleset if it doesn't exist.

        For v1, this creates an empty ruleset (no rules yet).
        Future versions will include actual tax adjustment rules.

        Args:
            version: Version to seed (default: "2025.1")

        Returns:
            Existing or newly created TaxRuleset
        """
        existing = self.get_active_ruleset(version, "PASS_THROUGH_BASE")
        if existing:
            return existing

        # Create empty ruleset for v1
        # Future: Add rules for meal & entertainment limits, depreciation, etc.
        return self.create_ruleset(
            version=version,
            scope="PASS_THROUGH_BASE",
            jurisdiction=None,
            rules=[]  # Empty for v1
        )
