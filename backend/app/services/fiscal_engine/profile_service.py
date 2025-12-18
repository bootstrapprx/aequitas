"""
Service for managing entity tax profiles.
"""
import uuid
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from app.db.models.entity_tax_profile import EntityTaxProfile
from app.schemas.fiscal_engine import EntityTaxProfileCreate, EntityTaxProfileUpdate


class ProfileService:
    """Service for creating and managing entity tax profiles."""

    def __init__(self, db: Session):
        self.db = db

    def get_profile(self, company_id: UUID) -> Optional[EntityTaxProfile]:
        """
        Get the tax profile for a company.

        Args:
            company_id: Company UUID

        Returns:
            EntityTaxProfile or None if not found
        """
        return self.db.query(EntityTaxProfile).filter(
            EntityTaxProfile.company_id == company_id
        ).first()

    def get_or_create_profile(self, company_id: UUID) -> EntityTaxProfile:
        """
        Get existing profile or create default profile for a company.

        Creates a default pass-through LLC profile if none exists.

        Args:
            company_id: Company UUID

        Returns:
            EntityTaxProfile (existing or newly created)
        """
        existing = self.get_profile(company_id)
        if existing:
            return existing

        # Create default profile
        profile = EntityTaxProfile(
            id=uuid.uuid4(),
            company_id=company_id,
            entity_type="LLC",
            tax_regime="PASS_THROUGH",
            accounting_method=None,  # Unknown
            fiscal_year_start=None,  # Unknown
            jurisdictions=[],
            elections={},
            notes=None
        )

        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)

        return profile

    def create_profile(self, profile_data: EntityTaxProfileCreate) -> EntityTaxProfile:
        """
        Create a new tax profile.

        Args:
            profile_data: Profile creation data

        Returns:
            Created EntityTaxProfile

        Raises:
            ValueError: If profile already exists for company
        """
        existing = self.get_profile(profile_data.company_id)
        if existing:
            raise ValueError(f"Tax profile already exists for company {profile_data.company_id}")

        profile = EntityTaxProfile(
            id=uuid.uuid4(),
            company_id=profile_data.company_id,
            entity_type=profile_data.entity_type,
            tax_regime=profile_data.tax_regime,
            accounting_method=profile_data.accounting_method,
            fiscal_year_start=profile_data.fiscal_year_start,
            jurisdictions=profile_data.jurisdictions,
            elections=profile_data.elections,
            notes=profile_data.notes
        )

        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)

        return profile

    def update_profile(self, company_id: UUID, update_data: EntityTaxProfileUpdate) -> EntityTaxProfile:
        """
        Update an existing tax profile.

        Args:
            company_id: Company UUID
            update_data: Profile update data

        Returns:
            Updated EntityTaxProfile

        Raises:
            ValueError: If profile doesn't exist
        """
        profile = self.get_profile(company_id)
        if not profile:
            raise ValueError(f"Tax profile not found for company {company_id}")

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(profile, key, value)

        self.db.commit()
        self.db.refresh(profile)

        return profile
