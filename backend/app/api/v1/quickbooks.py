"""Deprecated QuickBooks compatibility routes.

The maintained integration lives in :mod:`app.api.v1.qbo`. These legacy routes
are deliberately unavailable so they cannot bypass the authenticated, scoped
integration flow.
"""
from fastapi import APIRouter, HTTPException, status

router = APIRouter()


def _deprecated() -> None:
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="This QuickBooks route is retired. Use /api/v1/qbo instead.",
    )


@router.get("/quickbooks/authorize", deprecated=True)
def authorize_quickbooks() -> None:
    _deprecated()


@router.get("/quickbooks/callback", deprecated=True)
def quickbooks_callback() -> None:
    _deprecated()


@router.get("/quickbooks/accounts", deprecated=True)
def get_qbo_accounts() -> None:
    _deprecated()
