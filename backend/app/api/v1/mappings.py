"""
Account Mapping API Endpoints
Provides endpoints for managing account mappings between company accounts and master chart
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.db.models.user import User
from app.api.v1.auth import get_current_user
from app.schemas.account_mapping import AccountMapping as AccountMappingSchema, AccountMappingCreate
from app.services.mapping_service import MappingService

router = APIRouter()


# ========================================
# MAPPING CRUD ENDPOINTS
# ========================================

@router.get("", response_model=List[AccountMappingSchema], summary="Get Company Mappings", tags=["Mappings"])
def get_company_mappings(
    company_id: UUID = Query(..., description="Company ID"),
    status: Optional[str] = Query(None, description="Filter by status (suggested, confirmed, rejected, manual_review)"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all mappings for a company with optional filtering.

    **Query Parameters:**
    - company_id: Company UUID (required)
    - status: Filter by status
    - min_confidence: Minimum confidence threshold (0.0 to 1.0)
    """
    service = MappingService(db)
    return service.get_mappings_for_company(
        company_id=company_id,
        status=status,
        min_confidence=min_confidence
    )


@router.get("/{mapping_id}", response_model=AccountMappingSchema, summary="Get Mapping", tags=["Mappings"])
def get_mapping(
    mapping_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific mapping by ID"""
    service = MappingService(db)
    mapping = service.get_mapping_by_id(mapping_id)
    if not mapping:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapping not found")
    return mapping


@router.post("", response_model=AccountMappingSchema, status_code=status.HTTP_201_CREATED, summary="Create Mapping", tags=["Mappings"])
def create_mapping(
    mapping_data: AccountMappingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new account mapping.

    **Request Body Example:**
    ```json
    {
        "company_account_id": "uuid-here",
        "master_code": "1.10.10",
        "confidence": 0.95,
        "status": "suggested",
        "notes": "Auto-suggested mapping"
    }
    ```
    """
    service = MappingService(db)
    try:
        return service.create_mapping(
            company_account_id=mapping_data.company_account_id,
            master_code=mapping_data.master_code,
            confidence=mapping_data.confidence,
            status=mapping_data.status,
            notes=mapping_data.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Mapping", tags=["Mappings"])
def delete_mapping(
    mapping_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a mapping"""
    service = MappingService(db)
    if not service.delete_mapping(mapping_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapping not found")


# ========================================
# SUGGESTION ENDPOINTS
# ========================================

@router.post("/suggest", summary="Suggest Mapping for Account", tags=["Mappings - Suggestions"])
def suggest_mapping(
    company_account_id: UUID = Query(..., description="Company account ID"),
    auto_create: bool = Query(True, description="Automatically create mapping suggestion in DB"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate mapping suggestion for a single company account using AI.

    Uses the master chart service's AI-powered suggestion engine.

    **Returns:**
    - Top 5 suggested master accounts with confidence scores
    - Automatically creates a mapping record if auto_create=True
    """
    service = MappingService(db)
    try:
        return service.suggest_mapping(
            company_account_id=company_account_id,
            auto_create=auto_create
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/suggest-all", summary="Suggest Mappings for Company", tags=["Mappings - Suggestions"])
def suggest_all_mappings(
    company_id: UUID = Query(..., description="Company ID"),
    auto_create: bool = Query(True, description="Automatically create mapping suggestions"),
    only_unmapped: bool = Query(True, description="Only suggest for unmapped accounts"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate mapping suggestions for all accounts in a company.

    **Use Cases:**
    - Initial setup after importing accounts
    - Re-mapping after master chart changes
    - Bulk suggestion generation

    **Returns:**
    - Statistics about suggestions generated
    - List of all suggestions with confidence scores
    """
    service = MappingService(db)
    try:
        return service.suggest_mappings_for_company(
            company_id=company_id,
            auto_create=auto_create,
            only_unmapped=only_unmapped
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========================================
# CONFIRMATION WORKFLOW ENDPOINTS
# ========================================

@router.post("/{mapping_id}/confirm", response_model=AccountMappingSchema, summary="Confirm Mapping", tags=["Mappings - Workflow"])
def confirm_mapping(
    mapping_id: UUID,
    notes: Optional[str] = Query(None, description="Optional notes"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirm a suggested mapping.

    Changes status from 'suggested' to 'confirmed'.
    """
    service = MappingService(db)
    mapping = service.confirm_mapping(mapping_id=mapping_id, notes=notes)
    if not mapping:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapping not found")
    return mapping


@router.post("/{mapping_id}/reject", response_model=AccountMappingSchema, summary="Reject Mapping", tags=["Mappings - Workflow"])
def reject_mapping(
    mapping_id: UUID,
    notes: Optional[str] = Query(None, description="Optional notes about why rejected"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject a suggested mapping.

    Changes status from 'suggested' to 'rejected'.
    """
    service = MappingService(db)
    mapping = service.reject_mapping(mapping_id=mapping_id, notes=notes)
    if not mapping:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapping not found")
    return mapping


@router.post("/{mapping_id}/review", response_model=AccountMappingSchema, summary="Flag for Manual Review", tags=["Mappings - Workflow"])
def flag_for_review(
    mapping_id: UUID,
    notes: Optional[str] = Query(None, description="Optional notes about review needed"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Flag a mapping for manual review.

    Changes status to 'manual_review'.
    """
    service = MappingService(db)
    mapping = service.flag_for_review(mapping_id=mapping_id, notes=notes)
    if not mapping:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapping not found")
    return mapping


# ========================================
# BULK OPERATIONS
# ========================================

@router.post("/confirm-high-confidence", summary="Auto-Confirm High Confidence Mappings", tags=["Mappings - Bulk"])
def confirm_high_confidence(
    company_id: UUID = Query(..., description="Company ID"),
    confidence_threshold: float = Query(0.85, ge=0.0, le=1.0, description="Minimum confidence to auto-confirm"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Automatically confirm all mappings above a confidence threshold.

    **Default threshold:** 0.85 (85% confidence)

    **Use Case:**
    - After generating suggestions, bulk-confirm high-confidence matches
    - Speeds up mapping workflow by auto-confirming obvious matches

    **Returns:**
    - Statistics about confirmed mappings
    """
    service = MappingService(db)
    return service.confirm_all_high_confidence(
        company_id=company_id,
        confidence_threshold=confidence_threshold
    )


# ========================================
# STATISTICS & REPORTING
# ========================================

@router.get("/stats/{company_id}", summary="Get Mapping Statistics", tags=["Mappings - Statistics"])
def get_mapping_stats(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive mapping statistics for a company.

    **Returns:**
    - Total accounts and mappings
    - Breakdown by status (suggested, confirmed, rejected, manual_review)
    - Average confidence score
    - Completion percentage
    """
    service = MappingService(db)
    return service.get_mapping_stats(company_id=company_id)


# ========================================
# SEMANTIC SEARCH (pgvector-based)
# ========================================

@router.get("/semantic-search/{company_account_id}", summary="Find Similar Accounts (Semantic)", tags=["Mappings - Semantic Search"])
def semantic_search(
    company_account_id: UUID,
    limit: int = Query(5, ge=1, le=20, description="Number of results"),
    min_similarity: float = Query(0.5, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Find similar master accounts using semantic search (pgvector).

    **Requirements:**
    - pgvector extension must be enabled in PostgreSQL
    - Embeddings must be generated for accounts

    **Returns:**
    - List of similar master accounts with similarity scores
    - Sorted by similarity (highest first)

    **Use Case:**
    - Find semantically similar accounts regardless of exact keyword matches
    - "Office Supplies" might match "Stationery Expense" even if words differ
    """
    service = MappingService(db)
    return service.find_similar_master_accounts(
        company_account_id=company_account_id,
        limit=limit,
        min_similarity=min_similarity
    )


@router.post("/suggest-blended", summary="Suggest Mapping (AI + Semantic)", tags=["Mappings - Semantic Search"])
def suggest_blended(
    company_account_id: UUID = Query(..., description="Company account ID"),
    auto_create: bool = Query(True, description="Auto-create mapping suggestion"),
    use_semantic: bool = Query(True, description="Use semantic search"),
    semantic_weight: float = Query(0.3, ge=0.0, le=1.0, description="Weight for semantic vs AI"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enhanced mapping suggestion that blends AI and semantic search.

    **Blending Strategy:**
    - AI suggestions use rule-based matching and ML classification
    - Semantic search uses vector embeddings for similarity
    - Results are combined with weighted scoring

    **Parameters:**
    - semantic_weight: 0.3 means 30% semantic, 70% AI
    - Higher semantic_weight favors meaning over keywords

    **Returns:**
    - Blended suggestions with both AI and semantic scores
    - Top match for auto-creation
    - Method indicator (blended, ai_only, semantic_only)
    """
    service = MappingService(db)
    try:
        return service.suggest_mapping_with_embeddings(
            company_account_id=company_account_id,
            auto_create=auto_create,
            use_semantic=use_semantic,
            semantic_weight=semantic_weight
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========================================
# GROUP PROPAGATION (for multi-company setups)
# ========================================

@router.post("/propagate", summary="Propagate Mappings to Group", tags=["Mappings - Group Operations"])
def propagate_mappings(
    source_company_id: UUID = Query(..., description="Source company ID"),
    target_company_ids: List[UUID] = Query(..., description="Target company IDs"),
    only_confirmed: bool = Query(True, description="Only propagate confirmed mappings"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Propagate mappings from one company to others in a group.

    **Use Case:**
    - Bob has 8 companies with similar chart structures
    - Map accounts for Company A
    - Propagate those mappings to Companies B-H automatically

    **How it works:**
    1. Gets confirmed mappings from source company
    2. Finds matching accounts in target companies (by account code)
    3. Creates suggested mappings in target companies
    4. Tracks propagation source for audit trail

    **Returns:**
    - Statistics about propagation (how many propagated, skipped)
    """
    service = MappingService(db)
    return service.propagate_mappings_to_group(
        source_company_id=source_company_id,
        target_company_ids=target_company_ids,
        only_confirmed=only_confirmed
    )
