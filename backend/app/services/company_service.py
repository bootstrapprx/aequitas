from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from app.db.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.core.ucid import generate_ucid

class CompanyService:
    @staticmethod
    def create_company(db: Session, company_in: CompanyCreate) -> Company:
        """
        Creates a new company with a unique UCID.
        If a company with the same UCID exists but is inactive, it restores it if the name matches.
        """
        # Generate UCID
        ucid = generate_ucid(company_in.name)
        
        # Check for existing company with same UCID (active or inactive)
        existing_company = db.query(Company).filter(Company.ucid == ucid).first()
        
        if existing_company:
            if existing_company.is_active:
                # Active collision
                if existing_company.name == company_in.name:
                    return existing_company
                else:
                    raise ValueError(f"UCID collision detected for {company_in.name} (UCID: {ucid}). Please contact support.")
            else:
                # Inactive collision - Check if name matches (normalized check implicit by UCID match)
                # But let's check exact name or just assume reuse?
                # Prompt: "If the normalized legal name is the same, reuse UCID"
                # Since UCID is derived from normalized name, if UCID matches, normalized name matches.
                # So we can reuse/restore.
                
                # Reactivate and update details
                existing_company.is_active = True
                # Update other fields
                update_data = company_in.model_dump(exclude_unset=True)
                for field, value in update_data.items():
                    setattr(existing_company, field, value)
                
                db.commit()
                db.refresh(existing_company)
                return existing_company

        db_company = Company(
            name=company_in.name,
            ucid=ucid,
            email=company_in.email,
            phone=company_in.phone,
            website=company_in.website,
            address_line1=company_in.address_line1,
            address_line2=company_in.address_line2,
            city=company_in.city,
            state=company_in.state,
            postal_code=company_in.postal_code,
            country=company_in.country,
            tax_id=company_in.tax_id,
            industry=company_in.industry,
            description=company_in.description,
            is_active=True,
            subscription_type=company_in.subscription_type
        )
        db.add(db_company)
        db.commit()
        db.refresh(db_company)

        # Auto-initialize chart of accounts from master chart
        from app.services.companychart_service import CompanyChartService
        import logging
        logger = logging.getLogger(__name__)

        chart_service = CompanyChartService(db)
        try:
            logger.info(f"Initializing chart of accounts for company {db_company.ucid}...")
            result = chart_service.initialize_from_master_chart(db_company.id)
            logger.info(f"✓ Chart of accounts initialized: {result['accounts_created']} accounts created")
            print(f"✓ Company {db_company.ucid}: Chart of accounts initialized with {result['accounts_created']} accounts")
        except Exception as e:
            # Log the error but don't fail company creation
            logger.error(f"Failed to initialize chart of accounts for company {db_company.ucid}: {str(e)}")
            print(f"❌ Warning: Failed to initialize chart of accounts for company {db_company.ucid}")
            print(f"   Error: {str(e)}")
            print(f"   This company will need to have its chart initialized manually.")
            import traceback
            traceback.print_exc()

        return db_company

    @staticmethod
    def get_company_by_ucid(db: Session, ucid: str) -> Optional[Company]:
        return db.query(Company).filter(Company.ucid == ucid).first()
    
    @staticmethod
    def get_company_by_id(db: Session, company_id: UUID) -> Optional[Company]:
        return db.query(Company).filter(Company.id == company_id).first()
    
    @staticmethod
    def get_all_companies(db: Session, active_only: bool = True) -> list[Company]:
        query = db.query(Company)
        if active_only:
            query = query.filter(Company.is_active == True)
        return query.all()
    
    @staticmethod
    def update_company(db: Session, company_id: UUID, company_update: CompanyUpdate) -> Optional[Company]:
        """
        Updates an existing company.
        """
        company = CompanyService.get_company_by_id(db, company_id)
        if not company:
            return None
        
        # Update only provided fields
        update_data = company_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(company, field, value)
        
        db.commit()
        db.refresh(company)
        return company
    
    @staticmethod
    def inactivate_company(db: Session, ucid: str, confirmation: str, user_id: Optional[str] = None) -> Company:
        """
        Inactivates a company after confirming the name matches.
        """
        company = CompanyService.get_company_by_ucid(db, ucid)
        if not company:
            raise ValueError("Company not found")
        
        if company.name != confirmation:
            raise ValueError("Confirmation name does not match company name")
            
        if not company.is_active:
            return company # Already inactive

        company.is_active = False
        company.inactivated_at = datetime.utcnow()
        company.inactivated_by = user_id
        
        db.commit()
        db.refresh(company)
        
        # Log audit
        from app.services.audit_service import AuditService
        AuditService.log_event(
            db=db,
            action="COMPANY_INACTIVATE",
            entity_type="company",
            entity_id=ucid,
            user_id=user_id,
            payload={"name": company.name}
        )
        
        return company

    @staticmethod
    def activate_company(db: Session, ucid: str, confirmation: str, user_id: Optional[str] = None) -> Company:
        """
        Activates a company after confirming the name matches.
        """
        company = db.query(Company).filter(Company.ucid == ucid).first()
        if not company:
            raise ValueError("Company not found")
            
        if company.name != confirmation:
             raise ValueError("Confirmation name does not match company name")

        if company.is_active:
            return company # Already active
            
        company.is_active = True
        company.inactivated_at = None
        company.inactivated_by = None
        
        db.commit()
        db.refresh(company)
        
        # Log audit
        from app.services.audit_service import AuditService
        AuditService.log_event(
            db=db,
            action="COMPANY_ACTIVATE",
            entity_type="company",
            entity_id=ucid,
            user_id=user_id,
            payload={"name": company.name}
        )
        
        return company

    @staticmethod
    def delete_company(db: Session, company_id: UUID) -> bool:
        """
        Hard deletes a company (Admin only, or deprecated in favor of inactivation).
        For now, we keep it but maybe restricted.
        """
        company = CompanyService.get_company_by_id(db, company_id)
        if not company:
            return False
        
        db.delete(company)
        db.commit()
        return True
