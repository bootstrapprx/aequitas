from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status, Query
from sqlalchemy.orm import Session

from app.core.errors import AequitasError
from app.db.session import get_db
from app.integrations.qbo.auth import QBOAuthService
from app.integrations.qbo.accounts_import import QBOAccountsImportService
from app.integrations.qbo.accounts_export import QBOAccountsExportService
from app.integrations.qbo.reconcile import QBOReconciliationService
from app.services.idempotency_service import IdempotencyService

router = APIRouter()

# --- AUTHENTICATION ---

@router.get("/auth/url", summary="Get QuickBooks Authorization URL")
def get_qbo_authorization_url(db: Session = Depends(get_db)):
    service = QBOAuthService(db)
    return {"authorization_url": service.get_authorization_url()}

@router.post("/auth/callback", summary="Handle QBO OAuth2 Callback")
def handle_qbo_callback(
    company_id: UUID = Query(...),
    code: str = Query(...),
    realmId: str = Query(...),
    db: Session = Depends(get_db)
):
    service = QBOAuthService(db)
    try:
        token = service.exchange_code_for_tokens(company_id=company_id, authorization_code=code, realm_id=realmId)
        return {"message": "QuickBooks authorization successful.", "realm_id": token.realm_id}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to exchange token: {e}")

# --- DATA SYNC ---

@router.get("/{company_id}/import", summary="Import Chart of Accounts from QBO")
def import_qbo_chart_of_accounts(
    company_id: UUID,
    request: Request,
    idempotency_key: str = Header(None, alias="X-Aequitas-Idempotency-Key"),
    db: Session = Depends(get_db),
):
    if not idempotency_key:
        raise AequitasError(
            code="AEQ_QBO_IDEMPOTENCY_REQUIRED",
            message="X-Aequitas-Idempotency-Key header is required for this endpoint.",
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    idempotency_service = IdempotencyService(db)
    endpoint_identifier = f"{request.method}:{request.url.path}"

    record, created = idempotency_service.get_or_create(
        company_id=company_id, endpoint=endpoint_identifier, key=idempotency_key
    )

    if not created:
        return idempotency_service.resolve_existing(record)

    try:
        service = QBOAccountsImportService(company_id, db)
        result = service.import_accounts()
        idempotency_service.mark_completed(record, result)
        return result
    except ValueError as e:
        idempotency_service.mark_failed(record, {"error": str(e)})
        raise AequitasError(
            code="AEQ_QBO_UNAUTHORIZED",
            message=str(e),
            http_status=status.HTTP_401_UNAUTHORIZED,
        )
    except Exception as e:
        idempotency_service.mark_failed(record, {"error": str(e)})
        raise AequitasError(
            code="AEQ_QBO_IMPORT_FAILED",
            message="Failed to import accounts from QuickBooks Online.",
            details={"error": str(e)},
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@router.post("/{company_id}/export", summary="Export Master Chart to QBO")
def export_master_chart_to_qbo(company_id: UUID, db: Session = Depends(get_db)):
    try:
        service = QBOAccountsExportService(company_id, db)
        return service.publish_masterchart_to_qbo()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# --- RECONCILIATION & MAPPING ---

@router.get("/{company_id}/reconcile", summary="Reconcile QBO Chart of Accounts")
def reconcile_with_master_chart(company_id: UUID, db: Session = Depends(get_db)):
    """
    Performs a full reconciliation between the company's imported QBO accounts
    and the Master Chart, returning a detailed report of differences and suggestions.
    """
    try:
        service = QBOReconciliationService(company_id, db)
        return service.reconcile_qbo()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{company_id}/mapping", summary="Get Mapping Suggestions Preview")
def get_mapping_suggestions(company_id: UUID, db: Session = Depends(get_db)):
    """
    A convenience endpoint that returns just the 'suggested_mappings' portion
    of the main reconciliation report.
    """
    try:
        service = QBOReconciliationService(company_id, db)
        report = service.reconcile_qbo()
        return report.get("suggested_mappings", [])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
