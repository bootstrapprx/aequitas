"""
Payment webhook handlers for Stripe integration.
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import logging

from app.db.session import get_db
from app.db.models.pending_registration import PendingRegistration
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    
    This endpoint receives webhook events from Stripe and processes them.
    Currently handles:
    - checkout.session.completed: Finalizes pending registrations
    """
    if not settings.STRIPE_ENABLED:
        logger.warning("Received Stripe webhook but Stripe is not configured")
        return {"status": "ignored", "reason": "Stripe not configured"}
    
    try:
        import stripe
        stripe.api_key = settings.STRIPE_API_KEY
        
        # Get the raw body and signature
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Stripe webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Handle the event
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            await _handle_checkout_completed(db, session)
        else:
            logger.info(f"Unhandled Stripe event type: {event['type']}")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


async def _handle_checkout_completed(db: Session, session: dict):
    """
    Handle successful checkout session completion.
    
    Finds the pending registration and confirms it.
    """
    session_id = session.get("id")
    metadata = session.get("metadata", {})
    pending_token = metadata.get("pending_token")
    
    if not pending_token:
        logger.warning(f"Checkout completed without pending_token in metadata: {session_id}")
        return
    
    # Find pending registration
    pending = db.query(PendingRegistration).filter(
        PendingRegistration.token == pending_token
    ).first()
    
    if not pending:
        logger.warning(f"No pending registration found for token: {pending_token}")
        return
    
    # Import here to avoid circular import
    from app.api.v1.auth import _finalize_registration
    
    # Finalize the registration
    try:
        _finalize_registration(db, pending)
        
        # Clean up pending registration
        db.delete(pending)
        db.commit()
        
        logger.info(f"✓ Payment confirmed and registration finalized for: {pending.email}")
    except Exception as e:
        logger.error(f"Failed to finalize registration after payment: {e}")
        # Don't raise - we've received payment, we should try to recover
