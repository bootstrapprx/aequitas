from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.schemas.master_account import (
    MasterAccountSchema,
    MasterAccountCreate,
    MasterAccountUpdate,
    MasterAccountTree,
)
from app.services.masterchart_service import MasterChartService
from app.services.code_generator.service import CodeGeneratorService
from app.services.code_generator.exceptions import CodeGenerationException

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
def create_master_account(account_in: MasterAccountCreate, db: Session = Depends(get_db)):
    """
    Creates a new master account. If the `code` is omitted, it will be auto-generated.
    If `parent_code` is provided in the request body, the new account will be a child of that parent.
    """
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
def rebuild_master_chart_hierarchy(db: Session = Depends(get_db)):
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
def update_master_account(code: str, account_in: MasterAccountUpdate, db: Session = Depends(get_db)):
    service = MasterChartService(db)
    try:
        updated_account = service.update_account(code, account_in)
        if not updated_account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        return updated_account
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Account", tags=["Master Chart"])
def delete_master_account(code: str, db: Session = Depends(get_db)):
    service = MasterChartService(db)
    try:
        if not service.delete_account(code):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
