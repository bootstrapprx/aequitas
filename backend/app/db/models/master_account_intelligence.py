"""
MasterAccountIntelligence SQLAlchemy model.

CANONICAL REFERENCE:
- docs/canonical/CANON.md (Step 4: Extension Boundaries, Zone C)
- Migration 032: Relocate Advisory Metadata

CANON IV - INTELLIGENCE BOUNDARIES (ZONE C):
This model represents the Intelligence & Advisory Layer.
It provides AI-driven suggestions, classification hints, and vendor associations.

CRITICAL RULES:
- Read-only access to truth core (master_accounts)
- All suggestions must require human confirmation
- Cannot write to accounting truth tables
- Physically separated from truth-bearing data
"""
import uuid
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, func, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.db.base import Base


class MasterAccountIntelligence(Base):
    """
    Advisory intelligence and suggestions for MasterAccounts.

    ZONE C (Intelligence Layer):
    - Provides AI-friendly metadata for account classification
    - Stores vendor hints and keyword tags
    - Never contains accounting truth
    - Suggestions require human confirmation

    LIFECYCLE:
    - Created when AI generates suggestions for a master account
    - Updated as intelligence improves
    - Can be deleted without affecting truth core
    - No CASCADE to truth tables

    INVARIANTS:
    - One-to-one with MasterAccount (optional)
    - Cannot modify master_accounts table
    - Read-only relationship to truth
    """
    __tablename__ = "master_account_intelligence"

    # ========================================================================
    # PRIMARY KEY
    # ========================================================================
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # ========================================================================
    # FOREIGN KEY (One-to-One with MasterAccount)
    # ========================================================================
    master_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("master_accounts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    """Reference to MasterAccount (Zone A). One-to-one relationship."""

    # ========================================================================
    # ADVISORY METADATA (Formerly in master_accounts)
    # ========================================================================
    tags = Column(ARRAY(String), nullable=True)
    """AI-friendly keywords for classification and search"""

    default_vendors = Column(ARRAY(String), nullable=True)
    """Common vendor associations for auto-suggestion"""

    # ========================================================================
    # INTELLIGENCE CONFIDENCE SCORES
    # ========================================================================
    classification_confidence = Column(Numeric(3, 2), nullable=True)
    """
    Confidence score for auto-classification (0.00-1.00).
    Higher scores indicate more reliable suggestions.
    """

    # ========================================================================
    # AUDIT TIMESTAMPS
    # ========================================================================
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    """Creation timestamp"""

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    """Last update timestamp"""

    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    master_account = relationship(
        "MasterAccount",
        back_populates="intelligence",
        foreign_keys=[master_account_id]
    )
    """Referenced master account (Zone A truth core)"""

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def __repr__(self):
        return f"<MasterAccountIntelligence(master_account_id='{self.master_account_id}', tags={len(self.tags or [])}, vendors={len(self.default_vendors or [])})>"

    def matches_keywords(self, keywords: list[str]) -> bool:
        """
        Check if this intelligence record matches any of the given keywords.

        Args:
            keywords: List of keywords to search for

        Returns:
            True if any keyword matches, False otherwise
        """
        if not keywords or not self.tags:
            return False

        tags_lower = [tag.lower() for tag in self.tags]
        return any(keyword.lower() in tags_lower for keyword in keywords)

    def matches_vendor(self, vendor_name: str) -> bool:
        """
        Check if this intelligence record is associated with a given vendor.

        Args:
            vendor_name: Vendor name to match

        Returns:
            True if vendor is associated, False otherwise
        """
        if not self.default_vendors or not vendor_name:
            return False

        vendor_lower = vendor_name.lower()
        return any(vendor_lower in v.lower() for v in self.default_vendors)

    def to_dict(self):
        """
        Return object data in easily serializable format.

        Returns:
            Dictionary representation of intelligence metadata
        """
        return {
            "id": str(self.id),
            "master_account_id": str(self.master_account_id),
            "tags": self.tags or [],
            "default_vendors": self.default_vendors or [],
            "classification_confidence": float(self.classification_confidence) if self.classification_confidence else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
