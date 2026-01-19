"""
User Context Schemas

Provides authoritative context for dashboard hydration.
Canon II: Backend Creates Truth - UI must not infer state.
"""

from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class UserContextResponse(BaseModel):
    """
    Authoritative user context for dashboard rendering.
    
    This is the ONLY source of truth for:
    - Current company identity
    - Accounting activation status
    - Kernel compliance state
    - Protected structure status
    
    UI must NOT infer any of these from side effects.
    """
    # User identity
    user_id: UUID
    email: str
    full_name: Optional[str] = None
    
    # Current company (THE OPERATIONAL CONTEXT)
    current_company_id: Optional[UUID] = None
    current_company_name: Optional[str] = None
    current_company_ucid: Optional[str] = None
    total_companies: int
    
    # Accounting activation state (CANONICAL)
    accounting_active: bool  # True = onboarding complete + activated
    onboarding_status: Optional[str] = None  # DRAFT | ACTIVE, etc.
    
    # Kernel binding state (CANONICAL)
    kernel_version: Optional[str] = None  # e.g., "2025.2"
    kernel_layer: Optional[str] = None    # L0 | L1 | L2
    protected_structure: bool  # True = kernel-bound + accounts locked
    
    # Chart state
    total_accounts: int  # From backend count, not inferred
    
    # Fiscal state
    open_periods: int  # Count of OPEN fiscal periods
    
    class Config:
        from_attributes = True
