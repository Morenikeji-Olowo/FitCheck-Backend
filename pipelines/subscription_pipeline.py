from shared.logger import get_logger
from shared.exceptions import FitCheckException
from core.storage.supabase_client import supabase
from core.payments.stripe_client import stripe_client

logger = get_logger(__name__)


async def start_checkout(user_id: str) -> str:
    """
    Creates (or reuses) a Stripe customer for this user, then
    creates a Checkout session. Returns the hosted checkout URL.
    """
    logger.info(f"Starting checkout — user={user_id}")

    profile_result = supabase.table("profiles")\
        .select("email, stripe_customer_id, tier")\
        .eq("id", user_id)\
        .single()\
        .execute()

    if not profile_result.data:
        raise FitCheckException(
            "User not found.", code="USER_NOT_FOUND", status_code=404
        )

    profile = profile_result.data

    if profile.get("tier") == "premium":
        raise FitCheckException(
            "You already have an active Premium subscription.",
            code="ALREADY_PREMIUM", status_code=400
        )

    customer_id = profile.get("stripe_customer_id")

    if not customer_id:
        customer_id = stripe_client.create_customer(
            email=profile["email"], user_id=user_id
        )
        update_result = supabase.table("profiles")\
            .update({"stripe_customer_id": customer_id})\
            .eq("id", user_id)\
            .execute()

        if not update_result.data:
            raise FitCheckException(
                "Failed to save payment information.",
                code="DATABASE_ERROR", status_code=500
            )

        logger.info(f"Stripe customer saved to profile — user={user_id}")

    checkout_url = stripe_client.create_checkout_session(
        customer_id=customer_id, user_id=user_id
    )

    return checkout_url


async def get_subscription_status(user_id: str) -> dict:
    """Returns the current subscription state for a user."""
    result = supabase.table("profiles")\
        .select("tier, stripe_subscription_status, subscription_current_period_end")\
        .eq("id", user_id)\
        .single()\
        .execute()

    if not result.data:
        raise FitCheckException(
            "User not found.", code="USER_NOT_FOUND", status_code=404
        )

    data = result.data
    return {
        "tier": data.get("tier", "free"),
        "status": data.get("stripe_subscription_status", "inactive"),
        "renews_at": data.get("subscription_current_period_end")
    }


async def cancel_user_subscription(user_id: str) -> dict:
    """Cancels the user's subscription at the end of the current period."""
    logger.info(f"Cancel subscription requested — user={user_id}")

    result = supabase.table("profiles")\
        .select("subscription_id, tier")\
        .eq("id", user_id)\
        .single()\
        .execute()

    subscription_id = (result.data or {}).get("subscription_id")

    if not subscription_id:
        raise FitCheckException(
            "No active subscription found.",
            code="NO_ACTIVE_SUBSCRIPTION", status_code=400
        )

    stripe_client.cancel_subscription(subscription_id)

    logger.info(f"Subscription cancellation scheduled — user={user_id}")
    return {"message": "Your subscription will end at the current billing period."}