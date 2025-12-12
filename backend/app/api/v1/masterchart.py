from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.db.models.user import User
from app.api.v1.auth import get_current_user
from app.core.security import check_superuser
from app.schemas.master_account import (
    MasterAccountSchema,
    MasterAccountCreate,
    MasterAccountUpdate,
    MasterAccountTree,
)
from app.services.master_chart_service import MasterChartService
from app.services.code_generator.service import CodeGeneratorService
from app.services.code_generator.exceptions import CodeGenerationException
from app.core.validators.master_chart_validator import MasterChartValidator
from app.core.normalizers.master_chart_normalizer import MasterChartNormalizer

router = APIRouter()

# --- Master Chart CRUD Endpoints ---

@router.get("", response_model=List[MasterAccountSchema], summary="Get Master Chart List", tags=["Master Chart"])
def get_master_chart_list(
    search: Optional[str] = None,
    category: Optional[str] = None,
    account_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all master accounts with optional filtering.
    
    Query parameters:
    - search: Search in code and description
    - category: Filter by category
    - account_type: Filter by type ('H' for Header, 'D' for Detail)
    """
    service = MasterChartService(db)
    accounts = service.get_all_accounts()
    
    # Apply filters
    if search:
        search_lower = search.lower()
        accounts = [
            acc for acc in accounts
            if search_lower in acc.code.lower() or search_lower in acc.description.lower()
        ]
    
    if category:
        accounts = [acc for acc in accounts if acc.category == category]
    
    if account_type:
        accounts = [acc for acc in accounts if acc.type == account_type.upper()]
    
    return accounts

@router.post("", response_model=MasterAccountSchema, status_code=status.HTTP_201_CREATED, summary="Create Account", tags=["Master Chart"])
def create_master_account(
    account_in: MasterAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new master account. If the `code` is omitted, it will be auto-generated.
    If `parent_code` is provided in the request body, the new account will be a child of that parent.

    **Requires superuser privileges.**
    """
    check_superuser(current_user)

    service = MasterChartService(db)
    try:
        return service.create_account(account_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CodeGenerationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Code Generation Error: {e}")

@router.get("/tree", response_model=List[MasterAccountTree], summary="Get Master Chart as Tree", tags=["Master Chart"])
def get_master_chart_tree(db: Session = Depends(get_db)):
    service = MasterChartService(db)
    accounts = service.get_all_accounts()
    return service.build_tree(accounts)

@router.get("/stats", summary="Get CoA Statistics", tags=["Master Chart"])
def get_chart_statistics(db: Session = Depends(get_db)):
    service = MasterChartService(db)
    return service.get_coa_stats()

@router.post("/rebuild-hierarchy", summary="Rebuild Hierarchy", tags=["Master Chart"])
def rebuild_master_chart_hierarchy(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Rebuild the master chart hierarchy.

    **Requires superuser privileges.**
    """
    check_superuser(current_user)

    service = MasterChartService(db)
    service.rebuild_hierarchy()
    return {"status": "success", "message": "Hierarchy rebuilt successfully."}

@router.get("/categories", summary="Get All Categories", tags=["Master Chart"])
def get_categories(db: Session = Depends(get_db)):
    """Get all unique categories from master accounts."""
    service = MasterChartService(db)
    return service.get_categories()

@router.get("/{code}", response_model=MasterAccountSchema, summary="Get Account by Code", tags=["Master Chart"])
def get_master_account(code: str, db: Session = Depends(get_db)):
    service = MasterChartService(db)
    account = service.get_account_by_code(code)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account

@router.get("/id/{account_id}", response_model=MasterAccountSchema, summary="Get Account by ID", tags=["Master Chart"])
def get_master_account_by_id(account_id: UUID, db: Session = Depends(get_db)):
    service = MasterChartService(db)
    account = service.get_account_by_id(account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account

@router.put("/{code}", response_model=MasterAccountSchema, summary="Update Account", tags=["Master Chart"])
def update_master_account(
    code: str,
    account_in: MasterAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a master account.

    **Requires superuser privileges.**
    """
    check_superuser(current_user)

    service = MasterChartService(db)
    try:
        updated_account = service.update_account(code, account_in)
        if not updated_account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        return updated_account
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Account", tags=["Master Chart"])
def delete_master_account(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a master account.

    **Requires superuser privileges.**
    """
    check_superuser(current_user)

    service = MasterChartService(db)
    try:
        if not service.delete_account(code):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# --- Validation & Normalization Endpoints ---

@router.post("/validate", summary="Validate Account Data", tags=["Master Chart - Validation"])
def validate_account(
    account_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Validate a single account's data structure and business rules.

    Returns validation result with any errors or warnings.

    **Example request body:**
    ```json
    {
        "code": "1.10.10",
        "account_name": "Cash",
        "type": "D",
        "category": "Asset",
        "normal_balance": "Debit",
        "fs_mapping": "Balance Sheet"
    }
    ```
    """
    validator = MasterChartValidator()
    result = validator.validate_account(account_data)

    return {
        "is_valid": result.is_valid,
        "errors": result.errors,
        "warnings": result.warnings,
        "status": str(result)
    }


@router.post("/validate-chart", summary="Validate Entire Chart", tags=["Master Chart - Validation"])
def validate_chart(
    accounts: List[Dict[str, Any]] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Validate an entire chart of accounts for consistency and integrity.

    Checks for:
    - Duplicate codes
    - Orphaned accounts (missing parents)
    - Circular dependencies
    - Invalid account data

    **Example request body:**
    ```json
    [
        {"code": "1", "account_name": "Assets", "type": "H", ...},
        {"code": "1.10", "account_name": "Current Assets", "type": "H", "parent_code": "1", ...}
    ]
    ```
    """
    validator = MasterChartValidator()
    result = validator.validate_chart(accounts)

    return {
        "is_valid": result.is_valid,
        "errors": result.errors,
        "warnings": result.warnings,
        "total_accounts": len(accounts),
        "status": str(result)
    }


@router.get("/validate-integrity", summary="Validate Master Chart Integrity", tags=["Master Chart - Validation"])
def validate_master_chart_integrity(db: Session = Depends(get_db)):
    """
    Validate the integrity of the current master chart in the database.

    Returns:
    - Validation status
    - List of errors (if any)
    - List of warnings
    - Statistics about the chart
    """
    service = MasterChartService(db)
    validator = MasterChartValidator()

    # Get all accounts as dictionaries
    accounts = service.get_all_accounts()
    accounts_data = []
    for acc in accounts:
        accounts_data.append({
            "code": acc.code,
            "account_name": acc.description,
            "type": acc.type,
            "category": acc.category,
            "normal_balance": acc.normal_balance,
            "fs_mapping": acc.fs_mapping,
            "parent_code": acc.parent_code
        })

    # Validate
    result = validator.validate_chart(accounts_data)

    # Get stats
    stats = service.get_coa_stats()

    return {
        "is_valid": result.is_valid,
        "errors": result.errors,
        "warnings": result.warnings,
        "statistics": stats,
        "status": str(result)
    }


@router.post("/normalize", summary="Normalize Account Data", tags=["Master Chart - Normalization"])
def normalize_account_data(
    account_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Normalize account data according to Bob's OCD-level capitalization rules.

    Returns the normalized account data.

    **Example request body:**
    ```json
    {
        "account_name": "accounts payable",
        "category": "liability",
        "fs_mapping": "balance sheet",
        "normal_balance": "cr"
    }
    ```

    **Example response:**
    ```json
    {
        "account_name": "Accounts Payable",
        "category": "Liability",
        "fs_mapping": "Balance Sheet",
        "normal_balance": "Credit"
    }
    ```
    """
    normalizer = MasterChartNormalizer()
    normalized = normalizer.normalize_account_data(account_data)

    return {
        "original": account_data,
        "normalized": normalized
    }


@router.post("/normalize-batch", summary="Normalize Multiple Accounts", tags=["Master Chart - Normalization"])
def normalize_accounts_batch(
    accounts: List[Dict[str, Any]] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Normalize multiple accounts in a batch operation.

    Returns list of normalized accounts.
    """
    normalizer = MasterChartNormalizer()
    normalized_accounts = [normalizer.normalize_account_data(acc) for acc in accounts]

    return {
        "total_accounts": len(accounts),
        "normalized": normalized_accounts
    }
