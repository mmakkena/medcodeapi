"""Stripe integration service"""

import stripe
from app.config import settings

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


async def create_customer(email: str, user_id: str) -> stripe.Customer:
    """Create a Stripe customer"""
    customer = stripe.Customer.create(
        email=email,
        metadata={"user_id": user_id}
    )
    return customer


async def create_subscription(customer_id: str, price_id: str) -> stripe.Subscription:
    """Create a Stripe subscription"""
    subscription = stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": price_id}],
        payment_behavior="default_incomplete",
        expand=["latest_invoice.payment_intent"],
    )
    return subscription


async def cancel_subscription(subscription_id: str) -> stripe.Subscription:
    """Cancel a Stripe subscription"""
    subscription = stripe.Subscription.delete(subscription_id)
    return subscription


async def create_checkout_session(
    customer_email: str,
    price_id: str,
    success_url: str,
    cancel_url: str,
    customer_id: str | None = None
) -> stripe.checkout.Session:
    """Create a Stripe Checkout session for subscription"""
    session_params = {
        "mode": "subscription",
        "line_items": [{
            "price": price_id,
            "quantity": 1,
        }],
        "success_url": success_url,
        "cancel_url": cancel_url,
    }

    if customer_id:
        session_params["customer"] = customer_id
    else:
        session_params["customer_email"] = customer_email

    session = stripe.checkout.Session.create(**session_params)
    return session


async def create_billing_portal_session(customer_id: str, return_url: str) -> stripe.billing_portal.Session:
    """Create a Stripe billing portal session"""
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
    return session


async def verify_webhook_signature(payload: bytes, sig_header: str) -> dict:
    """Verify Stripe webhook signature and return event"""
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        return event
    except ValueError:
        raise ValueError("Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise ValueError("Invalid signature")
