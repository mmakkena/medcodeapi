"""Stripe billing endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.user import User
from app.models.subscription import StripeSubscription
from app.models.plan import Plan
from app.middleware.auth import get_current_user
from app.services.stripe_service import (
    create_billing_portal_session,
    create_checkout_session,
    verify_webhook_signature
)
from app.config import settings

router = APIRouter()


@router.post("/checkout")
async def create_checkout(
    plan_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe Checkout session for subscribing to a plan.
    """
    # Find the plan
    plan = db.query(Plan).filter(Plan.name == plan_name).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{plan_name}' not found"
        )

    if not plan.stripe_price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan '{plan_name}' does not have a Stripe price configured"
        )

    # Check if user already has a subscription
    existing_subscription = db.query(StripeSubscription).filter(
        StripeSubscription.user_id == current_user.id
    ).first()

    # Configure URLs
    frontend_url = settings.CORS_ORIGINS.split(',')[0]
    success_url = f"{frontend_url}/dashboard/billing?success=true"
    cancel_url = f"{frontend_url}/dashboard/billing?canceled=true"

    # Create checkout session
    checkout_session = await create_checkout_session(
        customer_email=current_user.email,
        price_id=plan.stripe_price_id,
        success_url=success_url,
        cancel_url=cancel_url,
        customer_id=existing_subscription.stripe_customer_id if existing_subscription else None
    )

    return {"url": checkout_session.url}


@router.get("/portal")
async def get_billing_portal(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Stripe billing portal URL for the current user.
    Allows users to manage their subscription, payment methods, and billing history.
    """
    # Find user's subscription
    subscription = db.query(StripeSubscription).filter(
        StripeSubscription.user_id == current_user.id
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found. Please subscribe to a plan first."
        )

    # Create billing portal session
    return_url = f"{settings.CORS_ORIGINS.split(',')[0]}/dashboard/billing"

    portal_session = await create_billing_portal_session(
        customer_id=subscription.stripe_customer_id,
        return_url=return_url
    )

    return {"url": portal_session.url}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    Updates subscription status based on Stripe events.
    """
    # Get raw body
    payload = await request.body()

    # Verify webhook signature
    try:
        event = await verify_webhook_signature(payload, stripe_signature)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Handle different event types
    event_type = event["type"]

    if event_type == "customer.subscription.created":
        await handle_subscription_created(event, db)
    elif event_type == "customer.subscription.updated":
        await handle_subscription_updated(event, db)
    elif event_type == "customer.subscription.deleted":
        await handle_subscription_deleted(event, db)
    elif event_type == "invoice.payment_failed":
        await handle_payment_failed(event, db)

    return {"status": "success"}


async def handle_subscription_created(event: dict, db: Session):
    """Handle subscription creation"""
    subscription_data = event["data"]["object"]

    # Find user by Stripe customer ID
    existing_sub = db.query(StripeSubscription).filter(
        StripeSubscription.stripe_customer_id == subscription_data["customer"]
    ).first()

    if existing_sub:
        # Update existing subscription
        existing_sub.stripe_subscription_id = subscription_data["id"]
        existing_sub.status = subscription_data["status"]
        existing_sub.current_period_start = datetime.fromtimestamp(subscription_data["current_period_start"])
        existing_sub.current_period_end = datetime.fromtimestamp(subscription_data["current_period_end"])
    else:
        # Create new subscription (if user exists)
        # TODO: Link to user account
        pass

    db.commit()


async def handle_subscription_updated(event: dict, db: Session):
    """Handle subscription update"""
    subscription_data = event["data"]["object"]

    subscription = db.query(StripeSubscription).filter(
        StripeSubscription.stripe_subscription_id == subscription_data["id"]
    ).first()

    if subscription:
        subscription.status = subscription_data["status"]
        subscription.current_period_start = datetime.fromtimestamp(subscription_data["current_period_start"])
        subscription.current_period_end = datetime.fromtimestamp(subscription_data["current_period_end"])
        db.commit()


async def handle_subscription_deleted(event: dict, db: Session):
    """Handle subscription cancellation"""
    subscription_data = event["data"]["object"]

    subscription = db.query(StripeSubscription).filter(
        StripeSubscription.stripe_subscription_id == subscription_data["id"]
    ).first()

    if subscription:
        subscription.status = "canceled"
        db.commit()


async def handle_payment_failed(event: dict, db: Session):
    """Handle failed payment"""
    invoice_data = event["data"]["object"]
    customer_id = invoice_data["customer"]

    subscription = db.query(StripeSubscription).filter(
        StripeSubscription.stripe_customer_id == customer_id
    ).first()

    if subscription:
        subscription.status = "past_due"
        db.commit()
