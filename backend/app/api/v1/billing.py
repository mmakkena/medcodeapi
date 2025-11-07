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


@router.get("/subscription")
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's subscription information
    """
    import logging
    logger = logging.getLogger(__name__)

    # Find user's subscription
    subscription = db.query(StripeSubscription).filter(
        StripeSubscription.user_id == current_user.id
    ).first()

    if not subscription:
        # Return free plan if no subscription
        free_plan = db.query(Plan).filter(Plan.name == "Free").first()
        logger.info(f"No subscription found for user {current_user.id}")
        return {
            "plan_name": "Free",
            "monthly_requests": free_plan.monthly_requests if free_plan else 100,
            "price_cents": 0,
            "status": "active",
            "features": free_plan.features if free_plan else {}
        }

    # Get plan details using plan_id from subscription
    plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()

    if not plan:
        # Fallback: try to get plan from subscription metadata or default to Developer
        plan = db.query(Plan).filter(Plan.name == "Developer").first()

    logger.info(f"User {current_user.id} has subscription {subscription.stripe_subscription_id} with status {subscription.status}")

    # Only return subscription if status is active, trialing, past_due, or incomplete
    # Filter out incomplete_expired, canceled, and unpaid subscriptions
    if subscription.status in ["incomplete_expired", "canceled", "unpaid"]:
        # Return free plan if subscription is incomplete/canceled
        free_plan = db.query(Plan).filter(Plan.name == "Free").first()
        logger.info(f"Subscription {subscription.stripe_subscription_id} has invalid status: {subscription.status}")
        return {
            "plan_name": "Free",
            "monthly_requests": free_plan.monthly_requests if free_plan else 100,
            "price_cents": 0,
            "status": "active",
            "features": free_plan.features if free_plan else {}
        }

    return {
        "plan_name": plan.name if plan else "Unknown",
        "monthly_requests": plan.monthly_requests if plan else 10000,
        "price_cents": plan.price_cents if plan else 4900,
        "status": subscription.status,
        "current_period_end": subscription.current_period_end,
        "features": plan.features if plan else {}
    }


@router.get("/subscription/debug")
async def debug_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Debug endpoint to see raw subscription data
    """
    import logging
    logger = logging.getLogger(__name__)

    # Find user's subscription
    subscription = db.query(StripeSubscription).filter(
        StripeSubscription.user_id == current_user.id
    ).first()

    if not subscription:
        return {
            "found": False,
            "user_id": str(current_user.id),
            "message": "No subscription found in database"
        }

    # Get plan details
    plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()

    logger.info(f"Debug: User {current_user.id} has subscription {subscription.stripe_subscription_id} with status {subscription.status}")

    return {
        "found": True,
        "user_id": str(current_user.id),
        "stripe_subscription_id": subscription.stripe_subscription_id,
        "stripe_customer_id": subscription.stripe_customer_id,
        "status": subscription.status,
        "plan_id": subscription.plan_id,
        "plan_name": plan.name if plan else None,
        "current_period_start": subscription.current_period_start,
        "current_period_end": subscription.current_period_end,
        "created_at": subscription.created_at,
        "updated_at": subscription.updated_at
    }


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
        customer_id=existing_subscription.stripe_customer_id if existing_subscription else None,
        user_id=str(current_user.id)
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

    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Received Stripe webhook: {event_type}, event_id: {event.get('id', 'unknown')}")

    if event_type == "checkout.session.completed":
        await handle_checkout_completed(event, db)
    elif event_type == "customer.subscription.created":
        await handle_subscription_created(event, db)
    elif event_type == "customer.subscription.updated":
        await handle_subscription_updated(event, db)
    elif event_type == "customer.subscription.deleted":
        await handle_subscription_deleted(event, db)
    elif event_type == "invoice.payment_succeeded":
        await handle_payment_succeeded(event, db)
    elif event_type == "invoice.payment_failed":
        await handle_payment_failed(event, db)
    else:
        logger.info(f"Unhandled webhook event type: {event_type}")

    return {"status": "success"}


async def handle_checkout_completed(event: dict, db: Session):
    """Handle checkout session completion"""
    import logging
    logger = logging.getLogger(__name__)

    session_data = event["data"]["object"]
    logger.info(f"Processing checkout.session.completed: {session_data.get('id')}")

    # Get subscription ID from checkout session
    subscription_id = session_data.get("subscription")
    customer_id = session_data.get("customer")

    if not subscription_id:
        logger.warning("No subscription ID in checkout session")
        return

    # Get user_id from session metadata
    user_id = session_data.get("metadata", {}).get("user_id")

    if not user_id:
        logger.error("No user_id in checkout session metadata")
        return

    # Check if subscription already exists
    existing_sub = db.query(StripeSubscription).filter(
        StripeSubscription.stripe_subscription_id == subscription_id
    ).first()

    if existing_sub:
        logger.info(f"Subscription {subscription_id} already exists, skipping")
        return

    # Get the subscription details from Stripe to find the price_id
    import stripe
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        logger.info(f"Retrieved subscription {subscription_id} from Stripe")

        # Get price_id from subscription items
        items_data = list(subscription["items"]["data"]) if "items" in subscription and "data" in subscription["items"] else []

        if items_data:
            price_id = items_data[0]["price"]["id"]
            logger.info(f"Found price_id: {price_id}")

            # Find plan by stripe_price_id
            plan = db.query(Plan).filter(Plan.stripe_price_id == price_id).first()

            if plan:
                # Create subscription record
                new_subscription = StripeSubscription(
                    user_id=user_id,
                    plan_id=plan.id,
                    stripe_subscription_id=subscription_id,
                    stripe_customer_id=customer_id,
                    status=subscription["status"],
                    current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
                    current_period_end=datetime.fromtimestamp(subscription["current_period_end"])
                )
                db.add(new_subscription)
                db.commit()
                logger.info(f"Created subscription for user {user_id}, plan {plan.name}")
            else:
                logger.error(f"Plan not found for price_id: {price_id}")
        else:
            logger.error("No items in subscription")
    except Exception as e:
        logger.error(f"Failed to retrieve subscription from Stripe: {e}")
        import traceback
        logger.error(traceback.format_exc())


async def handle_subscription_created(event: dict, db: Session):
    """Handle subscription creation"""
    import logging
    logger = logging.getLogger(__name__)

    subscription_data = event["data"]["object"]
    subscription_id = subscription_data["id"]

    # Log the event for debugging
    logger.info(f"Processing subscription.created event: {subscription_id}")

    # First, check if subscription already exists by stripe_subscription_id
    # (it may have been created by checkout.session.completed)
    existing_sub_by_id = db.query(StripeSubscription).filter(
        StripeSubscription.stripe_subscription_id == subscription_id
    ).first()

    if existing_sub_by_id:
        # Subscription already exists (created by checkout.session.completed)
        # Update the status, period fields, AND check if plan changed
        logger.info(f"Subscription {subscription_id} already exists, updating status and checking plan")
        old_plan_id = existing_sub_by_id.plan_id
        existing_sub_by_id.status = subscription_data.get("status", existing_sub_by_id.status)
        if "current_period_start" in subscription_data:
            existing_sub_by_id.current_period_start = datetime.fromtimestamp(subscription_data["current_period_start"])
        if "current_period_end" in subscription_data:
            existing_sub_by_id.current_period_end = datetime.fromtimestamp(subscription_data["current_period_end"])

        # Check if the plan (price) has changed
        items = subscription_data.get("items", {}).get("data", [])
        if items:
            new_price_id = items[0]["price"]["id"]
            logger.info(f"Subscription {subscription_id} has price_id: {new_price_id}")

            # Find the plan by Stripe price ID
            new_plan = db.query(Plan).filter(Plan.stripe_price_id == new_price_id).first()
            if new_plan and new_plan.id != old_plan_id:
                existing_sub_by_id.plan_id = new_plan.id
                logger.info(f"Updated subscription {subscription_id}: plan changed to '{new_plan.name}'")

        db.commit()
        return

    # If not found by ID, check by customer_id
    existing_sub = db.query(StripeSubscription).filter(
        StripeSubscription.stripe_customer_id == subscription_data.get("customer")
    ).first()

    if existing_sub:
        # Update existing subscription with the new subscription_id
        logger.info(f"Updating existing customer subscription with new subscription_id: {subscription_id}")
        old_plan_id = existing_sub.plan_id
        existing_sub.stripe_subscription_id = subscription_id
        existing_sub.status = subscription_data.get("status", "active")
        if "current_period_start" in subscription_data:
            existing_sub.current_period_start = datetime.fromtimestamp(subscription_data["current_period_start"])
        if "current_period_end" in subscription_data:
            existing_sub.current_period_end = datetime.fromtimestamp(subscription_data["current_period_end"])

        # Check if the plan (price) has changed
        items = subscription_data.get("items", {}).get("data", [])
        if items:
            new_price_id = items[0]["price"]["id"]
            logger.info(f"Subscription {subscription_id} has price_id: {new_price_id}")

            # Find the plan by Stripe price ID
            new_plan = db.query(Plan).filter(Plan.stripe_price_id == new_price_id).first()
            if new_plan and new_plan.id != old_plan_id:
                existing_sub.plan_id = new_plan.id
                logger.info(f"Updated subscription {subscription_id}: plan changed to '{new_plan.name}'")
    else:
        # Create new subscription
        # Get user_id from subscription metadata
        user_id = subscription_data.get("metadata", {}).get("user_id")

        if not user_id:
            # Try to find user by customer email (fallback)
            from app.models.user import User
            import stripe
            try:
                customer = stripe.Customer.retrieve(subscription_data.get("customer"))
                user = db.query(User).filter(User.email == customer.email).first()
                if user:
                    user_id = str(user.id)
            except Exception as e:
                logger.error(f"Failed to retrieve customer: {e}")

        if user_id:
            # Get price_id from subscription items
            items = subscription_data.get("items", {}).get("data", [])
            if not items:
                logger.error("No items in subscription data")
                return

            price_id = items[0]["price"]["id"]

            # Find plan by stripe_price_id
            plan = db.query(Plan).filter(Plan.stripe_price_id == price_id).first()

            if plan:
                # Create new subscription record
                new_subscription = StripeSubscription(
                    user_id=user_id,
                    plan_id=plan.id,
                    stripe_subscription_id=subscription_data["id"],
                    stripe_customer_id=subscription_data.get("customer"),
                    status=subscription_data.get("status", "active"),
                    current_period_start=datetime.fromtimestamp(
                        subscription_data.get("current_period_start", int(datetime.utcnow().timestamp()))
                    ),
                    current_period_end=datetime.fromtimestamp(
                        subscription_data.get("current_period_end", int(datetime.utcnow().timestamp()) + 2592000)  # +30 days
                    )
                )
                db.add(new_subscription)
                logger.info(f"Created subscription for user {user_id}, plan {plan.name}")
            else:
                logger.error(f"Plan not found for price_id: {price_id}")
        else:
            logger.error("Could not determine user_id for subscription")

    db.commit()


async def handle_subscription_updated(event: dict, db: Session):
    """Handle subscription update"""
    import logging
    logger = logging.getLogger(__name__)

    subscription_data = event["data"]["object"]
    subscription_id = subscription_data["id"]
    new_status = subscription_data.get("status")

    logger.info(f"Processing subscription.updated for {subscription_id}, new status: {new_status}")

    subscription = db.query(StripeSubscription).filter(
        StripeSubscription.stripe_subscription_id == subscription_id
    ).first()

    if subscription:
        old_status = subscription.status
        old_plan_id = subscription.plan_id

        # Update status
        subscription.status = new_status

        # Update periods
        if "current_period_start" in subscription_data:
            subscription.current_period_start = datetime.fromtimestamp(subscription_data["current_period_start"])
        if "current_period_end" in subscription_data:
            subscription.current_period_end = datetime.fromtimestamp(subscription_data["current_period_end"])

        # IMPORTANT: Check if the plan (price) has changed (plan upgrade/downgrade)
        items = subscription_data.get("items", {}).get("data", [])
        if items:
            new_price_id = items[0]["price"]["id"]
            logger.info(f"Subscription {subscription_id} has price_id: {new_price_id}")

            # Find the plan by Stripe price ID
            new_plan = db.query(Plan).filter(Plan.stripe_price_id == new_price_id).first()
            if new_plan and new_plan.id != old_plan_id:
                subscription.plan_id = new_plan.id
                logger.info(f"Updated subscription {subscription_id}: plan changed to '{new_plan.name}'")

        db.commit()
        logger.info(f"Updated subscription {subscription_id}: status '{old_status}' → '{subscription.status}'")
    else:
        logger.warning(f"Subscription not found for update: {subscription_id}")


async def handle_subscription_deleted(event: dict, db: Session):
    """Handle subscription cancellation"""
    subscription_data = event["data"]["object"]

    subscription = db.query(StripeSubscription).filter(
        StripeSubscription.stripe_subscription_id == subscription_data["id"]
    ).first()

    if subscription:
        subscription.status = "canceled"
        db.commit()


async def handle_payment_succeeded(event: dict, db: Session):
    """Handle successful payment - activate subscription"""
    import logging
    logger = logging.getLogger(__name__)

    invoice_data = event["data"]["object"]

    # Extract subscription ID from nested structure
    # In invoice.payment_succeeded, the subscription ID is in parent.subscription_details.subscription
    subscription_id = None
    if "parent" in invoice_data and invoice_data["parent"]:
        parent = invoice_data["parent"]
        if "subscription_details" in parent and parent["subscription_details"]:
            subscription_id = parent["subscription_details"].get("subscription")

    # Fallback: try top-level subscription field (for older API versions)
    if not subscription_id:
        subscription_id = invoice_data.get("subscription")

    if not subscription_id:
        logger.warning("No subscription ID in invoice.payment_succeeded event")
        return

    logger.info(f"Processing payment success for subscription: {subscription_id}")

    # Find subscription by stripe_subscription_id
    subscription = db.query(StripeSubscription).filter(
        StripeSubscription.stripe_subscription_id == subscription_id
    ).first()

    if subscription:
        # Update status to active when payment succeeds
        old_status = subscription.status
        subscription.status = "active"
        db.commit()
        logger.info(f"Updated subscription {subscription_id} status from '{old_status}' to 'active'")
    else:
        logger.warning(f"Subscription not found for payment success: {subscription_id}")


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
