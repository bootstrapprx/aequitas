"""
Template catalog schemas.

These models describe the enriched account catalog exposed to users as an optional selection list.
"""
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class CatalogAccount(BaseModel):
    id: str
    code: str
    description: str
    long_description: Optional[str] = None
    type: str
    category: str
    level: int
    parent_code: Optional[str] = None
    normal_balance: Optional[str] = None
    fs_mapping: Optional[str] = None
    cash_flow_classification: Optional[str] = None
    notes: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    tags: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


class CatalogAccountTree(CatalogAccount):
    children: List["CatalogAccountTree"] = []


class CatalogStats(BaseModel):
    total_accounts: int
    header_count: int
    detail_count: int
    max_depth: int
    orphans: int
    missing_parents: List[str]
    needs_rebuild: bool

