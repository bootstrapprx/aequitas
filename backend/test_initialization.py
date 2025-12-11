"""
Test script to debug master chart and company initialization issues.
"""
import sys
from app.db.session import SessionLocal
from app.db.models.master_account import MasterAccount
from app.db.models.company import Company
from app.db.models.company_account import CompanyAccount
from app.services.companychart_service import CompanyChartService

def main():
    db = SessionLocal()

    print("="*60)
    print("DEBUGGING CHART OF ACCOUNTS INITIALIZATION")
    print("="*60)

    # Check 1: Master Chart
    print("\n1. Checking Master Chart...")
    master_count = db.query(MasterAccount).count()
    print(f"   Total master accounts: {master_count}")

    if master_count == 0:
        print("   ❌ ERROR: Master chart is empty!")
        print("   Run: python -m app.data.seed_enriched_master_chart")
        return
    else:
        print(f"   ✓ Master chart loaded with {master_count} accounts")
        # Show sample
        sample = db.query(MasterAccount).limit(3).all()
        for acc in sample:
            print(f"      - {acc.code}: {acc.description}")

    # Check 2: Companies
    print("\n2. Checking Companies...")
    companies = db.query(Company).filter(Company.is_active == True).all()
    print(f"   Total active companies: {len(companies)}")

    if len(companies) == 0:
        print("   ⚠ No companies found to test")
        return

    # Check 3: Company Accounts
    print("\n3. Checking Company Accounts...")
    for company in companies:
        company_accounts = db.query(CompanyAccount).filter(
            CompanyAccount.company_id == company.id
        ).count()
        print(f"   Company: {company.name} ({company.ucid})")
        print(f"      Accounts: {company_accounts}")

        if company_accounts == 0:
            print(f"      ❌ No accounts! Attempting to initialize...")
            try:
                service = CompanyChartService(db)
                result = service.initialize_from_master_chart(company.id)
                print(f"      ✓ Initialized: {result}")
            except Exception as e:
                print(f"      ❌ Failed to initialize: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print(f"      ✓ Has accounts")
            # Show sample
            sample_accounts = db.query(CompanyAccount).filter(
                CompanyAccount.company_id == company.id
            ).limit(3).all()
            for acc in sample_accounts:
                print(f"         - {acc.code}: {acc.description}")

    print("\n" + "="*60)
    print("DIAGNOSIS COMPLETE")
    print("="*60)

    db.close()

if __name__ == "__main__":
    main()
