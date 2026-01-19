from typing import List, Optional

from fastapi import APIRouter, Query

from app.schemas.catalog import CatalogAccount, CatalogAccountTree, CatalogStats
from app.services.template_catalog_service import TemplateCatalogService


router = APIRouter()


@router.get("/accounts", response_model=List[CatalogAccount], summary="List Template Catalog Accounts")
def list_catalog_accounts(
    search: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    account_type: Optional[str] = Query(default=None),
    normal_balance: Optional[str] = Query(default=None),
):
    service = TemplateCatalogService()
    accounts = service.get_accounts()

    if search:
        search_lower = search.lower()
        accounts = [
            account
            for account in accounts
            if search_lower in account["code"].lower()
            or search_lower in account["description"].lower()
        ]

    if category:
        accounts = [account for account in accounts if account["category"] == category]

    if account_type:
        accounts = [account for account in accounts if account["type"] == account_type.upper()]

    if normal_balance:
        accounts = [
            account
            for account in accounts
            if (account.get("normal_balance") or "").lower() == normal_balance.lower()
        ]

    return accounts


@router.get("/tree", response_model=List[CatalogAccountTree], summary="Get Template Catalog Tree")
def get_catalog_tree():
    service = TemplateCatalogService()
    accounts = service.get_accounts()
    return service.build_tree(accounts)


@router.get("/stats", response_model=CatalogStats, summary="Get Template Catalog Stats")
def get_catalog_stats():
    service = TemplateCatalogService()
    accounts = service.get_accounts()
    return service.get_stats(accounts)


__all__ = ["router"]
