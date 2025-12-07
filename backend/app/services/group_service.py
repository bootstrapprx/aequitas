from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
import uuid

from app.db.models.group_company import GroupCompany
from app.db.models.group_company_member import GroupCompanyMember
from app.db.models.company import Company
from app.db.models.account_mapping import AccountMapping
from app.db.models.company_account import CompanyAccount


class GroupService:
    @staticmethod
    def create_group(
        db: Session,
        name: str,
        description: Optional[str],
        owner_user_id: UUID
    ) -> GroupCompany:
        """
        Create a new group company.
        """
        # Check if group name already exists
        existing = db.query(GroupCompany).filter(GroupCompany.name == name).first()
        if existing:
            raise ValueError(f"Group with name '{name}' already exists")

        group = GroupCompany(
            name=name,
            description=description,
            owner_user_id=owner_user_id
        )
        db.add(group)
        db.commit()
        db.refresh(group)
        return group

    @staticmethod
    def get_groups_for_user(db: Session, user_id: UUID) -> List[GroupCompany]:
        """
        Get all groups owned by a user.
        For now, only returns groups owned by the user.
        Could be extended to include groups where user has access to member companies.
        """
        return db.query(GroupCompany).filter(
            GroupCompany.owner_user_id == user_id
        ).all()

    @staticmethod
    def get_group_by_id(db: Session, group_id: UUID) -> Optional[GroupCompany]:
        """
        Get a group by ID.
        """
        return db.query(GroupCompany).filter(GroupCompany.id == group_id).first()

    @staticmethod
    def add_company_to_group(
        db: Session,
        group_id: UUID,
        company_id: UUID
    ) -> GroupCompanyMember:
        """
        Add a company to a group.
        """
        # Check if group exists
        group = GroupService.get_group_by_id(db, group_id)
        if not group:
            raise ValueError("Group not found")

        # Check if company exists
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError("Company not found")

        # Check if already a member
        existing = db.query(GroupCompanyMember).filter(
            GroupCompanyMember.group_company_id == group_id,
            GroupCompanyMember.company_id == company_id
        ).first()

        if existing:
            return existing

        member = GroupCompanyMember(
            group_company_id=group_id,
            company_id=company_id
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    @staticmethod
    def remove_company_from_group(
        db: Session,
        group_id: UUID,
        company_id: UUID
    ) -> bool:
        """
        Remove a company from a group.
        """
        member = db.query(GroupCompanyMember).filter(
            GroupCompanyMember.group_company_id == group_id,
            GroupCompanyMember.company_id == company_id
        ).first()

        if not member:
            return False

        db.delete(member)
        db.commit()
        return True

    @staticmethod
    def get_group_companies(db: Session, group_id: UUID) -> List[Company]:
        """
        Get all companies in a group.
        """
        members = db.query(GroupCompanyMember).filter(
            GroupCompanyMember.group_company_id == group_id
        ).all()

        company_ids = [member.company_id for member in members]
        return db.query(Company).filter(Company.id.in_(company_ids)).all()

    @staticmethod
    def propagate_mappings(
        db: Session,
        group_id: UUID,
        source_company_id: UUID,
        target_company_id: Optional[UUID] = None,
        force: bool = False
    ) -> dict:
        """
        Propagate account mappings from a source company to other companies in the group.

        Args:
            group_id: The group containing the companies
            source_company_id: Company to copy mappings from
            target_company_id: Optional specific target company (if None, propagates to all)
            force: If True, overwrites existing mappings

        Returns:
            Dictionary with propagation statistics
        """
        # Verify source company is in the group
        source_member = db.query(GroupCompanyMember).filter(
            GroupCompanyMember.group_company_id == group_id,
            GroupCompanyMember.company_id == source_company_id
        ).first()

        if not source_member:
            raise ValueError("Source company is not a member of this group")

        # Get target companies
        if target_company_id:
            # Verify target is in group
            target_member = db.query(GroupCompanyMember).filter(
                GroupCompanyMember.group_company_id == group_id,
                GroupCompanyMember.company_id == target_company_id
            ).first()
            if not target_member:
                raise ValueError("Target company is not a member of this group")
            target_companies = [target_company_id]
        else:
            # Get all companies in group except source
            members = db.query(GroupCompanyMember).filter(
                GroupCompanyMember.group_company_id == group_id,
                GroupCompanyMember.company_id != source_company_id
            ).all()
            target_companies = [m.company_id for m in members]

        # Get source mappings
        source_accounts = db.query(CompanyAccount).filter(
            CompanyAccount.company_id == source_company_id
        ).all()

        source_mappings = db.query(AccountMapping).join(
            CompanyAccount,
            AccountMapping.company_account_id == CompanyAccount.id
        ).filter(
            CompanyAccount.company_id == source_company_id,
            AccountMapping.status.in_(["confirmed", "suggested"])
        ).all()

        # Statistics
        stats = {
            "source_company_id": str(source_company_id),
            "target_companies": len(target_companies),
            "source_mappings": len(source_mappings),
            "created": 0,
            "updated": 0,
            "skipped": 0
        }

        # Build mapping lookup by account code
        mapping_by_code = {}
        for mapping in source_mappings:
            account = db.query(CompanyAccount).filter(
                CompanyAccount.id == mapping.company_account_id
            ).first()
            if account:
                mapping_by_code[account.code] = mapping

        # Propagate to each target company
        for target_company_id in target_companies:
            target_accounts = db.query(CompanyAccount).filter(
                CompanyAccount.company_id == target_company_id
            ).all()

            for target_account in target_accounts:
                # Find corresponding source mapping by account code
                if target_account.code not in mapping_by_code:
                    continue

                source_mapping = mapping_by_code[target_account.code]

                # Check if target account already has a mapping
                existing_mapping = db.query(AccountMapping).filter(
                    AccountMapping.company_account_id == target_account.id
                ).first()

                if existing_mapping:
                    if force:
                        # Update existing mapping
                        existing_mapping.master_code = source_mapping.master_code
                        existing_mapping.confidence = max(0.5, source_mapping.confidence * 0.9)
                        existing_mapping.status = "suggested"
                        existing_mapping.propagated_from = source_company_id
                        existing_mapping.notes = f"Propagated from group company (force=True)"
                        stats["updated"] += 1
                    else:
                        # Skip if not forcing
                        stats["skipped"] += 1
                        continue
                else:
                    # Create new mapping
                    new_mapping = AccountMapping(
                        company_account_id=target_account.id,
                        master_code=source_mapping.master_code,
                        confidence=max(0.5, source_mapping.confidence * 0.9),
                        status="suggested",
                        propagated_from=source_company_id,
                        notes="Propagated from group company"
                    )
                    db.add(new_mapping)
                    stats["created"] += 1

        db.commit()
        return stats
