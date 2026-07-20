import stripe
from core.config.settings import settings
from shared.logger import get_logger
from shared.exceptions import FitCheckException

logger = get_logger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeClient:
    """
    Thin wrapper around the Stripe SDK. No business logic here —
    that lives in the subscription pipeline/API layer. This class
    only knows how to talk to Stripe.
    """

    def create_customer(self, email: str, user_id: str) -> str:
        """Creates a Stripe customer, tagged with our internal user_id."""
        try:
            customer = stripe.Customer.create(
                email=email,
                metadata={"user_id": user_id}
            )
            logger.info(f"Stripe customer created — user={user_id} customer={customer.id}")
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer creation failed: {e}")
            raise FitCheckException(
                "Failed to set up payment account. Please try again.",
                code="STRIPE_ERROR", status_code=500
            )

def create_checkout_session(self, customer_id: str, user_id: str) -> str:
    """Creates a Stripe Checkout session, returns the hosted checkout URL."""
    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": settings.STRIPE_PRICE_ID, "quantity": 1}],
            success_url=f"{settings.APP_BASE_URL}/subscription/success",
            cancel_url=f"{settings.APP_BASE_URL}/subscription/cancelled",
            metadata={"user_id": user_id},
            client_reference_id=user_id,
            subscription_data={
                "metadata": {"user_id": user_id}
            }
        )

        if not session.url:
            raise FitCheckException(
                "Checkout session could not be created.",
                code="STRIPE_ERROR", status_code=500
            )

        logger.info(f"Checkout session created — user={user_id} session={session.id}")
        return session.url
    except stripe.error.StripeError as e:
        logger.error(f"Checkout session creation failed: {e}")
        raise FitCheckException(
            "Failed to start checkout. Please try again.",
            code="STRIPE_ERROR", status_code=500
        )
    def cancel_subscription(self, subscription_id: str) -> None:
        """Cancels a subscription at the end of the current billing period."""
        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            logger.info(f"Subscription cancellation scheduled — subscription={subscription_id}")
        except stripe.error.StripeError as e:
            logger.error(f"Subscription cancellation failed: {e}")
            raise FitCheckException(
                "Failed to cancel subscription. Please try again.",
                code="STRIPE_ERROR", status_code=500
            )

    def verify_webhook(self, payload: bytes, signature: str) -> dict:
        """Verifies a webhook came from Stripe, returns the parsed event."""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            logger.warning(f"Webhook verification failed: {e}")
            raise FitCheckException(
                "Invalid webhook signature.", code="INVALID_WEBHOOK", status_code=400
            )


stripe_client = StripeClient()