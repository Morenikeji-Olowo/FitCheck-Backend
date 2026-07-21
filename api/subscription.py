from fastapi import APIRouter, Query, Request,Depends
from shared.dependencies import get_current_user_id
from uuid import UUID
from shared.logger import get_logger
from shared.models.responses import SuccessResponse
from shared.exceptions import FitCheckException
from core.storage.supabase_client import supabase
from core.payments.stripe_client import stripe_client
from pipelines.subscription_pipeline import (
    start_checkout,
    get_subscription_status,
    cancel_user_subscription
)

logger = get_logger(__name__)

router = APIRouter(prefix="/subscription", tags=["Subscription"])


@router.get("/health")
async def health():
    return { "service": "subscription", "version": "1.0.0", "status": "healthy" }


@router.post("/checkout", response_model=SuccessResponse)
async def create_checkout(user_id: UUID = Depends(get_current_user_id)):
    """Start a Stripe Checkout session for premium subscription."""
    checkout_url = await start_checkout(str(user_id))
    return SuccessResponse(data={"checkout_url": checkout_url})


@router.get("/me", response_model=SuccessResponse)
async def get_my_subscription(user_id: UUID = Depends(get_current_user_id)):
    """Get current subscription status."""
    status = await get_subscription_status(str(user_id))
    return SuccessResponse(data=status)


@router.post("/cancel", response_model=SuccessResponse)
async def cancel_subscription(user_id: UUID = Depends(get_current_user_id)):
    """Cancel subscription — takes effect at end of billing period."""
    result = await cancel_user_subscription(str(user_id))
    return SuccessResponse(data=result)


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    event = stripe_client.verify_webhook(payload, signature)

    event_type = event["type"]
    data = event["data"]["object"].to_dict() 

    logger.info(f"Stripe webhook received — type={event_type}")

    if event_type == "checkout.session.completed":
        _handle_checkout_completed(data)

    elif event_type == "customer.subscription.updated":
        _handle_subscription_updated(data)

    elif event_type == "customer.subscription.deleted":
        _handle_subscription_deleted(data)

    elif event_type == "invoice.payment_failed":
        _handle_payment_failed(data)

    else:
        logger.info(f"Unhandled webhook event type: {event_type}")

    return {"received": True}

def _handle_checkout_completed(session: dict) -> None:
    """First successful payment — unlock premium."""
    user_id = session.get("client_reference_id") or session.get("metadata", {}).get("user_id")
    subscription_id = session.get("subscription")

    if not user_id:
        logger.error("Checkout completed but no user_id found in session")
        return

    result = supabase.table("profiles").update({
        "tier": "premium",
        "subscription_id": subscription_id,
        "stripe_subscription_status": "active"
    }).eq("id", user_id).execute()

    if not result.data:
        logger.error(f"Failed to update profile after checkout — user={user_id}")
        return

    logger.info(f"Premium unlocked — user={user_id} subscription={subscription_id}")


def _handle_subscription_updated(subscription: dict) -> None:
    """Subscription renewed, changed, or entered a new billing period."""
    user_id = subscription.get("metadata", {}).get("user_id")
    status = subscription.get("status")
    period_end = subscription.get("current_period_end")

    if not user_id:
        logger.warning("Subscription updated but no user_id in metadata — skipping")
        return

    updates = {"stripe_subscription_status": status}

    if period_end:
        from datetime import datetime, UTC
        updates["subscription_current_period_end"] = datetime.fromtimestamp(period_end, UTC).isoformat()

    if status in ("active", "trialing"):
        updates["tier"] = "premium"
    else:
        updates["tier"] = "free"

    result = supabase.table("profiles").update(updates).eq("id", user_id).execute()

    if not result.data:
        logger.error(f"Failed to update profile on subscription change — user={user_id}")
        return

    logger.info(f"Subscription updated — user={user_id} status={status}")

def _handle_subscription_deleted(subscription: dict) -> None:
    """Subscription fully ended — downgrade to free."""
    user_id = subscription.get("metadata", {}).get("user_id")

    if not user_id:
        logger.warning("Subscription deleted but no user_id in metadata — skipping")
        return

    supabase.table("profiles").update({
        "tier": "free",
        "stripe_subscription_status": "cancelled"
    }).eq("id", user_id).execute()

    logger.info(f"Subscription ended, downgraded to free — user={user_id}")


def _handle_payment_failed(invoice: dict) -> None:
    """Payment failed — mark status, don't immediately downgrade (grace period)."""
    customer_id = invoice.get("customer")

    if not customer_id:
        return

    result = supabase.table("profiles")\
        .select("id")\
        .eq("stripe_customer_id", customer_id)\
        .single()\
        .execute()

    if not result.data:
        logger.warning(f"Payment failed for unknown customer={customer_id}")
        return

    user_id = result.data["id"]
    supabase.table("profiles").update({
        "stripe_subscription_status": "past_due"
    }).eq("id", user_id).execute()

    logger.warning(f"Payment failed — user={user_id} marked past_due")