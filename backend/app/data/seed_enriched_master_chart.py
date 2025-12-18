"""
Enriched US-GAAP Master Chart Seed Data
Loads the complete enriched master chart with AI-ready fields

Total Accounts: 345
- Category Headers: 7
- Detail Accounts: 338

Enhanced Fields:
- long_description: Professional IFRS/GAAP explanations
- fs_mapping: Balance Sheet or Income Statement classification
- tags: AI-friendly keywords for classification
- default_vendors: Common vendor associations
- regulatory_mapping: IFRS/IPSAS/ASC standard references
- normal_balance: Debit or Credit
- cash_flow_classification: Operating, Investing, or Financing
- cost_center: Default cost center assignment

Date: 2025-12-01

UPDATED: 2025-12-11
- Added validation using MasterChartValidator
- Added normalization using MasterChartNormalizer
- Improved error reporting
- Made idempotent with force_reload option
"""

import json
import csv
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models.master_account import MasterAccount
from app.db.session import SessionLocal
from app.core.validators.master_chart_validator import MasterChartValidator
from app.core.normalizers.master_chart_normalizer import MasterChartNormalizer
import os

def load_enriched_master_chart(
    db: Session,
    force_reload: bool = False,
    validate: bool = True,
    normalize: bool = True
):
    """
    Load the enriched US-GAAP master chart of accounts into the database.
    This includes 345 accounts with full IFRS/GAAP compliance and AI-ready fields.

    Args:
        db: Database session
        force_reload: If True, delete existing accounts and reload
        validate: If True, validate all accounts before loading (default: True)
        normalize: If True, normalize account names and descriptions (default: True)

    Returns:
        dict: Status information including loaded count and any errors
    """

    # Initialize validator and normalizer
    validator = MasterChartValidator()
    normalizer = MasterChartNormalizer()

    # Determine the path to the CSV file
    data_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(data_dir, 'enriched_master_chart.csv')

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Enriched master chart CSV not found at {csv_path}")

    print(f"Loading enriched master chart from {csv_path}...")

    # Check if accounts already exist (IDEMPOTENT)
    existing_count = db.query(MasterAccount).count()
    if existing_count > 0 and not force_reload:
        print(f"  ✓ Master chart already loaded ({existing_count} accounts).")
        print(f"    Use force_reload=True to reload.")
        return {
            "status": "skipped",
            "message": "Master chart already exists",
            "existing_count": existing_count,
            "loaded_count": 0
        }

    if force_reload and existing_count > 0:
        print(f"  ⚠ Force reload: Deleting {existing_count} existing accounts...")
        db.query(MasterAccount).delete()
        db.commit()
    
    # Load the CSV data
    accounts_data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        accounts_data = list(reader)

    print(f"Found {len(accounts_data)} accounts in CSV...")

    # Map description to account_name for validator compatibility
    for account in accounts_data:
        if 'description' in account and 'account_name' not in account:
            account['account_name'] = account['description']

    # Validate entire chart structure if validation is enabled
    if validate:
        print(f"  Validating chart structure...")
        validation_result = validator.validate_chart(accounts_data)
        if not validation_result.is_valid:
            print(f"  ✗ Chart validation failed with {len(validation_result.errors)} error(s):")
            for error in validation_result.errors[:5]:  # Show first 5 errors
                print(f"    - {error}")
            if len(validation_result.errors) > 5:
                print(f"    ... and {len(validation_result.errors) - 5} more errors")
            raise ValueError(f"Master chart validation failed: {len(validation_result.errors)} errors")

        if validation_result.warnings:
            print(f"  ⚠ {len(validation_result.warnings)} warning(s) found")
        else:
            print(f"  ✓ Chart validation passed")

    # First pass: Create all accounts without parent relationships
    code_to_id_map = {}
    loaded_count = 0
    skipped_count = 0
    validation_warnings = []

    for account_data in accounts_data:
        try:
            # Skip duplicates
            if account_data['code'] in code_to_id_map:
                print(f"  Skipping duplicate account code: {account_data['code']}")
                continue

            # Parse dates
            start_date_str = account_data.get('start_date', '').strip()
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            else:
                # Default to 2024-01-01 if start_date is missing
                start_date = datetime(2024, 1, 1).date()

            end_date = None
            if account_data.get('end_date') and account_data['end_date'].strip():
                end_date = datetime.strptime(account_data['end_date'], '%Y-%m-%d').date()
            
            # Parse tags (comma-separated string to list)
            tags = None
            if account_data.get('tags') and account_data['tags'].strip():
                tags = [tag.strip() for tag in account_data['tags'].split(',')]
            
            # Parse default_vendors (comma-separated string to list)
            default_vendors = None
            if account_data.get('default_vendors') and account_data['default_vendors'].strip():
                default_vendors = [v.strip() for v in account_data['default_vendors'].split(',')]
            
            # Parse regulatory_mapping (JSON string to dict)
            regulatory_mapping = None
            if account_data.get('regulatory_mapping') and account_data['regulatory_mapping'].strip():
                try:
                    regulatory_mapping = json.loads(account_data['regulatory_mapping'])
                except json.JSONDecodeError:
                    print(f"  Warning: Invalid JSON in regulatory_mapping for {account_data['code']}")
                    regulatory_mapping = {}

            # Normalize account data if normalization is enabled
            if normalize:
                account_data['description'] = normalizer.normalize_account_name(account_data['description'])
                if account_data.get('long_description'):
                    account_data['long_description'] = normalizer.normalize_description(account_data['long_description'])
                if account_data.get('category'):
                    account_data['category'] = normalizer.normalize_category(account_data['category'])
                if account_data.get('fs_mapping'):
                    account_data['fs_mapping'] = normalizer.normalize_fs_mapping(account_data['fs_mapping'])
                if account_data.get('normal_balance'):
                    account_data['normal_balance'] = normalizer.normalize_normal_balance(account_data['normal_balance'])

            # Create account with all enriched fields
            account = MasterAccount(
                code=account_data['code'],
                description=account_data['description'],
                start_date=start_date,
                end_date=end_date,
                type='H' if account_data['type'] == 'Header' else 'D',
                level=int(account_data.get('level', 0)),  # Default to 0 if missing
                category=account_data['category'],
                notes=account_data.get('notes'),
                parent_code=account_data.get('parent_code') if account_data.get('parent_code') else None,
                # Enriched fields
                long_description=account_data.get('long_description'),
                fs_mapping=account_data.get('fs_mapping'),
                tags=tags,
                default_vendors=default_vendors,
                regulatory_mapping=regulatory_mapping,
                normal_balance=account_data.get('normal_balance'),
                cash_flow_classification=account_data.get('cash_flow_classification'),
                cost_center=account_data.get('cost_center'),
                version=account_data.get('version', '2024.1'),
            )
            
            db.add(account)
            db.flush()  # Get the ID without committing
            
            code_to_id_map[account_data['code']] = account.id
            loaded_count += 1
            
            if loaded_count % 50 == 0:
                print(f"  Loaded {loaded_count} accounts...")
        
        except Exception as e:
            print(f"  Error loading account {account_data.get('code', 'UNKNOWN')}: {e}")
            skipped_count += 1
            continue
    
    print(f"  First pass complete: {loaded_count} accounts loaded, {skipped_count} skipped")
    
    # Second pass: Set parent_id relationships
    print("  Setting parent relationships...")
    parent_count = 0
    
    for account_data in accounts_data:
        if account_data.get('parent_code') and account_data['parent_code'].strip():
            account = db.query(MasterAccount).filter(
                MasterAccount.code == account_data['code']
            ).first()
            
            if account and account_data['parent_code'] in code_to_id_map:
                account.parent_id = code_to_id_map[account_data['parent_code']]
                parent_count += 1
    
    print(f"  Set {parent_count} parent relationships")
    
    # Commit all changes
    db.commit()

    print(f"\n✓ Successfully loaded {loaded_count} accounts")

    # Return detailed status
    return {
        "status": "success",
        "loaded_count": loaded_count,
        "skipped_count": skipped_count,
        "validation_warnings": len(validation_warnings) if validate else 0
    }
    
    # Print summary statistics
    headers = db.query(MasterAccount).filter(MasterAccount.type == 'H').count()
    details = db.query(MasterAccount).filter(MasterAccount.type == 'D').count()
    
    # Count by category
    categories = db.query(MasterAccount.category, func.count(MasterAccount.id)).group_by(MasterAccount.category).all()
    
    # Count accounts with vendors
    with_vendors = db.query(MasterAccount).filter(MasterAccount.default_vendors.isnot(None)).count()
    
    # Count accounts with tags
    with_tags = db.query(MasterAccount).filter(MasterAccount.tags.isnot(None)).count()
    
    print(f"\n{'='*60}")
    print(f"ENRICHED MASTER CHART SUMMARY")
    print(f"{'='*60}")
    print(f"  Header accounts: {headers}")
    print(f"  Detail accounts: {details}")
    print(f"  Total accounts: {headers + details}")
    print(f"\n  Accounts by Category:")
    for category, count in sorted(categories, key=lambda x: x[1], reverse=True):
        print(f"    {category}: {count}")
    print(f"\n  Enrichment Coverage:")
    print(f"    Accounts with vendor mappings: {with_vendors}")
    print(f"    Accounts with AI tags: {with_tags}")
    print(f"    Accounts with long descriptions: {details}")  # All detail accounts have long descriptions
    print(f"{'='*60}\n")
    
    return True


def get_master_chart_as_objects(db: Session):
    """
    Retrieve all master accounts as Python objects for AI interaction.
    Returns a list of MasterAccount objects optimized for DEXTER.
    """
    accounts = db.query(MasterAccount).order_by(MasterAccount.code).all()
    return accounts


def get_master_chart_for_ai(db: Session):
    """
    Retrieve master chart in AI-friendly format for DEXTER.
    Returns a list of simplified dicts optimized for AI processing.
    """
    accounts = db.query(MasterAccount).order_by(MasterAccount.code).all()
    return [account.to_ai_context() for account in accounts]


def search_accounts_by_keywords(db: Session, keywords: list[str]):
    """
    Search master accounts by keywords.
    Useful for AI-powered account suggestion.
    """
    accounts = db.query(MasterAccount).filter(MasterAccount.type == 'D').all()
    matches = [acc for acc in accounts if acc.matches_keywords(keywords)]
    return matches


def search_accounts_by_vendor(db: Session, vendor_name: str):
    """
    Find accounts associated with a specific vendor.
    Useful for automatic account suggestion based on vendor.
    """
    accounts = db.query(MasterAccount).filter(
        MasterAccount.default_vendors.isnot(None)
    ).all()
    matches = [acc for acc in accounts if acc.matches_vendor(vendor_name)]
    return matches


if __name__ == "__main__":
    db = SessionLocal()
    try:
        load_enriched_master_chart(db, force_reload=False)
        
        # Test AI interaction functions
        print("\n" + "="*60)
        print("TESTING AI INTERACTION FUNCTIONS")
        print("="*60)
        
        # Test keyword search
        print("\n1. Testing keyword search for 'software'...")
        matches = search_accounts_by_keywords(db, ['software', 'computer'])
        print(f"   Found {len(matches)} matching accounts:")
        for acc in matches[:5]:  # Show first 5
            print(f"   - {acc.code}: {acc.description}")
        
        # Test vendor search
        print("\n2. Testing vendor search for 'AWS'...")
        matches = search_accounts_by_vendor(db, 'AWS')
        print(f"   Found {len(matches)} matching accounts:")
        for acc in matches[:5]:  # Show first 5
            print(f"   - {acc.code}: {acc.description}")
            if acc.default_vendors:
                print(f"     Vendors: {', '.join(acc.default_vendors[:3])}")
        
        # Test AI context
        print("\n3. Testing AI context generation...")
        ai_accounts = get_master_chart_for_ai(db)
        print(f"   Generated AI context for {len(ai_accounts)} accounts")
        print(f"   Sample account:")
        if ai_accounts:
            import json
            print(json.dumps(ai_accounts[0], indent=2))
        
        print("\n" + "="*60)
        print("AI INTERACTION TESTS COMPLETE")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
